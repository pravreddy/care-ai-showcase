"""
AI Detector Services — Thin Orchestrator
==========================================
Entry point for AI detection. Just dispatches to the right provider.

All provider-specific code lives in ./providers/
Shared helpers (chunking, prompts) live in ./providers/base.py
Auto-fallback logic lives in ./fallback.py

To add a new provider:
  1. Create ./providers/YOUR_PROVIDER.py with a `call_YOUR_PROVIDER(text, chunk_index, total_chunks)` function
  2. Import it here and add a branch in detect_ai_content()
  3. Optionally add it to ./fallback.py for auto-cascade
"""
import logging
from django.conf import settings

from .providers import groq, gemini, cloudflare, siliconflow, mistral, grok, openai, huggingface
from .providers.base import (
    split_into_chunks, detect_chunked, detect_chunked_resumable,
    insufficient_text_result, MIN_CHARS,
)
from .fallback import detect_auto_fallback

logger = logging.getLogger(__name__)

DEFAULT_PROVIDER = getattr(settings, 'DEFAULT_AI_DETECTOR_PROVIDER', 'groq')


def detect_ai_content(text: str, provider: str = None) -> dict:
    """
    Main entry point: detect AI content in text.
    Routes to the right provider based on `provider` arg.
    """
    provider = provider or DEFAULT_PROVIDER
    text = text.strip()

    if len(text) < MIN_CHARS:
        return insufficient_text_result(provider)

    # Gemini has 1M context — single API call, no chunking
    if provider == 'gemini':
        logger.info(f'AI detector Gemini: {len(text)} chars in single call (no chunking)')
        return gemini.call_gemini(text)

    # Auto-fallback: try free providers in order until one succeeds
    if provider == 'auto':
        return detect_auto_fallback(text)

    # HuggingFace is legacy binary classifier — no chunking
    if provider == 'huggingface':
        return huggingface.detect_with_huggingface(text[:2000])

    # All other providers use chunked analysis
    chunks = split_into_chunks(text)
    logger.info(f'AI detector v2: {len(text)} chars -> {len(chunks)} chunks, provider={provider}')

    if provider == 'groq':
        return detect_chunked(chunks, text, groq.call_groq_quick, 'groq')
    elif provider == 'groq_deep':
        return detect_chunked(chunks, text, groq.call_groq_deep, 'groq_deep')
    elif provider == 'mistral':
        return detect_chunked(chunks, text, mistral.call_mistral, 'mistral')
    elif provider == 'siliconflow':
        return detect_chunked(chunks, text, siliconflow.call_siliconflow, 'siliconflow')
    elif provider == 'cloudflare':
        return detect_chunked(chunks, text, cloudflare.call_cloudflare, 'cloudflare')
    elif provider == 'grok':
        return detect_chunked(chunks, text, grok.call_grok, 'grok')
    elif provider == 'openai':
        return detect_chunked(chunks, text, openai.call_openai, 'openai')
    elif provider == 'binoculars':
        # Local statistical detector (perplexity ratio). Heavy ML deps are
        # imported lazily inside the provider, so importing it here is cheap.
        from .providers import binoculars
        return detect_chunked(chunks, text, binoculars.call_binoculars, 'binoculars')
    else:
        # Unknown provider — fallback to HuggingFace
        return huggingface.detect_with_huggingface(text[:2000])


def detect_ai_content_resumable(text: str, provider: str = None,
                                 skip_chunks: int = 0,
                                 existing_sentences: list = None,
                                 progress_callback=None) -> dict:
    """
    Same as detect_ai_content but supports resuming from a specific chunk.
    Used by Celery task — saves progress after each chunk.
    """
    provider = provider or DEFAULT_PROVIDER
    text = text.strip()

    if len(text) < MIN_CHARS:
        return insufficient_text_result(provider)

    # Pick the right API call function for the provider
    if provider == 'groq_deep':
        api_fn = groq.call_groq_deep
    elif provider == 'groq':
        api_fn = groq.call_groq_quick
    elif provider == 'mistral':
        api_fn = mistral.call_mistral
    elif provider == 'siliconflow':
        api_fn = siliconflow.call_siliconflow
    elif provider == 'cloudflare':
        api_fn = cloudflare.call_cloudflare
    elif provider == 'grok':
        api_fn = grok.call_grok
    elif provider == 'openai':
        api_fn = openai.call_openai
    elif provider == 'binoculars':
        from .providers import binoculars
        api_fn = binoculars.call_binoculars
    else:
        # Unsupported for resumable: use non-chunked fallback
        return huggingface.detect_with_huggingface(text[:2000])

    chunks = split_into_chunks(text)
    logger.info(f'AI detector resumable: {len(text)} chars -> {len(chunks)} chunks, skip={skip_chunks}')

    return detect_chunked_resumable(
        chunks, text, api_fn, provider,
        skip_chunks=skip_chunks,
        existing_sentences=existing_sentences or [],
        progress_callback=progress_callback,
    )
