"""
Binoculars provider tests — no ML deps required.

These exercise the scoring math and the result-shaping in call_binoculars by
mocking the model forward pass (_binoculars_b), so they run anywhere pytest
runs without installing torch/transformers.
"""
from unittest.mock import patch

from django.test import SimpleTestCase

from ai_detector.providers import binoculars as B


class TestBinocularsScoreMapping(SimpleTestCase):
    """_b_to_prob: lower Binoculars score => more AI."""

    def test_low_score_is_more_ai(self):
        self.assertGreater(B._b_to_prob(B.THRESHOLD - 0.3), 0.5)

    def test_high_score_is_more_human(self):
        self.assertLess(B._b_to_prob(B.THRESHOLD + 0.3), 0.5)

    def test_probability_is_bounded(self):
        self.assertGreaterEqual(B._b_to_prob(-10.0), 0.0)
        self.assertLessEqual(B._b_to_prob(10.0), 1.0)

    def test_monotonic_decreasing_in_b(self):
        a = B._b_to_prob(B.THRESHOLD - 0.4)
        b = B._b_to_prob(B.THRESHOLD)
        c = B._b_to_prob(B.THRESHOLD + 0.4)
        self.assertGreater(a, b)
        self.assertGreater(b, c)


class TestSentenceSplitter(SimpleTestCase):

    def test_splits_on_terminators_and_newlines(self):
        out = B._split_sentences('One sentence. Two here!\nThree?')
        self.assertEqual(len(out), 3)

    def test_ignores_empty(self):
        self.assertEqual(B._split_sentences('   \n  '), [])


class TestLabelFor(SimpleTestCase):

    def test_thresholds(self):
        self.assertEqual(B._label_for(85), 'AI')
        self.assertEqual(B._label_for(50), 'Mixed')
        self.assertEqual(B._label_for(10), 'Human')


class TestCallBinoculars(SimpleTestCase):

    def test_load_error_returns_clean_error_result(self):
        with patch.object(B, '_lazy_load', lambda: None), \
             patch.object(B, '_LOAD_ERROR', 'torch not installed'):
            res = B.call_binoculars('some reasonably long text here', 1, 1)
        self.assertEqual(res['provider'], 'binoculars')
        self.assertIsNotNone(res['error'])
        self.assertIsNone(res['ai_probability'])

    def test_too_short_returns_error_result(self):
        with patch.object(B, '_lazy_load', lambda: None), \
             patch.object(B, '_LOAD_ERROR', None), \
             patch.object(B, '_binoculars_b', lambda text: None):
            res = B.call_binoculars('short', 1, 1)
        self.assertEqual(res['provider'], 'binoculars')
        self.assertIsNotNone(res['error'])

    def test_ai_leaning_result_shape(self):
        # B below threshold → AI-leaning probability.
        fake = (B.THRESHOLD - 0.4, 120)
        with patch.object(B, '_lazy_load', lambda: None), \
             patch.object(B, '_LOAD_ERROR', None), \
             patch.object(B, '_binoculars_b', lambda text: fake):
            res = B.call_binoculars('Sentence one here. Sentence two follows.', 1, 1)

        self.assertEqual(res['provider'], 'binoculars')
        self.assertIsNone(res['error'])
        self.assertGreater(res['ai_probability'], 0.5)
        self.assertEqual(res['human_probability'], round(1 - res['ai_probability'], 4))
        self.assertIn(res['verdict'], ('LIKELY_AI', 'POSSIBLY_AI', 'LIKELY_HUMAN'))
        self.assertTrue(res['sentences'])
        for s in res['sentences']:
            self.assertIn(s['label'], ('AI', 'Human', 'Mixed'))
        self.assertEqual(res['raw']['threshold'], B.THRESHOLD)

    def test_human_leaning_result_shape(self):
        # B above threshold → human-leaning probability.
        fake = (B.THRESHOLD + 0.4, 120)
        with patch.object(B, '_lazy_load', lambda: None), \
             patch.object(B, '_LOAD_ERROR', None), \
             patch.object(B, '_binoculars_b', lambda text: fake):
            res = B.call_binoculars('A plain human sentence. Another one here.', 1, 1)
        self.assertLess(res['ai_probability'], 0.5)
        self.assertIsNone(res['error'])
