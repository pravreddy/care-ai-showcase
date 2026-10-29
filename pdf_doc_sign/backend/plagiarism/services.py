"""
Plagiarism Checker — Detection Service
========================================
Providers:
  - 'groq'      : FREE. Uses Groq + Llama 3.1 to analyse text for copied patterns,
                  well-known phrases, and structural plagiarism signals.
                  NOTE: This is pattern analysis, not a live web search.
  - 'copyleaks' : Paid. Real web+academic database search via Copyleaks API.
                  Sign up at https://copyleaks.com/api

Groq is the default — free, fast, and good enough for student use cases.
Add COPYLEAKS_API_KEY + COPYLEAKS_EMAIL to .env for real source matching.
"""
import json as json_lib
import logging
import uuid
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

DEFAULT_PROVIDER = getattr(settings, 'DEFAULT_PLAGIARISM_PROVIDER', 'groq')

# Groq
GROQ_API_KEY = getattr(settings, 'GROQ_API_KEY', '')
GROQ_MODEL = getattr(settings, 'GROQ_MODEL', 'llama-3.1-8b-instant')
GROQ_API_URL = 'https://api.groq.com/openai/v1/chat/completions'

# Copyleaks (optional paid provider)
COPYLEAKS_API_KEY = getattr(settings, 'COPYLEAKS_API_KEY', '')
COPYLEAKS_EMAIL = getattr(settings, 'COPYLEAKS_EMAIL', '')

MAX_CHARS = 3000


# ─── Main Entry Point ──────────────────────────────────────────────────────────

def check_plagiarism(text: str, provider: str = None) -> dict:
    """
    Check text for plagiarism.
    Returns a standardised dict regardless of which provider is used.
    """
    provider = provider or DEFAULT_PROVIDER
    trimmed = text[:MAX_CHARS].strip()

    if len(trimmed) < 100:
        return _insufficient_text_result(provider)

    if provider == 'copyleaks':
        return _check_with_copyleaks(trimmed)
    return _check_with_groq(trimmed)


# ─── Groq (FREE — Pattern Analysis) ───────────────────────────────────────────

def _check_with_groq(text: str) -> dict:
    """
    Uses Groq's free Llama 3.1 to detect plagiarism signals:
    - Well-known copied phrases or passages
    - Sudden style shifts suggesting pasted content
    - Overly formal or encyclopaedic language inconsistent with context
    - Structural patterns common in copied academic text

    This is NOT a live web search — it cannot verify URLs.
    Use Copyleaks for real source matching.
    """
    if not GROQ_API_KEY:
        return _error_result(
            'Groq API key not configured. Add GROQ_API_KEY to .env. '
            'Get your free key at console.groq.com',
            'groq',
        )

    prompt = _build_groq_prompt(text)

    try:
        response = requests.post(
            GROQ_API_URL,
            headers={
                'Authorization': f'Bearer {GROQ_API_KEY}',
                'Content-Type': 'application/json',
            },
            json={
                'model': GROQ_MODEL,
                'messages': [
                    {
                        'role': 'system',
                        'content': (
                            'You are an expert academic integrity analyst. '
                            'Detect signs of plagiarism, copied text, and unoriginal content. '
                            'Always respond with valid JSON only — no markdown, no extra text.'
                        ),
                    },
                    {'role': 'user', 'content': prompt},
                ],
                'temperature': 0,
                'max_tokens': 2000,
            },
            timeout=30,
        )
        response.raise_for_status()
        raw = response.json()
    except requests.exceptions.Timeout:
        return _error_result('Groq API timed out. Please try again.', 'groq')
    except requests.exceptions.RequestException as e:
        logger.error(f'Groq plagiarism API error: {e}')
        return _error_result(f'Groq unavailable: {str(e)}', 'groq')

    return _parse_groq_response(raw)


def _build_groq_prompt(text: str) -> str:
    return f"""Analyse the following text for plagiarism and unoriginal content.

TEXT TO ANALYSE:
---
{text}
---

Look for these plagiarism signals:
- Passages that appear to be copied from well-known sources (Wikipedia, textbooks, news)
- Sudden changes in writing style, vocabulary, or tone that suggest pasted content
- Overly formal, encyclopaedic, or textbook-style language inconsistent with the rest
- Repetitive sentence structures typical of copied academic text
- Generic filler content that appears AI-generated or template-based

Respond with ONLY this JSON structure, no other text:
{{
  "plagiarism_score": <float 0.0-1.0>,
  "original_score": <float 0.0-1.0>,
  "verdict": "<LIKELY_PLAGIARISED|POSSIBLY_SIMILAR|MOSTLY_ORIGINAL>",
  "explanation": "<2-3 sentence summary of findings>",
  "sentences": [
    {{
      "text": "<exact sentence from text>",
      "plagiarism_probability": <float 0.0-1.0>,
      "label": "<Copied|Similar|Original>",
      "possible_source": "<describe likely source type e.g. Wikipedia, textbook, news article, or null>"
    }}
  ]
}}

Rules:
- plagiarism_score + original_score should sum to approximately 1.0
- Label sentences: Copied (>=0.7), Similar (0.3-0.7), Original (<0.3)
- Include ALL sentences, max 30
- possible_source: describe the type of source you suspect, do NOT invent specific URLs
- Be conservative — only flag as Copied if you are confident"""


