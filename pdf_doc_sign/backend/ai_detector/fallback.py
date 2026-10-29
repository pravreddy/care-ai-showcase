"""
Auto-Fallback Orchestrator
===========================
Tries free providers in order. First one that succeeds wins.
User sees only the result — backend silently cascades through providers.

Order: Gemini → Mistral → Groq → SiliconFlow → Cloudflare
Cloud-first for speed/reliability. The local LLM is NOT in this chain — it is an
opt-in choice (provider='openai'), because local CPU inference is slow and a
single slow chunk would otherwise discard the whole run and fall back anyway.

To change order or add providers: edit the PROVIDER_CHAIN list below.
"""
import logging

from .providers import gemini, groq, siliconflow, cloudflare, mistral
from .providers.base import split_into_chunks, detect_chunked, error_result

logger = logging.getLogger(__name__)


def detect_auto_fallback(text: str) -> dict:
    """Try cloud providers in order until one succeeds (Gemini first)."""
    errors = []

    # Attempt 1: Gemini (single call, 1M context, no chunking)
    if gemini.GEMINI_API_KEY:
        logger.info('Auto-fallback: trying Gemini')
        result = gemini.call_gemini(text)
        if not result.get('error'):
            result['provider_used'] = 'gemini'
            logger.info('Auto-fallback: Gemini succeeded')
            return result
        errors.append(f"gemini: {result.get('error', 'unknown')[:80]}")
        logger.warning(f'Auto-fallback: Gemini failed — {errors[-1]}')

    # Attempt 2: Mistral (European, 1 req/sec, dense logical models)
    if mistral.MISTRAL_API_KEY:
        logger.info('Auto-fallback: trying Mistral')
        chunks = split_into_chunks(text)
        result = detect_chunked(chunks, text, mistral.call_mistral, 'mistral')
        if not result.get('error'):
            result['provider_used'] = 'mistral'
            logger.info('Auto-fallback: Mistral succeeded')
            return result
        errors.append(f"mistral: {result.get('error', 'unknown')[:80]}")
        logger.warning(f'Auto-fallback: Mistral failed — {errors[-1]}')

    # Attempt 3: Groq 8B (chunked, fast)
    if groq.GROQ_API_KEY:
        logger.info('Auto-fallback: trying Groq 8B')
        chunks = split_into_chunks(text)
        result = detect_chunked(chunks, text, groq.call_groq_quick, 'groq')
        if not result.get('error'):
            result['provider_used'] = 'groq'
            logger.info('Auto-fallback: Groq 8B succeeded')
            return result
        errors.append(f"groq: {result.get('error', 'unknown')[:80]}")
        logger.warning(f'Auto-fallback: Groq 8B failed — {errors[-1]}')

    # Attempt 3: SiliconFlow (Llama 3.3 70B free tier) — skipped if no key
    if siliconflow.SILICONFLOW_API_KEY:
        logger.info('Auto-fallback: trying SiliconFlow')
        chunks = split_into_chunks(text)
        result = detect_chunked(chunks, text, siliconflow.call_siliconflow, 'siliconflow')
        if not result.get('error'):
            result['provider_used'] = 'siliconflow'
            logger.info('Auto-fallback: SiliconFlow succeeded')
            return result
        errors.append(f"siliconflow: {result.get('error', 'unknown')[:80]}")
        logger.warning(f'Auto-fallback: SiliconFlow failed — {errors[-1]}')

    # Attempt 4: Cloudflare Workers AI
    if cloudflare.CLOUDFLARE_ACCOUNT_ID and cloudflare.CLOUDFLARE_API_TOKEN:
        logger.info('Auto-fallback: trying Cloudflare Workers AI')
        chunks = split_into_chunks(text)
        result = detect_chunked(chunks, text, cloudflare.call_cloudflare, 'cloudflare')
        if not result.get('error'):
            result['provider_used'] = 'cloudflare'
            logger.info('Auto-fallback: Cloudflare succeeded')
            return result
        errors.append(f"cloudflare: {result.get('error', 'unknown')[:80]}")
        logger.warning(f'Auto-fallback: Cloudflare failed — {errors[-1]}')

    # All providers failed
    logger.error(f'Auto-fallback: ALL providers failed — {errors}')
    return error_result(
        f'All AI providers unavailable. Last errors: {"; ".join(errors[-3:])}',
        'auto',
    )
