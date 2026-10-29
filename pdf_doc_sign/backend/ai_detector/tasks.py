"""
AI Detector — Celery Tasks (with chunk resume)
================================================
Saves progress after each successful chunk.
On retry, skips already-completed chunks and resumes from where it stopped.
No more reprocessing the entire document on failure.
"""
import logging
from datetime import timedelta
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from django.utils import timezone
from .models import AIDetectionScan
from .services import detect_ai_content, detect_ai_content_resumable

logger = logging.getLogger(__name__)


@shared_task
def cleanup_old_scans_task():
    """
    Runs nightly at 3am UTC.
    Deletes AI detection scans older than 30 days.
    """
    cutoff = timezone.now() - timedelta(days=30)
    old_scans = AIDetectionScan.objects.filter(created_at__lt=cutoff)
    count = old_scans.count()
    if count == 0:
        logger.info('Cleanup: no scans older than 30 days')
        return
    deleted, _ = old_scans.delete()
    logger.info(f'Cleanup: deleted {deleted} scans older than 30 days')


@shared_task(
    bind=True,
    max_retries=5,
    # Local CPU inference runs ~2 min/chunk; a full doc (up to 15 chunks) can
    # take ~30 min — far longer than the cloud path it was originally sized for.
    # Raised so a local run completes in a single pass instead of hitting the
    # limit and restarting (the 'auto' path is not chunk-resumable).
    soft_time_limit=2700,   # 45 min
    time_limit=2760,
)
def run_ai_detection(self, scan_id: str, text: str, provider: str, user_id: int):
    """
    Run AI detection in background with chunk-level resume.
    After each chunk, saves progress to DB.
    On retry, loads saved progress and skips completed chunks.
    """
    try:
        scan = AIDetectionScan.objects.get(id=scan_id)
    except AIDetectionScan.DoesNotExist:
        logger.error(f'Scan {scan_id} not found')
        return

    # Load any existing progress from previous attempt
    existing_sentences = scan.sentence_analysis or []
    existing_chunks_done = scan.chunks_analysed if scan.chunks_analysed > 0 else 0

    scan.status = 'processing'
    if self.request.retries > 0:
        scan.error_message = f'Retry {self.request.retries}/{self.max_retries} — resuming from chunk {existing_chunks_done + 1}'
        logger.info(f'Resuming scan {scan_id} from chunk {existing_chunks_done + 1} (attempt {self.request.retries + 1})')
    scan.save(update_fields=['status', 'error_message'])

    logger.info(
        f'AI detection task: scan={scan_id}, chars={len(text)}, '
        f'provider={provider}, attempt={self.request.retries + 1}/{self.max_retries + 1}, '
        f'chunks_already_done={existing_chunks_done}'
    )

    try:
        # For 'auto' and 'gemini' providers, use single-call detect_ai_content (no chunk resume needed)
        # For chunked providers (groq_deep, groq, etc.), use resumable path
        if provider in ('auto', 'gemini'):
            result = detect_ai_content(text, provider=provider)
        else:
            result = detect_ai_content_resumable(
                text,
                provider=provider,
                skip_chunks=existing_chunks_done,
                existing_sentences=existing_sentences,
                progress_callback=lambda partial: _save_progress(scan, partial),
            )

        if result.get('error'):
            error_msg = result.get('error', '')
            # Transient errors — let Celery retry (progress is saved)
            if '429' in str(error_msg) or 'rate' in str(error_msg).lower() or 'timeout' in str(error_msg).lower():
                logger.warning(f'Transient error on scan {scan_id}: {error_msg} — will auto-retry from chunk {scan.chunks_analysed + 1}')
                raise Exception(f'Transient: {error_msg}')

            # Permanent error
            scan.status = 'failed'
            scan.error_message = error_msg
            scan.save(update_fields=['status', 'error_message'])
            return

        # Success — save final result
        scan.status = 'completed'
        scan.ai_probability = result.get('ai_probability')
        scan.human_probability = result.get('human_probability')
        scan.verdict = result.get('verdict', '')
        scan.explanation = result.get('explanation') or ''
        scan.sentence_analysis = result.get('sentences') or []
        scan.raw_response = result.get('raw')
        scan.error_message = ''
        scan.chunks_analysed = result.get('chunks_analysed', 1)
        scan.chunks_total = result.get('chunks_total', 1)
        scan.ai_sentence_count = result.get('ai_sentence_count', 0)
        scan.total_sentence_count = result.get('total_sentence_count', 0)
        scan.save()

        # Increment usage
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(id=user_id)
            user.increment_ai_scan_usage()
        except Exception as e:
            logger.error(f'Failed to increment scan usage for user {user_id}: {e}')

        logger.info(f'AI detection complete: scan={scan_id}, verdict={scan.verdict}, ai={scan.ai_probability}')

    except SoftTimeLimitExceeded:
        logger.warning(f'Scan {scan_id} hit time limit at chunk {scan.chunks_analysed} — progress saved, will resume')
        scan.error_message = f'Time limit reached at chunk {scan.chunks_analysed}/{scan.chunks_total}. Retrying...'
        scan.save(update_fields=['error_message'])
        # Explicit retry with backoff
        raise self.retry(countdown=120, max_retries=5)

    except Exception as e:
        if self.request.retries >= 5:
            logger.error(f'Scan {scan_id} failed after 6 attempts: {e}')
            scan.status = 'failed'
            scan.error_message = f'Failed after 6 attempts at chunk {scan.chunks_analysed}. Click reprocess to try again.'
            scan.save(update_fields=['status', 'error_message'])
            return

        # Calculate backoff: 2min, 4min, 8min, 10min (capped)
        countdown = min(120 * (2 ** self.request.retries), 600)
        logger.warning(f'Scan {scan_id} error at chunk {scan.chunks_analysed}: {e} — retrying in {countdown}s (attempt {self.request.retries + 2}/6)')
        raise self.retry(countdown=countdown, exc=e, max_retries=5)


def _save_progress(scan, partial_result):
    """
    Called after each successful chunk — saves progress to DB.
    If task dies, retry will resume from here.
    """
    scan.sentence_analysis = partial_result.get('sentences', [])
    scan.chunks_analysed = partial_result.get('chunks_analysed', 0)
    scan.chunks_total = partial_result.get('chunks_total', 1)
    scan.ai_sentence_count = partial_result.get('ai_sentence_count', 0)
    scan.total_sentence_count = partial_result.get('total_sentence_count', 0)
    # Save partial AI probability so user sees progress
    if partial_result.get('ai_probability') is not None:
        scan.ai_probability = partial_result['ai_probability']
        scan.human_probability = partial_result.get('human_probability')
    scan.save(update_fields=[
        'sentence_analysis', 'chunks_analysed', 'chunks_total',
        'ai_sentence_count', 'total_sentence_count',
        'ai_probability', 'human_probability',
    ])
    logger.info(f'  Progress saved: {scan.chunks_analysed}/{scan.chunks_total} chunks done')
