"""
Google Gemini provider — FREE, 1000 req/day, 1M context window
https://aistudio.google.com/app/apikey

Unique feature: Single API call for entire document (no chunking needed).
"""
import logging
import json as json_lib
import requests
from django.conf import settings

from .base import (
    system_prompt, build_full_doc_prompt_v2,
    verdict_from_pct, error_result, apply_classification_rules,
    build_summary_explanation,
)

logger = logging.getLogger(__name__)

GEMINI_API_KEY = getattr(settings, 'GEMINI_API_KEY', '')
GEMINI_MODEL = getattr(settings, 'GEMINI_MODEL', 'gemini-2.5-flash-lite')
GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models'


def call_gemini(full_text: str) -> dict:
    """
    Call Gemini with entire document in one request.
    1M token context — no chunking needed.
    """
    if not GEMINI_API_KEY:
        return error_result(
            'Gemini API key not configured. Get free key at aistudio.google.com/apikey',
            'gemini',
        )

    prompt = build_full_doc_prompt_v2(full_text)
    url = f'{GEMINI_API_URL}/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}'

    try:
        response = requests.post(
            url,
            headers={'Content-Type': 'application/json'},
            json={
                'system_instruction': {
                    'parts': [{'text': system_prompt()}]
                },
                'contents': [{
                    'parts': [{'text': prompt}]
                }],
                'generationConfig': {
                    'temperature': 0,
                    'maxOutputTokens': 65536,
                    'responseMimeType': 'application/json',
                },
            },
            timeout=180,
        )
        response.raise_for_status()
        return _parse_gemini_response(response.json())
    except requests.exceptions.Timeout:
        return error_result('Gemini timed out', 'gemini')
    except requests.exceptions.RequestException as e:
        logger.error(f'Gemini API error: {e}')
        return error_result(f'Gemini unavailable: {str(e)}', 'gemini')


def _parse_gemini_response(raw: dict) -> dict:
    """Parse Gemini V2 response: extract dimensions, apply Python classification."""
    try:
        # Check for truncated response (MAX_TOKENS)
        finish_reason = raw.get('candidates', [{}])[0].get('finishReason', '')
        if finish_reason == 'MAX_TOKENS':
            logger.warning('Gemini response truncated (MAX_TOKENS) — response may be incomplete')

        content = raw['candidates'][0]['content']['parts'][0]['text'].strip()
        if content.startswith('```'):
            content = content.split('```')[1]
            if content.startswith('json'):
                content = content[4:]
        parsed = json_lib.loads(content.strip())

        sentences = parsed.get('sentences', [])
        ai_sentence_count = sum(1 for s in sentences if s.get('label') == 'AI')
        total_sentence_count = len(sentences)

        # V2: Extract dimension scores and apply Python classification
        dims = parsed.get('dimensions', {})
        dim_a = float(dims.get('prose_structure_A', 0.5))
        dim_b = float(dims.get('content_specificity_B', 0.5))
        dim_c = float(dims.get('mechanical_signals_C', 0.0))
        c_signals = parsed.get('c_signals_found', [])

        classification = apply_classification_rules(dim_a, dim_b, dim_c, c_signals)
        ai_score = classification['ai_probability']
        ai_pct = round(ai_score * 100)

        # Build explanation combining LLM's analysis + Python's reasoning
        llm_explanation = parsed.get('explanation', '')
        python_reason = classification.get('classification_reason', '')
        explanation = build_summary_explanation(
            ai_pct, ai_sentence_count, total_sentence_count, 1,
            [llm_explanation] if llm_explanation else []
        )
        # Append the dimension scores for transparency
        explanation += (f' Dimension scores: A={dim_a:.2f} (prose structure), '
                        f'B={dim_b:.2f} (content specificity), '
                        f'C={dim_c:.2f} (mechanical signals).')
        if c_signals:
            explanation += f' Mechanical signals found: {", ".join(c_signals[:5])}.'

        logger.info(
            f'Gemini V2 dimensions: A={dim_a:.2f}, B={dim_b:.2f}, C={dim_c:.2f}, '
            f'c_signals={c_signals}, '
            f'python_ai_prob={ai_score:.4f}, verdict={classification["verdict"]}'
        )

        return {
            'ai_probability': ai_score,
            'human_probability': round(1 - ai_score, 4),
            'mixed_probability': 0.0,
            'verdict': classification['verdict'],
            'explanation': explanation,
            'sentences': sentences,
            'provider': 'gemini',
            'chunks_analysed': 1,
            'chunks_total': 1,
            'chunks_failed': 0,
            'ai_sentence_count': ai_sentence_count,
            'total_sentence_count': total_sentence_count,
            'dimensions': classification.get('dimensions', {}),
            'c_signals_found': c_signals,
            'classification_reason': python_reason,
            'raw': raw,
            'error': None,
        }
    except (KeyError, ValueError, IndexError, json_lib.JSONDecodeError) as e:
        logger.error(f'Gemini parse error: {e} | content: {raw}')
        return error_result(f'Unexpected Gemini response: {str(e)}', 'gemini')
