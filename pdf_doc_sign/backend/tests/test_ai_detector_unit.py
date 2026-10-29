"""
AI Detector — Unit Tests for base.py

Scope: pure functions only. No network, no DB, no Django views.

What's covered:
- split_into_chunks: edge cases around chunk boundaries, sentence-respecting splits
- system_prompt / detection_rules: string contracts (won't break downstream parsers)
- build_chunk_prompt / build_full_doc_prompt: JSON schema presence, chunk notes
- parse_openai_response: happy path, markdown fences, malformed JSON, missing keys
- verdict_from_pct: threshold boundaries
- error_result / insufficient_text_result: response shape
- build_summary_explanation: tone changes across score bands
- build_partial_result: progress math
- detect_chunked: aggregation, rate-limit skip, all-chunks-failed path
- detect_chunked_resumable: skip_chunks, progress callback, 429 raises
"""
import json

import pytest

from ai_detector.providers import base


# ---------------------------------------------------------------------------
# split_into_chunks
# ---------------------------------------------------------------------------

class TestSplitIntoChunks:

    def test_short_text_single_chunk(self):
        text = 'A short sentence.'
        chunks = base.split_into_chunks(text)
        assert chunks == ['A short sentence.']

    def test_empty_text_returns_single_empty_chunk(self):
        # split_into_chunks is called after MIN_CHARS guard; empty input should
        # not crash — it returns [''] which the pipeline treats as a no-op chunk.
        chunks = base.split_into_chunks('')
        assert chunks == ['']

    def test_exactly_chunk_size_is_single_chunk(self):
        text = 'a' * base.CHUNK_SIZE
        chunks = base.split_into_chunks(text)
        assert len(chunks) == 1

    def test_over_chunk_size_splits(self):
        text = ('Sentence one is here. ' * 300)  # ~6300 chars, 2–3 chunks
        chunks = base.split_into_chunks(text)
        assert len(chunks) >= 2
        # All chunks must be non-empty
        assert all(c.strip() for c in chunks)

    def test_chunks_capped_at_max(self):
        # 50k chars → much more than MAX_CHUNKS × CHUNK_SIZE potential,
        # but MAX_TOTAL_CHARS truncates at 50k and MAX_CHUNKS caps.
        text = 'x' * (base.MAX_TOTAL_CHARS * 2)
        chunks = base.split_into_chunks(text)
        assert len(chunks) <= base.MAX_CHUNKS

    def test_respects_sentence_boundaries_when_possible(self):
        # Build text where a sentence boundary sits near the chunk edge.
        para = 'This is a sentence. ' * 160  # ~3200 chars
        chunks = base.split_into_chunks(para)
        # Every chunk (except possibly the last) should end shortly after
        # a '. ' so we're not mid-sentence.
        for chunk in chunks[:-1]:
            # Allow small slack — splitter searches a 300-char window.
            assert chunk.rstrip().endswith('.') or chunk.rstrip().endswith('sentence.')

    def test_max_total_chars_truncates(self):
        text = 'x' * (base.MAX_TOTAL_CHARS + 10000)
        chunks = base.split_into_chunks(text)
        total = sum(len(c) for c in chunks)
        # Total text processed must not exceed the hard cap.
        assert total <= base.MAX_TOTAL_CHARS


# ---------------------------------------------------------------------------
# Prompt builders — contract tests
# ---------------------------------------------------------------------------

