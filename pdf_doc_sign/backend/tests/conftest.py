"""
Shared pytest fixtures for the SignSimple backend test suite.

Scope guidance:
- Put cross-module fixtures here (e.g. `mock_llm_response`).
- Keep feature-specific fixtures in their own test file or a dedicated conftest.
"""
import pytest


# ---------------------------------------------------------------------------
# AI detector shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_llm_response_human():
    """Standard LLM response payload for a clearly human-written text."""
    return {
        'ai_probability': 0.08,
        'human_probability': 0.92,
        'explanation': 'Text contains specific personal anecdotes and irregular sentence rhythms.',
        'sentences': [
            {'text': 'I remember the day clearly.', 'ai_probability': 0.05, 'label': 'Human'},
            {'text': 'It was pouring down.', 'ai_probability': 0.10, 'label': 'Human'},
        ],
    }


@pytest.fixture
def mock_llm_response_ai():
    """Standard LLM response payload for a clearly AI-generated text."""
    return {
        'ai_probability': 0.89,
        'human_probability': 0.11,
        'explanation': (
            'Polished transitions and parallel clause structure observed '
            'across multiple paragraphs.'
        ),
        'sentences': [
            {'text': 'Furthermore, this ensures consistency.', 'ai_probability': 0.92, 'label': 'AI'},
            {'text': 'In addition, it supports compliance.', 'ai_probability': 0.88, 'label': 'AI'},
        ],
    }


@pytest.fixture
def mock_llm_response_paraphrased():
    """LLM response for AI-paraphrased human content — the critical middle case."""
    return {
        'ai_probability': 0.72,
        'human_probability': 0.28,
        'explanation': (
            'Named individuals and dates present (Dimension B high) but prose '
            'structure is polished with Furthermore/Overall transitions and '
            'parallel regulation lists (Dimension A high). Classified as '
            'AI-paraphrased human draft.'
        ),
        'sentences': [
            {
                'text': 'On 13 March 2026, our carer delivered breakfast.',
                'ai_probability': 0.68,
                'label': 'AI',
            },
            {
                'text': 'Furthermore, this ensures person-centred care under Regulation 9.',
                'ai_probability': 0.82,
                'label': 'AI',
            },
        ],
    }


@pytest.fixture
def mock_gemini_v2_response_paraphrased():
    """Gemini V2 response: raw dimension scores instead of computed ai_probability.

    Python classification rules will compute the final score from these.
    A=0.75, B=0.80, C=0.05 → A≥0.6 AND B≥0.6 → ai_prob = 0.55 + (0.75-0.6)*0.5 = 0.625
    """
    return {
        'dimensions': {
            'prose_structure_A': 0.75,
            'content_specificity_B': 0.80,
            'mechanical_signals_C': 0.05,
        },
        'explanation': (
            'High Dimension A: polished transitions (Furthermore, In addition), '
            'parallel regulation lists, balanced clause construction. '
            'High Dimension B: named individuals, specific dates, Birdie references. '
            'Low Dimension C: no mechanical human signals found.'
        ),
        'c_signals_found': [],
        'sentences': [
            {
                'text': 'On 13 March 2026, our carer delivered breakfast.',
                'ai_probability': 0.68,
                'label': 'AI',
            },
            {
                'text': 'Furthermore, this ensures person-centred care under Regulation 9.',
                'ai_probability': 0.82,
                'label': 'AI',
            },
        ],
    }


@pytest.fixture
def mock_gemini_v2_response_paraphrased():
    """Gemini V2 response: raw dimension scores instead of computed ai_probability.

    Python classification rules will compute the final score from these.
    A=0.75, B=0.80, C=0.05 → A≥0.6 AND B≥0.6 → ai_prob = 0.55 + (0.75-0.6)*0.5 = 0.625
    """
    return {
        'dimensions': {
            'prose_structure_A': 0.75,
            'content_specificity_B': 0.80,
            'mechanical_signals_C': 0.05,
        },
        'explanation': (
            'High Dimension A: polished transitions (Furthermore, In addition), '
            'parallel regulation lists, balanced clause construction. '
            'High Dimension B: named individuals, specific dates, Birdie references. '
            'Low Dimension C: no mechanical human signals found.'
        ),
        'c_signals_found': [],
        'sentences': [
            {
                'text': 'On 13 March 2026, our carer delivered breakfast.',
                'ai_probability': 0.68,
                'label': 'AI',
            },
            {
                'text': 'Furthermore, this ensures person-centred care under Regulation 9.',
                'ai_probability': 0.82,
                'label': 'AI',
            },
        ],
    }


def _groq_wrap(payload: dict) -> dict:
    """Wrap an LLM payload in the Groq/OpenAI-compatible response envelope."""
    import json
    return {
        'choices': [
            {'message': {'content': json.dumps(payload)}}
        ]
    }


@pytest.fixture
def groq_wrap():
    """Expose the wrapper as a fixture so tests can use it directly."""
    return _groq_wrap
