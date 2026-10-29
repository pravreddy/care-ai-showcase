"""
HuggingFace provider — Legacy, no chunking
Binary classifier only (no sentence-level analysis).
Kept for backwards compatibility. Prefer Groq or Gemini.
"""
import logging
import requests
from django.conf import settings

from .base import verdict_from_pct, error_result

logger = logging.getLogger(__name__)

HF_API_URL = getattr(
    settings, 'HF_AI_DETECTOR_URL',
    'https://api-inference.huggingface.co/models/desklib/ai-text-detector-v1.01',
)
HF_TOKEN = getattr(settings, 'HF_API_TOKEN', '')


def detect_with_huggingface(text: str) -> dict:
    """Binary classifier — just AI% or Human%, no sentence analysis."""
    headers = {'Content-Type': 'application/json'}
    if HF_TOKEN:
        headers['Authorization'] = f'Bearer {HF_TOKEN}'
    try:
        response = requests.post(
            HF_API_URL, headers=headers,
            json={'inputs': text}, timeout=30,
        )
        if response.status_code == 410:
            return error_result('HuggingFace model retired. Use Groq instead.', 'huggingface')
        response.raise_for_status()
        raw = response.json()
    except requests.exceptions.RequestException as e:
        return error_result(f'HuggingFace unavailable: {str(e)}', 'huggingface')

    try:
        items = raw[0] if isinstance(raw[0], list) else raw
        ai_score, human_score = 0.0, 0.0
        for item in items:
            label = item.get('label', '').upper()
            score = float(item.get('score', 0))
            if label in ('LABEL_1', 'FAKE', 'AI'):
                ai_score = score
            elif label in ('LABEL_0', 'REAL', 'HUMAN'):
                human_score = score
        return {
            'ai_probability': round(ai_score, 4),
            'human_probability': round(human_score, 4),
            'verdict': verdict_from_pct(ai_score * 100),
            'explanation': None,
            'sentences': [],
            'provider': 'huggingface',
            'raw': raw,
            'error': None,
        }
    except (IndexError, KeyError, TypeError, ValueError) as e:
        return error_result(f'HuggingFace parse error: {str(e)}', 'huggingface')
