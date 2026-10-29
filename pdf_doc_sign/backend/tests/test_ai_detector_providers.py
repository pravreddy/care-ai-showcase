"""
AI Detector — Provider-level tests with mocked HTTP.

Scope: each provider module — verify the request payload, headers, error
handling, and response parsing without making real API calls.

Pattern: patch `requests.post` (and `requests.get` where needed) to return
canned envelopes. This is cheap, deterministic, and catches 80% of the bugs
that would otherwise only surface in production.
"""
import json
from unittest.mock import patch, MagicMock

import pytest
from django.test import override_settings

from ai_detector.providers import groq, gemini, cloudflare, mistral, siliconflow, grok, openai
from ai_detector.providers import base


# ---------------------------------------------------------------------------
# Groq provider
# ---------------------------------------------------------------------------

class TestGroqProvider:

    def _envelope(self, payload):
        return {'choices': [{'message': {'content': json.dumps(payload)}}]}

    @override_settings()
    def test_missing_api_key_returns_error(self):
        with patch.object(groq, 'GROQ_API_KEY', ''):
            result = groq.call_groq_quick('some text')
        assert result['error'] is not None
        assert 'api key' in result['error'].lower() or 'not configured' in result['error'].lower()
        assert result['provider'] == 'groq'

    @patch('ai_detector.providers.groq.requests.post')
    def test_happy_path_quick_scan(self, mock_post, mock_llm_response_human):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: self._envelope(mock_llm_response_human),
        )
        mock_post.return_value.raise_for_status = MagicMock()

        with patch.object(groq, 'GROQ_API_KEY', 'test-key'):
            result = groq.call_groq_quick('real text to analyse')

        assert result['error'] is None
        assert result['ai_probability'] == pytest.approx(0.08)
        # Verify the request was built correctly.
        args, kwargs = mock_post.call_args
        assert kwargs['headers']['Authorization'] == 'Bearer test-key'
        body = kwargs['json']
        assert body['temperature'] == 0  # determinism
        assert len(body['messages']) == 2  # system + user
        assert body['messages'][0]['role'] == 'system'
        assert body['messages'][1]['role'] == 'user'

    @patch('ai_detector.providers.groq.requests.post')
    def test_happy_path_deep_scan_uses_70b(self, mock_post, mock_llm_response_ai):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: self._envelope(mock_llm_response_ai),
        )
        mock_post.return_value.raise_for_status = MagicMock()

        with patch.object(groq, 'GROQ_API_KEY', 'test-key'):
            groq.call_groq_deep('text')

        body = mock_post.call_args.kwargs['json']
        assert '70b' in body['model'].lower()

    @patch('ai_detector.providers.groq.requests.post', side_effect=__import__('requests').exceptions.Timeout())
    def test_timeout_returns_error(self, mock_post):
        with patch.object(groq, 'GROQ_API_KEY', 'test-key'):
            result = groq.call_groq_quick('text')
        assert result['error'] is not None
        assert 'timed out' in result['error'].lower()

    @patch('ai_detector.providers.groq.requests.post')
    def test_http_error_returns_error(self, mock_post):
        import requests
        mock_post.side_effect = requests.exceptions.RequestException('connection refused')
        with patch.object(groq, 'GROQ_API_KEY', 'test-key'):
            result = groq.call_groq_quick('text')
        assert result['error'] is not None
        assert 'unavailable' in result['error'].lower() or 'connection' in result['error'].lower()

    @patch('ai_detector.providers.groq.requests.post')
    def test_malformed_llm_json_surfaces_error(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {'choices': [{'message': {'content': 'not json'}}]},
        )
        mock_post.return_value.raise_for_status = MagicMock()

        with patch.object(groq, 'GROQ_API_KEY', 'test-key'):
            result = groq.call_groq_quick('text')
        assert result['error'] is not None
        assert result['verdict'] == 'ERROR'


# ---------------------------------------------------------------------------
# Gemini provider — single-call, 1M context
# ---------------------------------------------------------------------------

