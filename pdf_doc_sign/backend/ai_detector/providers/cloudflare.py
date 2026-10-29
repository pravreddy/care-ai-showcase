"""
Cloudflare Workers AI provider — FREE 10K neurons/day
https://dash.cloudflare.com → Workers & Pages → AI

Uses Cloudflare's own API format (not OpenAI-compatible).
"""
import logging
import json as json_lib
import requests
from django.conf import settings

from .base import (
    system_prompt, build_chunk_prompt,
    verdict_from_pct, error_result,
)

logger = logging.getLogger(__name__)

CLOUDFLARE_ACCOUNT_ID = getattr(settings, 'CLOUDFLARE_ACCOUNT_ID', '')
CLOUDFLARE_API_TOKEN = getattr(settings, 'CLOUDFLARE_API_TOKEN', '')
CLOUDFLARE_MODEL = getattr(settings, 'CLOUDFLARE_MODEL', '@cf/meta/llama-3.1-8b-instruct')


def call_cloudflare(text: str, chunk_index: int = 1, total_chunks: int = 1) -> dict:
    """Cloudflare Workers AI. Different API format than OpenAI."""
    if not CLOUDFLARE_ACCOUNT_ID or not CLOUDFLARE_API_TOKEN:
        return error_result(
            'Cloudflare credentials not configured. Get free at cloudflare.com/developer-platform/workers-ai',
            'cloudflare',
        )

    prompt = build_chunk_prompt(text, chunk_index, total_chunks)
    url = f'https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/{CLOUDFLARE_MODEL}'

    try:
        response = requests.post(
            url,
            headers={
                'Authorization': f'Bearer {CLOUDFLARE_API_TOKEN}',
                'Content-Type': 'application/json',
            },
            json={
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
        return _parse_cloudflare_response(response.json())
    except requests.exceptions.Timeout:
        return error_result('Cloudflare timed out', 'cloudflare')
    except requests.exceptions.RequestException as e:
        logger.error(f'Cloudflare AI error: {e}')
        return error_result(f'Cloudflare unavailable: {str(e)}', 'cloudflare')


def _parse_cloudflare_response(raw: dict) -> dict:
    """Cloudflare response format: {'result': {'response': '...'}, 'success': true}"""
    try:
        if not raw.get('success'):
            errors = raw.get('errors', [{'message': 'unknown'}])
            return error_result(f"Cloudflare error: {errors[0].get('message', 'unknown')}", 'cloudflare')

        content = raw['result']['response'].strip()
        if content.startswith('```'):
            content = content.split('```')[1]
            if content.startswith('json'):
                content = content[4:]
        parsed = json_lib.loads(content.strip())

        ai_score = float(parsed.get('ai_probability', 0))
        human_score = float(parsed.get('human_probability', 1 - ai_score))
        sentences = parsed.get('sentences', [])

        return {
            'ai_probability': round(ai_score, 4),
            'human_probability': round(human_score, 4),
            'mixed_probability': 0.0,
            'verdict': verdict_from_pct(ai_score * 100),
            'explanation': parsed.get('explanation', ''),
            'sentences': sentences,
            'provider': 'cloudflare',
            'raw': raw,
            'error': None,
        }
    except (KeyError, ValueError, json_lib.JSONDecodeError) as e:
        logger.error(f'Cloudflare parse error: {e} | content: {raw}')
        return error_result(f'Cloudflare parse error: {str(e)}', 'cloudflare')
