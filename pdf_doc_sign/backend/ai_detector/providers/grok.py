"""
Grok provider (xAI) — PAID
https://x.ai/api
"""
import logging
import requests
from django.conf import settings

from .base import (
    system_prompt, build_chunk_prompt,
    parse_openai_response, error_result,
)

logger = logging.getLogger(__name__)

GROK_API_URL = getattr(settings, 'GROK_API_URL', 'https://api.x.ai/v1/chat/completions')
GROK_API_KEY = getattr(settings, 'GROK_API_KEY', '')
GROK_MODEL = getattr(settings, 'GROK_MODEL', 'grok-3-mini')


def call_grok(text: str, chunk_index: int = 1, total_chunks: int = 1) -> dict:
    if not GROK_API_KEY:
        return error_result('Grok API key not configured', 'grok')

    prompt = build_chunk_prompt(text, chunk_index, total_chunks)
    try:
        response = requests.post(
            GROK_API_URL,
            headers={
                'Authorization': f'Bearer {GROK_API_KEY}',
                'Content-Type': 'application/json',
            },
            json={
                'model': GROK_MODEL,
                'messages': [
                    {'role': 'system', 'content': system_prompt()},
                    {'role': 'user', 'content': prompt},
                ],
                'temperature': 0,
                'max_tokens': 3000,
            },
            timeout=45,
        )
        response.raise_for_status()
        return parse_openai_response(response.json(), 'grok')
    except requests.exceptions.RequestException as e:
        return error_result(f'Grok unavailable: {str(e)}', 'grok')