class TestPromptBuilders:

    def test_system_prompt_mentions_both_dimensions(self):
        """Guards against accidentally reverting the recalibration."""
        p = base.system_prompt()
        assert 'A' in p and 'B' in p
        assert 'prose-structure' in p.lower() or 'prose structure' in p.lower()
        assert 'content-specificity' in p.lower() or 'content specificity' in p.lower()

    def test_system_prompt_insists_on_json_only(self):
        assert 'JSON only' in base.system_prompt() or 'valid JSON' in base.system_prompt()

    def test_detection_rules_contains_classification_thresholds(self):
        rules = base.detection_rules()
        # Our calibration rule says A>=0.6 AND B>=0.6 → flag AI. If someone
        # accidentally lowers the bar to A<0.4 or removes it, this fails.
        assert '0.6' in rules
        assert 'DIMENSION A' in rules
        assert 'DIMENSION B' in rules

    def test_build_chunk_prompt_includes_text_and_schema(self):
        prompt = base.build_chunk_prompt('Hello world.', chunk_index=1, total_chunks=1)
        assert 'Hello world.' in prompt
        # JSON schema keys must appear so the LLM returns the right shape.
        assert '"ai_probability"' in prompt
        assert '"human_probability"' in prompt
        assert '"sentences"' in prompt

    def test_build_chunk_prompt_adds_note_for_multi_chunk(self):
        single = base.build_chunk_prompt('x', chunk_index=1, total_chunks=1)
        multi = base.build_chunk_prompt('x', chunk_index=2, total_chunks=5)
        assert 'section 2 of 5' in multi
        assert 'section' not in single.lower().replace('sections in the prompt', '') or \
            'section 1 of 1' not in single  # no chunk note for single chunk

    def test_build_full_doc_prompt_marks_complete(self):
        prompt = base.build_full_doc_prompt('Hello world.')
        assert 'COMPLETE document' in prompt
        assert '"ai_probability"' in prompt


# ---------------------------------------------------------------------------
# parse_openai_response
# ---------------------------------------------------------------------------

class TestParseOpenAIResponse:

    def _envelope(self, payload):
        return {'choices': [{'message': {'content': json.dumps(payload)}}]}

    def test_happy_path(self, mock_llm_response_human):
        raw = self._envelope(mock_llm_response_human)
        result = base.parse_openai_response(raw, 'groq')
        assert result['error'] is None
        assert result['ai_probability'] == pytest.approx(0.08)
        assert result['human_probability'] == pytest.approx(0.92)
        assert result['verdict'] == 'LIKELY_HUMAN'
        assert result['provider'] == 'groq'
        assert len(result['sentences']) == 2

    def test_strips_markdown_json_fence(self, mock_llm_response_ai):
        # LLMs sometimes wrap JSON in ```json ... ``` despite being told not to.
        content = '```json\n' + json.dumps(mock_llm_response_ai) + '\n```'
        raw = {'choices': [{'message': {'content': content}}]}
        result = base.parse_openai_response(raw, 'groq')
        assert result['error'] is None
        assert result['ai_probability'] == pytest.approx(0.89)

    def test_strips_bare_markdown_fence(self, mock_llm_response_ai):
        content = '```\n' + json.dumps(mock_llm_response_ai) + '\n```'
        raw = {'choices': [{'message': {'content': content}}]}
        result = base.parse_openai_response(raw, 'groq')
        assert result['error'] is None

    def test_malformed_json_returns_error(self):
        raw = {'choices': [{'message': {'content': 'not actually json'}}]}
        result = base.parse_openai_response(raw, 'groq')
        assert result['error'] is not None
        assert result['verdict'] == 'ERROR'

    def test_missing_choices_returns_error(self):
        raw = {'unexpected': 'shape'}
        result = base.parse_openai_response(raw, 'groq')
        assert result['error'] is not None

    def test_infers_human_probability_when_missing(self):
        # Some LLMs omit human_probability; we must derive it.
        payload = {
            'ai_probability': 0.4,
            'explanation': 'x',
            'sentences': [],
        }
        raw = self._envelope(payload)
        result = base.parse_openai_response(raw, 'groq')
        assert result['human_probability'] == pytest.approx(0.6)


# ---------------------------------------------------------------------------
# Verdict thresholds
# ---------------------------------------------------------------------------

class TestVerdictFromPct:

    @pytest.mark.parametrize('pct,expected', [
        (0, 'LIKELY_HUMAN'),
        (20, 'LIKELY_HUMAN'),
        (39.9, 'LIKELY_HUMAN'),
        (40, 'POSSIBLY_AI'),
        (69.9, 'POSSIBLY_AI'),
        (70, 'LIKELY_AI'),
        (100, 'LIKELY_AI'),
    ])
    def test_boundaries(self, pct, expected):
        assert base.verdict_from_pct(pct) == expected


# ---------------------------------------------------------------------------
# Error helpers
# ---------------------------------------------------------------------------

