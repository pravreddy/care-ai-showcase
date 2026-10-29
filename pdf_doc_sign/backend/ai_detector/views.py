"""
AI Detector Views — v4 (Quick + Deep Scan)
=============================================
POST /api/ai-detector/scan/              — upload file → quick scan (8B, instant)
POST /api/ai-detector/scan-text/         — paste text → quick scan (8B, instant)
POST /api/ai-detector/scans/<id>/deep/   — trigger deep scan (70B, background)
POST /api/ai-detector/scans/<id>/        — reprocess a failed scan
GET  /api/ai-detector/scans/<id>/        — poll scan status
GET  /api/ai-detector/history/           — list user's past scans
DELETE /api/ai-detector/scans/<id>/      — delete a specific scan
GET  /api/ai-detector/providers/         — list available providers
GET  /api/ai-detector/usage/             — check remaining scans
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.conf import settings

from .models import AIDetectionScan
from .serializers import AIDetectionScanSerializer
from .utils import extract_text, get_extension, SUPPORTED_EXTENSIONS
from .services import detect_ai_content, DEFAULT_PROVIDER
from .tasks import run_ai_detection

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
VALID_PROVIDERS = ['auto', 'huggingface', 'groq', 'groq_deep', 'gemini', 'mistral', 'siliconflow', 'cloudflare', 'grok', 'openai', 'binoculars']


def _check_scan_limit(user):
    """Check if user has remaining AI scans. Returns (ok, error_response)."""
    if not user.can_scan_document:
        plan = user.subscription_plan
        limit = user.ai_scans_limit
        return False, Response({
            'error': 'AI scan limit reached for this month.',
            'plan': plan,
            'limit': limit,
            'used': user.ai_scans_used_this_month,
            'remaining': 0,
            'upgrade_hint': (
                'Upgrade your plan for more AI scans, '
                'or purchase extra scans (£2.50 for 100 scans).'
            ),
        }, status=status.HTTP_429_TOO_MANY_REQUESTS)
    return True, None


def _save_result(scan, result):
    """Save detection result onto a scan object."""
    scan.status = 'completed' if not result.get('error') else 'failed'
    scan.ai_probability = result.get('ai_probability')
    scan.human_probability = result.get('human_probability')
    scan.verdict = result.get('verdict', '')
    scan.explanation = result.get('explanation') or ''
    scan.sentence_analysis = result.get('sentences') or []
    scan.raw_response = result.get('raw')
    scan.error_message = result.get('error') or ''
    scan.chunks_analysed = result.get('chunks_analysed', 1)
    scan.chunks_total = result.get('chunks_total', 1)
    scan.ai_sentence_count = result.get('ai_sentence_count', 0)
    scan.total_sentence_count = result.get('total_sentence_count', 0)
    scan.save()
    return scan


class AIDetectView(APIView):
    """POST a file — queues async scan via auto-fallback (Gemini → Groq → Mistral → Cloudflare).

    Returns immediately with 'processing' status. Frontend polls /scans/<id>/ or refreshes history.
    No more HTTP timeouts waiting for long-running scans.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ok, err = _check_scan_limit(request.user)
        if not ok:
            return err

        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file uploaded.'}, status=status.HTTP_400_BAD_REQUEST)

        if file.size > MAX_FILE_SIZE:
            return Response({'error': 'File too large. Maximum size is 10MB.'}, status=status.HTTP_400_BAD_REQUEST)

        # Provider defaults to 'auto' — the smart fallback chain, which now tries
        # the local LLM first and only falls back to cloud providers. The frontend
        # sends 'auto'; a valid per-request override is still honoured.
        provider = request.data.get('provider', 'auto')
        if provider not in VALID_PROVIDERS:
            provider = 'auto'

        ext = get_extension(file.name)
        if ext not in SUPPORTED_EXTENSIONS:
            return Response(
                {'error': f'.{ext} is not supported.', 'supported': SUPPORTED_EXTENSIONS},
                status=status.HTTP_400_BAD_REQUEST,
            )

        organisation = getattr(request, 'organisation', None)

        scan = AIDetectionScan.objects.create(
            user=request.user, organisation=organisation,
            original_filename=file.name, file_type=ext,
            file_size_bytes=file.size, status='pending', provider=provider,
        )

        # Extract text (fast, keep synchronous)
        try:
            text, _ = extract_text(file, file.name)
        except ValueError as e:
            scan.status = 'failed'
            scan.error_message = str(e)
            scan.save(update_fields=['status', 'error_message'])
            return Response({'error': str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        except Exception as e:
            logger.error(f'Text extraction error for {file.name}: {e}')
            scan.status = 'failed'
            scan.error_message = 'Failed to read file content.'
            scan.save(update_fields=['status', 'error_message'])
            return Response({'error': 'Could not read file content.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        scan.text_length = len(text)
        scan.extracted_text = text

        if not text.strip():
            scan.status = 'failed'
            scan.error_message = 'No text could be extracted from this file.'
            scan.save(update_fields=['status', 'error_message', 'text_length', 'extracted_text'])
            return Response({'error': scan.error_message}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        # Queue background task — returns immediately, no HTTP timeout
        scan.status = 'processing'
        scan.save(update_fields=['status', 'text_length', 'extracted_text'])
        run_ai_detection.delay(str(scan.id), text, provider, request.user.id)

        data = AIDetectionScanSerializer(scan).data
        data['usage'] = {
            'used': request.user.ai_scans_used_this_month,
            'limit': request.user.ai_scans_limit,
            'remaining': request.user.ai_scans_remaining,
        }
        return Response(data, status=status.HTTP_202_ACCEPTED)


class AIDetectTextView(APIView):
    """POST plain text — queues async scan via auto-fallback.

    Returns immediately with 'processing' status. No HTTP timeout waiting for result.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ok, err = _check_scan_limit(request.user)
        if not ok:
            return err

        text = request.data.get('text', '').strip()
        if len(text) < 50:
            return Response(
                {'error': 'Text too short. Minimum 50 characters required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(text) > 50000:
            text = text[:50000]

        # Provider defaults to 'auto' — the smart fallback chain, which now tries
        # the local LLM first and only falls back to cloud providers. The frontend
        # sends 'auto'; a valid per-request override is still honoured.
        provider = request.data.get('provider', 'auto')
        if provider not in VALID_PROVIDERS:
            provider = 'auto'

        organisation = getattr(request, 'organisation', None)

        scan = AIDetectionScan.objects.create(
            user=request.user, organisation=organisation,
            original_filename='Pasted text',
            file_type='txt',
            file_size_bytes=len(text.encode('utf-8')),
            text_length=len(text),
            extracted_text=text,
            status='processing',
            provider=provider,
        )

        # Queue background task — returns immediately
        run_ai_detection.delay(str(scan.id), text, provider, request.user.id)

        data = AIDetectionScanSerializer(scan).data
        data['usage'] = {
            'used': request.user.ai_scans_used_this_month,
            'limit': request.user.ai_scans_limit,
            'remaining': request.user.ai_scans_remaining,
        }
        return Response(data, status=status.HTTP_202_ACCEPTED)


class AIDetectScanDetailView(APIView):
    """GET scan status / DELETE scan / POST reprocess."""
    permission_classes = [IsAuthenticated]

    def get(self, request, scan_id):
        try:
            scan = AIDetectionScan.objects.get(id=scan_id, user=request.user)
            return Response(AIDetectionScanSerializer(scan).data)
        except AIDetectionScan.DoesNotExist:
            return Response({'error': 'Scan not found.'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, scan_id):
        try:
            scan = AIDetectionScan.objects.get(id=scan_id, user=request.user)
            scan.delete()
            return Response({'deleted': str(scan_id)}, status=status.HTTP_200_OK)
        except AIDetectionScan.DoesNotExist:
            return Response({'error': 'Scan not found.'}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, scan_id):
        """POST = reprocess a failed scan."""
        try:
            scan = AIDetectionScan.objects.get(id=scan_id, user=request.user)
        except AIDetectionScan.DoesNotExist:
            return Response({'error': 'Scan not found.'}, status=status.HTTP_404_NOT_FOUND)

        if scan.status == 'processing':
            return Response({'error': 'Scan is already processing.'}, status=status.HTTP_400_BAD_REQUEST)

        if not scan.extracted_text:
            return Response({'error': 'No text to reprocess.'}, status=status.HTTP_400_BAD_REQUEST)

        scan.status = 'processing'
        scan.error_message = ''
        scan.verdict = ''
        scan.save(update_fields=['status', 'error_message', 'verdict'])

        run_ai_detection.delay(str(scan.id), scan.extracted_text, scan.provider, request.user.id)

        return Response(AIDetectionScanSerializer(scan).data, status=status.HTTP_202_ACCEPTED)


class AIDeepScanView(APIView):
    """POST — trigger deep scan from an existing quick scan.

    Deep scan uses Gemini 2.5 Flash (1M context, single API call).
    Falls back to Groq 70B if Gemini fails. Much faster than the old chunked 70B path.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, scan_id):
        try:
            original = AIDetectionScan.objects.get(id=scan_id, user=request.user)
        except AIDetectionScan.DoesNotExist:
            return Response({'error': 'Scan not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not original.extracted_text:
            return Response({'error': 'No text to analyse.'}, status=status.HTTP_400_BAD_REQUEST)

        organisation = getattr(request, 'organisation', None)

        # Create a new scan for the deep analysis
        deep_scan = AIDetectionScan.objects.create(
            user=request.user,
            organisation=organisation,
            original_filename=f'{original.original_filename} (Deep Scan)',
            file_type=original.file_type,
            file_size_bytes=original.file_size_bytes,
            text_length=original.text_length,
            extracted_text=original.extracted_text,
            status='processing',
            provider='auto',
        )

        # Queue background task with auto-fallback (Gemini first, then Mistral/Groq/Cloudflare)
        run_ai_detection.delay(str(deep_scan.id), original.extracted_text, 'auto', request.user.id)

        return Response(AIDetectionScanSerializer(deep_scan).data, status=status.HTTP_202_ACCEPTED)


class AIDetectHistoryView(APIView):
    """GET list of past scans for the current user."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        organisation = getattr(request, 'organisation', None)
        scans = AIDetectionScan.objects.filter(user=request.user)
        if organisation:
            scans = scans.filter(organisation=organisation)
        scans = scans.order_by('-created_at')[:50]
        return Response({'results': AIDetectionScanSerializer(scans, many=True).data})


class AIDetectorProvidersView(APIView):
    """GET — returns which providers are configured and available."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        hf_token = getattr(settings, 'HF_API_TOKEN', '')
        groq_key = getattr(settings, 'GROQ_API_KEY', '')
        grok_key = getattr(settings, 'GROK_API_KEY', '')
        openai_key = getattr(settings, 'OPENAI_API_KEY', '')
        gemini_key = getattr(settings, 'GEMINI_API_KEY', '')
        mistral_key = getattr(settings, 'MISTRAL_API_KEY', '')
        siliconflow_key = getattr(settings, 'SILICONFLOW_API_KEY', '')
        cloudflare_account = getattr(settings, 'CLOUDFLARE_ACCOUNT_ID', '')
        cloudflare_token = getattr(settings, 'CLOUDFLARE_API_TOKEN', '')

        # Binoculars runs locally — "configured" means the ML deps are present.
        import importlib.util
        binoculars_ready = bool(
            importlib.util.find_spec('torch') and importlib.util.find_spec('transformers')
        )

        return Response({
            'default': DEFAULT_PROVIDER,
            'providers': [
                {
                    'id': 'auto', 'name': 'Auto (smart fallback)',
                    'description': 'Fast cloud engines — tries Gemini first, then others automatically (recommended)',
                    'available': True, 'configured': True,
                    'has_explanation': True, 'has_sentences': True, 'cost': 'Free',
                },
                {
                    'id': 'huggingface', 'name': 'HuggingFace (Free)',
                    'description': 'Fast binary classifier — no sentence analysis',
                    'available': True, 'configured': bool(hf_token),
                    'has_explanation': False, 'has_sentences': False, 'cost': 'Free',
                },
                {
                    'id': 'groq', 'name': 'Quick Scan (FREE)',
                    'description': 'Llama 8B — instant full document scan with sentence highlighting',
                    'available': bool(groq_key), 'configured': bool(groq_key),
                    'has_explanation': True, 'has_sentences': True, 'cost': 'Free',
                },
                {
                    'id': 'gemini', 'name': 'Gemini Flash (FREE)',
                    'description': 'Google Gemini 2.5 Flash — 1M context, entire doc in one call, no rate limits',
                    'available': bool(gemini_key), 'configured': bool(gemini_key),
                    'has_explanation': True, 'has_sentences': True, 'cost': 'Free',
                },
                {
                    'id': 'mistral', 'name': 'Mistral AI (FREE)',
                    'description': 'European LLM — GDPR-friendly, dense logical models, ~1 req/sec',
                    'available': bool(mistral_key), 'configured': bool(mistral_key),
                    'has_explanation': True, 'has_sentences': True, 'cost': 'Free',
                },
                {
                    'id': 'siliconflow', 'name': 'SiliconFlow (FREE)',
                    'description': 'Llama 3.3 70B via SiliconFlow — OpenAI-compatible, free tier',
                    'available': bool(siliconflow_key), 'configured': bool(siliconflow_key),
                    'has_explanation': True, 'has_sentences': True, 'cost': 'Free',
                },
                {
                    'id': 'cloudflare', 'name': 'Cloudflare Workers AI (FREE)',
                    'description': 'Llama 3.1 8B — 10K neurons/day free, very reliable',
                    'available': bool(cloudflare_account and cloudflare_token),
                    'configured': bool(cloudflare_account and cloudflare_token),
                    'has_explanation': True, 'has_sentences': True, 'cost': 'Free',
                },
                {
                    'id': 'grok', 'name': 'Grok (xAI)',
                    'description': 'Deep analysis — sentence highlighting + explanation',
                    'available': bool(grok_key), 'configured': bool(grok_key),
                    'has_explanation': True, 'has_sentences': True, 'cost': 'Paid',
                },
                {
                    'id': 'openai', 'name': 'Local LLM (Ollama)',
                    'description': 'Runs on your own server — private, no API cost. '
                                   'Slower on CPU (several minutes per document).',
                    'available': bool(openai_key), 'configured': bool(openai_key),
                    'has_explanation': True, 'has_sentences': True, 'cost': 'Free (local)',
                },
                {
                    'id': 'binoculars', 'name': 'Binoculars (local, statistical)',
                    'description': 'Perplexity-ratio detector running on-server — a statistical '
                                   'cross-check to the LLM judges. No API cost. Needs calibration; '
                                   'best used alongside another provider.',
                    'available': binoculars_ready, 'configured': binoculars_ready,
                    'has_explanation': True, 'has_sentences': True, 'cost': 'Free (local)',
                },
            ],
        })


class AIDetectorUsageView(APIView):
    """GET — returns current user's AI scan usage and limits."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        plan_info = settings.SUBSCRIPTION_PLANS.get(user.subscription_plan, {})
        return Response({
            'plan': user.subscription_plan,
            'ai_scans': {
                'used': user.ai_scans_used_this_month,
                'limit': user.ai_scans_limit,
                'remaining': user.ai_scans_remaining,
                'extra_purchased': user.extra_ai_scans_purchased,
            },
            'documents': {
                'used': user.documents_used_this_month,
                'limit': user.documents_limit,
                'remaining': user.documents_remaining,
                'extra_purchased': user.extra_docs_purchased,
            },
            'plan_details': plan_info,
        })
