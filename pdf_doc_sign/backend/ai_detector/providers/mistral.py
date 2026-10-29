"""
Mistral AI provider — FREE Experiment tier
https://console.mistral.ai

European/GDPR-friendly. ~1 req/sec rate limit (much better than Groq).
Uses OpenAI-compatible API.
"""
import logging
import requests
from django.conf import settings

from .base import (
    system_prompt, build_chunk_prompt,
    parse_openai_response, error_result,
)

logger = logging.getLogger(__name__)

MISTRAL_API_KEY = getattr(settings, 'MISTRAL_API_KEY', '')
MISTRAL_MODEL = getattr(settings, 'MISTRAL_MODEL', 'mistral-small-latest')
MISTRAL_API_URL = 'https://api.mistral.ai/v1/chat/completions'


def call_mistral(text: str, chunk_index: int = 1, total_chunks: int = 1) -> dict:
    """Mistral AI call (OpenAI-compatible API)."""
    if not MISTRAL_API_KEY:
        return error_result(
            'Mistral API key not configured. Get free key at console.mistral.ai',
            'mistral',
        )

    prompt = build_chunk_prompt(text, chunk_index, total_chunks)
    try:
        response = requests.post(
            MISTRAL_API_URL,
            headers={
                'Authorization': f'Bearer {MISTRAL_API_KEY}',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
            json={
                'model': MISTRAL_MODEL,
                'messages': [
                    {'role': 'system', 'content': system_prompt()},
                    {'role': 'user', 'content': prompt},
                ],
                'temperature': 0,
                'max_tokens': 3000,
                'response_format': {'type': 'json_object'},
            },
            timeout=60,
        )
        response.raise_for_status()
        return parse_openai_response(response.json(), 'mistral')
    except requests.exceptions.Timeout:
        return error_result('Mistral timed out', 'mistral')
    except requests.exceptions.RequestException as e:
        logger.error(f'Mistral API error: {e}')
        return error_result(f'Mistral unavailable: {str(e)}', 'mistral')