class TestErrorHelpers:

    def test_insufficient_text_shape(self):
        r = base.insufficient_text_result('groq')
        assert r['verdict'] == 'INSUFFICIENT_TEXT'
        assert r['ai_probability'] is None
        assert r['provider'] == 'groq'
        assert 'minimum' in r['error'].lower() or '50' in r['error']

    def test_error_result_shape(self):
        r = base.error_result('boom', 'groq')
        assert r['verdict'] == 'ERROR'
        assert r['error'] == 'boom'
        assert r['provider'] == 'groq'
        assert r['sentences'] == []


# ---------------------------------------------------------------------------
# Summary explanation — tone bands
# ---------------------------------------------------------------------------

class TestBuildSummaryExplanation:

    def test_low_score_sounds_human(self):
        msg = base.build_summary_explanation(5, 0, 50, 1, [])
        assert 'human-written' in msg.lower()

    def test_mid_score_warns_false_positives(self):
        msg = base.build_summary_explanation(25, 3, 50, 1, [])
        assert 'false positive' in msg.lower() or 'formal writing' in msg.lower()

    def test_high_score_lists_ai_signals(self):
        msg = base.build_summary_explanation(85, 40, 50, 3, [])
        lower = msg.lower()
        assert 'ai generation' in lower or 'ai-generated' in lower

    def test_embeds_stats(self):
        msg = base.build_summary_explanation(50, 10, 100, 4, [])
        assert '10 of 100' in msg
        assert '4 analysed section' in msg

    def test_deduplicates_explanations(self):
        explanations = [
            'Parallel structure observed. Other stuff.',
            'Parallel structure observed. Different other stuff.',  # near-duplicate first sentence
            'Something else entirely happened here.',
        ]
        msg = base.build_summary_explanation(60, 5, 10, 1, explanations)
        # We keep at most 3 unique points but near-duplicates should collapse.
        assert msg.count('Parallel structure observed') == 1


# ---------------------------------------------------------------------------
# build_partial_result
# ---------------------------------------------------------------------------

class TestBuildPartialResult:

    def test_computes_weighted_average(self):
        sentences = [
            {'text': 'x', 'label': 'AI'},
            {'text': 'y', 'label': 'Human'},
        ]
        chunk_scores = [
            {'ai_probability': 0.8, 'char_count': 1000},
            {'ai_probability': 0.2, 'char_count': 1000},
        ]
        partial = base.build_partial_result(
            sentences, chunk_scores, ['a', 'b'], [], 'groq', 2,
        )
        assert partial['ai_probability'] == pytest.approx(0.5)
        assert partial['ai_sentence_count'] == 1
        assert partial['total_sentence_count'] == 2
        assert partial['chunks_analysed'] == 2
        assert partial['chunks_total'] == 2

    def test_handles_empty_scores(self):
        partial = base.build_partial_result([], [], ['a'], [], 'groq', 0)
        # Must not divide by zero.
        assert partial['ai_probability'] == 0 or partial['ai_probability'] == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# detect_chunked — orchestration with fake api_call_fn
# ---------------------------------------------------------------------------

