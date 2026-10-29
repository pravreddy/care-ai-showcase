"""
Groq provider — FREE, 14,400 req/day
https://console.groq.com

Supports two tiers:
- Quick scan: Llama 3.1 8B (131K tokens/min, instant)
- Deep scan: Llama 3.3 70B (6K tokens/min, needs 65s gaps in Celery)
"""
import logging
import requests
from django.conf import settings

from .base import system_prompt, build_chunk_prompt, parse_openai_response, error_result

logger = logging.getLogger(__name__)

GROQ_API_KEY = getattr(settings, 'GROQ_API_KEY', '')
GROQ_MODEL_QUICK = getattr(settings, 'GROQ_MODEL', 'llama-3.1-8b-instant')
GROQ_MODEL_DEEP = 'llama-3.3-70b-versatile'
GROQ_API_URL = 'https://api.groq.com/openai/v1/chat/completions'


def call_groq_quick(text: str, chunk_index: int = 1, total_chunks: int = 1) -> dict:
    """Quick scan: Llama 8B, instant."""
    return _call_groq(text, GROQ_MODEL_QUICK, chunk_index, total_chunks)


def call_groq_deep(text: str, chunk_index: int = 1, total_chunks: int = 1) -> dict:
    """Deep scan: Llama 70B, background."""
    return _call_groq(text, GROQ_MODEL_DEEP, chunk_index, total_chunks)


def _call_groq(text: str, model: str, chunk_index: int, total_chunks: int) -> dict:
    if not GROQ_API_KEY:
        return error_result(
            'Groq API key not configured. Get free key at console.groq.com',
            'groq',
        )

    prompt = build_chunk_prompt(text, chunk_index, total_chunks)

    try:
        response = requests.post(
            GROQ_API_URL,
            headers={
                'Authorization': f'Bearer {GROQ_API_KEY}',
                'Content-Type': 'application/json',
            },
            json={
                'model': model,
                'messages': [
                    {'role': 'system', 'content': system_prompt()},
                    {'role': 'user', 'content': prompt},
                ],
                'temperature': 0,
                'max_tokens': 3000,
            },
            timeout=60,
        )
        response.raise_for_status()
        return parse_openai_response(response.json(), 'groq')
    except requests.exceptions.Timeout:
        return error_result('Groq timed out', 'groq')
    except requests.exceptions.RequestException as e:
        logger.error(f'Groq API error: {e}')
        return error_result(f'Groq unavailable: {str(e)}', 'groq')