class TestGeminiProvider:

    def _gemini_envelope(self, payload):
        return {
            'candidates': [{
                'content': {'parts': [{'text': json.dumps(payload)}]}
            }]
        }

    def test_missing_api_key_returns_error(self):
        with patch.object(gemini, 'GEMINI_API_KEY', ''):
            result = gemini.call_gemini('text')
        assert result['error'] is not None
        assert result['provider'] == 'gemini'

    @patch('ai_detector.providers.gemini.requests.post')
    def test_happy_path_full_document(self, mock_post, mock_gemini_v2_response_paraphrased):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: self._gemini_envelope(mock_gemini_v2_response_paraphrased),
        )
        mock_post.return_value.raise_for_status = MagicMock()

        with patch.object(gemini, 'GEMINI_API_KEY', 'test-key'):
            result = gemini.call_gemini('some longer document text')

        assert result['error'] is None
        # V2: Python computes score from dimensions. A=0.75, B=0.80, C=0.05
        # A>=0.6 AND B>=0.6 -> ai_prob = 0.55 + (0.75-0.6)*0.5 = 0.625
        assert result['ai_probability'] == pytest.approx(0.625, abs=0.01)
        assert result['chunks_total'] == 1  # no chunking for Gemini
        assert result['provider'] == 'gemini'
        assert 'dimensions' in result  # V2 exposes dimension scores

    @patch('ai_detector.providers.gemini.requests.post')
    def test_system_instruction_uses_system_prompt(self, mock_post, mock_llm_response_human):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: self._gemini_envelope(mock_llm_response_human),
        )
        mock_post.return_value.raise_for_status = MagicMock()

        with patch.object(gemini, 'GEMINI_API_KEY', 'test-key'):
            gemini.call_gemini('text')

        body = mock_post.call_args.kwargs['json']
        assert 'system_instruction' in body
        # The system instruction must carry our calibrated prompt.
        sys_text = body['system_instruction']['parts'][0]['text']
        assert 'DIMENSION' in sys_text or 'prose-structure' in sys_text.lower() or 'THREE independent' in sys_text

    @patch('ai_detector.providers.gemini.requests.post')
    def test_malformed_response_returns_error(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {'unexpected': 'shape'},
        )
        mock_post.return_value.raise_for_status = MagicMock()

        with patch.object(gemini, 'GEMINI_API_KEY', 'test-key'):
            result = gemini.call_gemini('text')
        assert result['error'] is not None


# ---------------------------------------------------------------------------
# Cloudflare, Mistral, SiliconFlow, Grok, OpenAI — all OpenAI-compatible
# ---------------------------------------------------------------------------

class TestOpenAICompatibleProviders:
    """Grouped tests — all these providers share parse_openai_response."""

    def _envelope(self, payload):
        return {'choices': [{'message': {'content': json.dumps(payload)}}]}

    @patch('ai_detector.providers.mistral.requests.post')
    def test_mistral_happy_path(self, mock_post, mock_llm_response_human):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: self._envelope(mock_llm_response_human),
        )
        mock_post.return_value.raise_for_status = MagicMock()

        with patch.object(mistral, 'MISTRAL_API_KEY', 'test-key'):
            result = mistral.call_mistral('text')
        assert result['error'] is None
        assert result['provider'] == 'mistral'

    @patch('ai_detector.providers.siliconflow.requests.post')
    def test_siliconflow_happy_path(self, mock_post, mock_llm_response_ai):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: self._envelope(mock_llm_response_ai),
        )
        mock_post.return_value.raise_for_status = MagicMock()

        with patch.object(siliconflow, 'SILICONFLOW_API_KEY', 'test-key'):
            result = siliconflow.call_siliconflow('text')
        assert result['error'] is None
        assert result['provider'] == 'siliconflow'

    @patch('ai_detector.providers.grok.requests.post')
    def test_grok_happy_path(self, mock_post, mock_llm_response_ai):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: self._envelope(mock_llm_response_ai),
        )
        mock_post.return_value.raise_for_status = MagicMock()

        with patch.object(grok, 'GROK_API_KEY', 'test-key'):
            result = grok.call_grok('text')
        assert result['error'] is None
        assert result['provider'] == 'grok'

    @patch('ai_detector.providers.openai.requests.post')
    def test_openai_happy_path(self, mock_post, mock_llm_response_human):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: self._envelope(mock_llm_response_human),
        )
        mock_post.return_value.raise_for_status = MagicMock()

        with patch.object(openai, 'OPENAI_API_KEY', 'test-key'):
            result = openai.call_openai('text')
        assert result['error'] is None
        assert result['provider'] == 'openai'

    @patch('ai_detector.providers.cloudflare.requests.post')
    def test_cloudflare_happy_path(self, mock_post, mock_llm_response_human):
        # Cloudflare uses a different envelope: {'success': true, 'result': {'response': '...'}}
        cf_envelope = {
            'success': True,
            'result': {'response': json.dumps(mock_llm_response_human)},
        }
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: cf_envelope,
        )
        mock_post.return_value.raise_for_status = MagicMock()

        with patch.multiple(
            cloudflare,
            CLOUDFLARE_ACCOUNT_ID='acc',
            CLOUDFLARE_API_TOKEN='tok',
        ):
            result = cloudflare.call_cloudflare('text')
        assert result['error'] is None
        assert result['provider'] == 'cloudflare'

    def test_missing_api_keys_return_errors(self):
        """Every provider must fail gracefully when unconfigured."""
        with patch.object(mistral, 'MISTRAL_API_KEY', ''):
            assert mistral.call_mistral('x')['error'] is not None
        with patch.object(siliconflow, 'SILICONFLOW_API_KEY', ''):
            assert siliconflow.call_siliconflow('x')['error'] is not None
        with patch.object(grok, 'GROK_API_KEY', ''):
            assert grok.call_grok('x')['error'] is not None
        with patch.object(openai, 'OPENAI_API_KEY', ''):
            assert openai.call_openai('x')['error'] is not None
        with patch.multiple(cloudflare, CLOUDFLARE_ACCOUNT_ID='', CLOUDFLARE_API_TOKEN=''):
            assert cloudflare.call_cloudflare('x')['error'] is not None


