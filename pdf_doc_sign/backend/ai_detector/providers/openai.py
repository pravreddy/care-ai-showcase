"""
OpenAI provider — PAID
https://platform.openai.com
"""
import logging
import requests
from django.conf import settings

from .base import (
    system_prompt, build_chunk_prompt,
    parse_openai_response, error_result,
)

logger = logging.getLogger(__name__)

OPENAI_API_KEY = getattr(settings, 'OPENAI_API_KEY', '')
OPENAI_MODEL = getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini')
# Base URL is configurable so this provider can also point at any
# OpenAI-compatible server (e.g. a local Ollama at http://careai-ollama:11434/v1).
OPENAI_BASE_URL = getattr(settings, 'OPENAI_BASE_URL', 'https://api.openai.com/v1').rstrip('/')
# Per-request timeout (seconds). 300s default because a local model on CPU can
# take >120s on a single chunk; too low a value makes local chunks time out.
OPENAI_TIMEOUT = getattr(settings, 'OPENAI_TIMEOUT', 300)


def call_openai(text: str, chunk_index: int = 1, total_chunks: int = 1) -> dict:
    if not OPENAI_API_KEY:
        return error_result('OpenAI API key not configured', 'openai')

    prompt = build_chunk_prompt(text, chunk_index, total_chunks)
    try:
        response = requests.post(
            f'{OPENAI_BASE_URL}/chat/completions',
            headers={
                'Authorization': f'Bearer {OPENAI_API_KEY}',
                'Content-Type': 'application/json',
            },
            json={
                'model': OPENAI_MODEL,
                'messages': [
                    {'role': 'system', 'content': system_prompt()},
                    {'role': 'user', 'content': prompt},
                ],
                'temperature': 0,
                'max_tokens': 3000,
                # Force valid-JSON output. Ollama and OpenAI both honour this;
                # it stops small local models truncating/malforming the JSON,
                # which is what makes the per-sentence data (and the Turnitin
                # report's highlighting) reliable.
                'response_format': {'type': 'json_object'},
            },
            timeout=OPENAI_TIMEOUT,
        )
        response.raise_for_status()
        return parse_openai_response(response.json(), 'openai')
    except requests.exceptions.RequestException as e:
        return error_result(f'OpenAI unavailable: {str(e)}', 'openai')