def _parse_groq_response(raw: dict) -> dict:
    try:
        content = raw['choices'][0]['message']['content'].strip()
        if content.startswith('```'):
            content = content.split('```')[1]
            if content.startswith('json'):
                content = content[4:]
        parsed = json_lib.loads(content.strip())

        plag_score = float(parsed.get('plagiarism_score', 0))
        orig_score = float(parsed.get('original_score', 1 - plag_score))
        verdict = parsed.get('verdict', _verdict_from_score(plag_score))
        sentences = parsed.get('sentences', [])

        return {
            'plagiarism_score': round(plag_score, 4),
            'original_score': round(orig_score, 4),
            'verdict': verdict,
            'explanation': parsed.get('explanation', ''),
            'sentence_matches': sentences,
            'source_matches': [],  # Groq cannot return real URLs
            'provider': 'groq',
            'raw': raw,
            'error': None,
        }
    except (KeyError, ValueError, IndexError, json_lib.JSONDecodeError) as e:
        logger.error(f'Groq plagiarism parse error: {e} | raw: {raw}')
        return _error_result(f'Unexpected Groq response: {str(e)}', 'groq')


# ─── Copyleaks (Paid — Real Source Matching) ──────────────────────────────────

def _check_with_copyleaks(text: str) -> dict:
    """
    Copyleaks API — real-time web + academic database search.
    Requires COPYLEAKS_API_KEY and COPYLEAKS_EMAIL in settings.
    Sign up at https://copyleaks.com/api
    Note: Copyleaks uses an async scan model. This implementation
    uses their Education API sync endpoint for short texts.
    """
    if not COPYLEAKS_API_KEY or not COPYLEAKS_EMAIL:
        return _error_result(
            'Copyleaks not configured. Add COPYLEAKS_API_KEY and COPYLEAKS_EMAIL to .env.',
            'copyleaks',
        )

    try:
        # Step 1: Authenticate
        auth_response = requests.post(
            'https://id.copyleaks.com/v3/account/login/api',
            json={'email': COPYLEAKS_EMAIL, 'key': COPYLEAKS_API_KEY},
            timeout=15,
        )
        auth_response.raise_for_status()
        access_token = auth_response.json().get('access_token', '')

        if not access_token:
            return _error_result('Copyleaks authentication failed.', 'copyleaks')

        # Step 2: Submit scan (Education API)
        scan_id = str(uuid.uuid4())
        scan_response = requests.put(
            f'https://api.copyleaks.com/v3/education/submit/text/{scan_id}',
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
            },
            json={
                'text': text,
                'filename': 'scan.txt',
                'properties': {
                    'webhooks': {'status': ''},  # no webhook for now
                    'sensitiveDataProtection': True,
                },
            },
            timeout=30,
        )
        scan_response.raise_for_status()

        # Copyleaks is async — return pending state with scan_id
        # In production you'd handle the webhook callback
        return {
            'plagiarism_score': None,
            'original_score': None,
            'verdict': 'PENDING',
            'explanation': (
                f'Copyleaks scan submitted (ID: {scan_id}). '
                'Results are delivered asynchronously via webhook. '
                'Check back shortly.'
            ),
            'sentence_matches': [],
            'source_matches': [],
            'provider': 'copyleaks',
            'scan_id': scan_id,
            'raw': scan_response.json() if scan_response.content else {},
            'error': None,
        }

    except requests.exceptions.RequestException as e:
        logger.error(f'Copyleaks API error: {e}')
        return _error_result(f'Copyleaks unavailable: {str(e)}', 'copyleaks')


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _verdict_from_score(score: float) -> str:
    pct = score * 100
    if pct >= 50:
        return 'LIKELY_PLAGIARISED'
    elif pct >= 20:
        return 'POSSIBLY_SIMILAR'
    return 'MOSTLY_ORIGINAL'


def _insufficient_text_result(provider: str) -> dict:
    return {
        'plagiarism_score': None,
        'original_score': None,
        'verdict': 'INSUFFICIENT_TEXT',
        'explanation': None,
        'sentence_matches': [],
        'source_matches': [],
        'provider': provider,
        'raw': {},
        'error': 'Not enough text to analyse (minimum 100 characters needed).',
    }


def _error_result(message: str, provider: str) -> dict:
    return {
        'plagiarism_score': None,
        'original_score': None,
        'verdict': 'ERROR',
        'explanation': None,
        'sentence_matches': [],
        'source_matches': [],
        'provider': provider,
        'raw': {},
        'error': message,
    }
