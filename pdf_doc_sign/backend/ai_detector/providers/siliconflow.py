"""
SiliconFlow provider — FREE tier, OpenAI-compatible
https://siliconflow.cn

NOTE: China-hosted. Skip if UK data residency matters.
Supports Llama 3.3 70B, DeepSeek, Qwen.
"""
import logging
import requests
from django.conf import settings

from .base import (
    system_prompt, build_chunk_prompt,
    parse_openai_response, error_result,
)

logger = logging.getLogger(__name__)

SILICONFLOW_API_KEY = getattr(settings, 'SILICONFLOW_API_KEY', '')
SILICONFLOW_MODEL = getattr(settings, 'SILICONFLOW_MODEL', 'meta-llama/Llama-3.3-70B-Instruct')
SILICONFLOW_API_URL = 'https://api.siliconflow.cn/v1/chat/completions'


def call_siliconflow(text: str, chunk_index: int = 1, total_chunks: int = 1) -> dict:
    """SiliconFlow API call (OpenAI-compatible)."""
    if not SILICONFLOW_API_KEY:
        return error_result(
            'SiliconFlow API key not configured. Get free key at siliconflow.cn',
            'siliconflow',
        )

    prompt = build_chunk_prompt(text, chunk_index, total_chunks)
    try:
        response = requests.post(
            SILICONFLOW_API_URL,
            headers={
                'Authorization': f'Bearer {SILICONFLOW_API_KEY}',
                'Content-Type': 'application/json',
            },
            json={
                'model': SILICONFLOW_MODEL,
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
        return parse_openai_response(response.json(), 'siliconflow')
    except requests.exceptions.Timeout:
        return error_result('SiliconFlow timed out', 'siliconflow')
    except requests.exceptions.RequestException as e:
        logger.error(f'SiliconFlow API error: {e}')
        return error_result(f'SiliconFlow unavailable: {str(e)}', 'siliconflow')