# ---------------------------------------------------------------------------
# Auto-fallback orchestrator
# ---------------------------------------------------------------------------

class TestAutoFallback:

    def test_falls_back_when_first_provider_unconfigured(self):
        from ai_detector import fallback
        # All keys empty → final error result with all providers tried.
        with patch.multiple(
            fallback.gemini, GEMINI_API_KEY='',
        ), patch.multiple(
            fallback.mistral, MISTRAL_API_KEY='',
        ), patch.multiple(
            fallback.groq, GROQ_API_KEY='',
        ), patch.multiple(
            fallback.siliconflow, SILICONFLOW_API_KEY='',
        ), patch.multiple(
            fallback.cloudflare, CLOUDFLARE_ACCOUNT_ID='', CLOUDFLARE_API_TOKEN='',
        ):
            result = fallback.detect_auto_fallback('some text')
        assert result['error'] is not None
        assert result['provider'] == 'auto'

    @patch('ai_detector.providers.gemini.call_gemini')
    def test_stops_at_first_successful_provider(self, mock_gemini):
        from ai_detector import fallback
        mock_gemini.return_value = {
            'ai_probability': 0.5,
            'human_probability': 0.5,
            'verdict': 'POSSIBLY_AI',
            'explanation': 'test',
            'sentences': [],
            'error': None,
            'provider': 'gemini',
        }
        with patch.object(fallback.gemini, 'GEMINI_API_KEY', 'key'):
            result = fallback.detect_auto_fallback('text')
        assert result['error'] is None
        assert result['provider_used'] == 'gemini'
        mock_gemini.assert_called_once()

    @patch('ai_detector.providers.groq.call_groq_quick')
    @patch('ai_detector.providers.mistral.call_mistral')
    @patch('ai_detector.providers.gemini.call_gemini')
    def test_cascades_gemini_to_mistral_to_groq(
        self, mock_gemini, mock_mistral, mock_groq,
    ):
        from ai_detector import fallback
        # Gemini fails, Mistral fails, Groq succeeds.
        mock_gemini.return_value = base.error_result('gemini down', 'gemini')
        mock_mistral.return_value = base.error_result('mistral down', 'mistral')
        mock_groq.return_value = {
            'ai_probability': 0.3, 'human_probability': 0.7,
            'verdict': 'LIKELY_HUMAN', 'explanation': 'ok',
            'sentences': [], 'error': None,
        }
        with patch.multiple(
            fallback.gemini, GEMINI_API_KEY='k1',
        ), patch.multiple(
            fallback.mistral, MISTRAL_API_KEY='k2',
        ), patch.multiple(
            fallback.groq, GROQ_API_KEY='k3',
        ), patch.multiple(
            fallback.siliconflow, SILICONFLOW_API_KEY='',
        ):
            result = fallback.detect_auto_fallback('some longer text that gets chunked')
        assert result['error'] is None
        assert result['provider_used'] == 'groq'