class TestDetectChunked:

    def _fake_api(self, ai_prob, sentences=None, explanation='test'):
        """Return an api_call_fn that always returns the given score."""
        def _call(chunk, chunk_index=1, total_chunks=1):
            return {
                'ai_probability': ai_prob,
                'human_probability': 1 - ai_prob,
                'explanation': explanation,
                'sentences': sentences or [],
                'error': None,
            }
        return _call

    def _fake_api_erroring(self, error_msg):
        def _call(chunk, chunk_index=1, total_chunks=1):
            return base.error_result(error_msg, 'test')
        return _call

    def test_single_chunk_aggregation(self):
        chunks = ['short text']
        result = base.detect_chunked(chunks, 'short text', self._fake_api(0.7), 'test')
        assert result['error'] is None
        assert result['ai_probability'] == pytest.approx(0.7)
        assert result['verdict'] == 'LIKELY_AI'
        assert result['chunks_analysed'] == 1
        assert result['chunks_total'] == 1

    def test_multiple_chunks_weighted_average(self):
        chunks = ['aaa' * 100, 'bbb' * 100]  # equal sizes
        # Both chunks return 0.5 → average is 0.5
        result = base.detect_chunked(chunks, 'x', self._fake_api(0.5), 'test')
        assert result['ai_probability'] == pytest.approx(0.5)

    def test_all_chunks_fail_returns_error(self):
        chunks = ['a', 'b']
        result = base.detect_chunked(
            chunks, 'x', self._fake_api_erroring('API down'), 'test',
        )
        assert result['error'] is not None
        assert 'API down' in result['error']

    def test_rate_limit_skips_chunk(self):
        chunks = ['a', 'b']
        # First chunk rate-limits, second succeeds
        call_count = {'n': 0}
        def _mixed(chunk, chunk_index=1, total_chunks=1):
            call_count['n'] += 1
            if chunk_index == 1:
                return base.error_result('429 rate limited', 'test')
            return {
                'ai_probability': 0.3,
                'human_probability': 0.7,
                'explanation': 'ok',
                'sentences': [],
                'error': None,
            }
        result = base.detect_chunked(chunks, 'x', _mixed, 'test')  # not groq_deep → skip not sleep
        # Should have succeeded with only the second chunk contributing.
        assert result['error'] is None
        assert result['chunks_analysed'] == 1
        assert result['chunks_failed'] >= 1

    def test_sentences_aggregated_across_chunks(self):
        chunks = ['a' * 100, 'b' * 100]
        def _call(chunk, chunk_index=1, total_chunks=1):
            return {
                'ai_probability': 0.3,
                'human_probability': 0.7,
                'explanation': f'chunk {chunk_index}',
                'sentences': [
                    {'text': f'sentence from chunk {chunk_index}',
                     'label': 'AI', 'ai_probability': 0.8},
                ],
                'error': None,
            }
        result = base.detect_chunked(chunks, 'x', _call, 'test')
        assert len(result['sentences']) == 2
        assert result['ai_sentence_count'] == 2


# ---------------------------------------------------------------------------
# detect_chunked_resumable
# ---------------------------------------------------------------------------

class TestDetectChunkedResumable:

    def _ok_api(self, chunk, chunk_index=1, total_chunks=1):
        return {
            'ai_probability': 0.4,
            'human_probability': 0.6,
            'explanation': f'chunk {chunk_index}',
            'sentences': [
                {'text': f'sent {chunk_index}', 'label': 'Mixed', 'ai_probability': 0.4},
            ],
            'error': None,
        }

    def test_skips_already_done_chunks(self):
        chunks = ['a' * 100, 'b' * 100, 'c' * 100]
        calls = []
        def _tracking(chunk, chunk_index=1, total_chunks=1):
            calls.append(chunk_index)
            return self._ok_api(chunk, chunk_index, total_chunks)

        result = base.detect_chunked_resumable(
            chunks, 'x', _tracking, 'groq',
            skip_chunks=2,
            existing_sentences=[{'text': 'prev', 'label': 'Human', 'ai_probability': 0.1}],
        )
        # Only the final chunk should be called.
        assert calls == [3]
        assert result['error'] is None
        # Existing sentence should be preserved alongside the new one.
        assert len(result['sentences']) == 2

    def test_429_raises_for_retry_after_saving_progress(self):
        chunks = ['a' * 100, 'b' * 100]
        saved = []
        def _progress(partial):
            saved.append(partial)

        def _api_429(chunk, chunk_index=1, total_chunks=1):
            return base.error_result('429 rate limit', 'groq')

        with pytest.raises(Exception, match='Rate limited'):
            base.detect_chunked_resumable(
                chunks, 'x', _api_429, 'groq',
                skip_chunks=0,
                existing_sentences=[],
                progress_callback=_progress,
            )
        # Progress must have been saved before raising — otherwise retries
        # would re-do chunks that actually succeeded.
        assert len(saved) == 1

    def test_progress_callback_fires_per_chunk(self):
        chunks = ['a' * 100, 'b' * 100, 'c' * 100]
        saved = []
        def _progress(partial):
            saved.append(partial['chunks_analysed'])

        base.detect_chunked_resumable(
            chunks, 'x', self._ok_api, 'groq',
            skip_chunks=0,
            existing_sentences=[],
            progress_callback=_progress,
        )
        # Callback fires after each chunk (1, 2, 3).
        assert saved == [1, 2, 3]
