"""
Binoculars provider — local, statistical AI detection (perplexity ratio).
=========================================================================

This is a *different kind* of signal from the LLM-judge providers (groq,
gemini, etc.). Those ask a language model to judge prose patterns. This
measures how predictable the text is to a pair of small base models, using
the Binoculars method (Hans et al., 2024):

    B(x) = log_perplexity_observer(x) / cross_perplexity(observer, performer)

  - Lower B  → more machine-like (predictable)  → higher ai_probability
  - Higher B → more human-like                  → lower  ai_probability

The two-model *ratio* (not raw single-model perplexity) is the whole point:
it normalises away text that is simply inherently predictable, which is what
makes naive GPT-2 perplexity over-flag formal human writing.

Design notes
------------
* CPU-friendly by default: two small same-family models (base + instruct)
  that SHARE a tokenizer — required by the method. Defaults to SmolLM2-360M.
  Override via settings for bigger/more accurate pairs (needs RAM/GPU).
* Heavy deps (torch, transformers) are imported lazily inside _lazy_load so
  the app/admin still import fine when they aren't installed. If they're
  missing, this provider returns a clean error_result instead of crashing.
* Implements the standard provider contract: call_binoculars(text,
  chunk_index, total_chunks) -> result dict, so it slots straight into
  services.detect_ai_content / detect_chunked like every other provider.

⚠️  IMPORTANT — calibration & fairness:
  - THRESHOLD is model-pair specific and MUST be calibrated (see BINOCULARS.md).
    The default is a starting guess, not a tuned value.
  - Perplexity-based detection over-flags non-native English and heavily
    edited text. Treat the output as a probabilistic cross-check, never a
    verdict — especially anywhere it could affect a person.

Configurable settings (all optional):
    BINOCULARS_OBSERVER_MODEL   (str)   default 'HuggingFaceTB/SmolLM2-360M'
    BINOCULARS_PERFORMER_MODEL  (str)   default 'HuggingFaceTB/SmolLM2-360M-Instruct'
    BINOCULARS_THRESHOLD        (float) default 0.90   (calibrate this!)
    BINOCULARS_STEEPNESS        (float) default 8.0    (sigmoid sharpness)
    BINOCULARS_MAX_TOKENS       (int)   default 512    (per scoring window)
    BINOCULARS_MAX_SENTENCES    (int)   default 40     (per chunk, cost cap)
    BINOCULARS_DEVICE           (str)   default 'cpu'  ('cuda' if you have a GPU)
"""
import logging
import math
import re

from django.conf import settings

from .base import error_result, verdict_from_pct

logger = logging.getLogger(__name__)

# ─── Config ──────────────────────────────────────────────────────────────────
OBSERVER_MODEL = getattr(settings, 'BINOCULARS_OBSERVER_MODEL', 'HuggingFaceTB/SmolLM2-360M')
PERFORMER_MODEL = getattr(settings, 'BINOCULARS_PERFORMER_MODEL', 'HuggingFaceTB/SmolLM2-360M-Instruct')
THRESHOLD = float(getattr(settings, 'BINOCULARS_THRESHOLD', 0.90))
STEEPNESS = float(getattr(settings, 'BINOCULARS_STEEPNESS', 8.0))
MAX_TOKENS = int(getattr(settings, 'BINOCULARS_MAX_TOKENS', 512))
MAX_SENTENCES_SCORED = int(getattr(settings, 'BINOCULARS_MAX_SENTENCES', 40))
DEVICE = getattr(settings, 'BINOCULARS_DEVICE', 'cpu')

_MIN_SCORE_TOKENS = 16   # below this, the ratio is too noisy to trust

# ─── Lazy-loaded model state ─────────────────────────────────────────────────
_TORCH = None
_TOKENIZER = None
_OBSERVER = None
_PERFORMER = None
_LOAD_ERROR = None
_LOADED = False


def _lazy_load():
    """Load torch + the two models once. Records an error string on failure
    (e.g. deps not installed) instead of raising, so callers degrade cleanly."""
    global _TORCH, _TOKENIZER, _OBSERVER, _PERFORMER, _LOAD_ERROR, _LOADED
    if _LOADED:
        return
    _LOADED = True
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        _TORCH = torch
        logger.info(
            f'[BINOCULARS] loading observer={OBSERVER_MODEL} '
            f'performer={PERFORMER_MODEL} on {DEVICE}'
        )
        # Both models MUST share this tokenizer (same-family base/instruct).
        _TOKENIZER = AutoTokenizer.from_pretrained(OBSERVER_MODEL)
        dtype = torch.float32 if DEVICE == 'cpu' else torch.float16
        _OBSERVER = AutoModelForCausalLM.from_pretrained(
            OBSERVER_MODEL, torch_dtype=dtype
        ).to(DEVICE).eval()
        _PERFORMER = AutoModelForCausalLM.from_pretrained(
            PERFORMER_MODEL, torch_dtype=dtype
        ).to(DEVICE).eval()
        logger.info('[BINOCULARS] models loaded')
    except Exception as e:  # noqa: BLE001 — any failure → graceful degrade
        _LOAD_ERROR = str(e)
        logger.error(f'[BINOCULARS] load failed: {e}')


def _binoculars_b(text: str):
    """Return (B, n_tokens) for a piece of text, or None if too short/invalid.

    B = mean observer NLL on the actual tokens
        ÷ mean cross-entropy(performer distribution, observer logprobs)
    """
    text = (text or '').strip()
    if not text:
        return None
    torch = _TORCH

    enc = _TOKENIZER(text, return_tensors='pt', truncation=True, max_length=MAX_TOKENS)
    input_ids = enc['input_ids'].to(DEVICE)
    attn = enc['attention_mask'].to(DEVICE)
    n_tokens = int(attn.sum().item())
    if n_tokens < _MIN_SCORE_TOKENS:
        return None

    with torch.no_grad():
        obs_logits = _OBSERVER(input_ids, attention_mask=attn).logits
        perf_logits = _PERFORMER(input_ids, attention_mask=attn).logits

    # Shift for next-token prediction.
    obs_logits = obs_logits[:, :-1, :].float()
    perf_logits = perf_logits[:, :-1, :].float()
    labels = input_ids[:, 1:]
    mask = attn[:, 1:].float()

    logp_obs = torch.log_softmax(obs_logits, dim=-1)
    p_perf = torch.softmax(perf_logits, dim=-1)

    # Observer perplexity: mean negative log-likelihood of the real tokens.
    nll_obs = -logp_obs.gather(-1, labels.unsqueeze(-1)).squeeze(-1)        # [1, T-1]
    # Cross-perplexity: how surprised the observer is by the performer's dist.
    x_ent = -(p_perf * logp_obs).sum(-1)                                    # [1, T-1]

    denom = mask.sum().clamp(min=1.0)
    log_ppl = (nll_obs * mask).sum() / denom
    x_ppl = (x_ent * mask).sum() / denom
    if float(x_ppl) <= 1e-9:
        return None

    return float(log_ppl / x_ppl), n_tokens


def _b_to_prob(b: float) -> float:
    """Map a Binoculars score to ai_probability in [0, 1].
    Lower B (more machine-like) → higher probability. Sigmoid around THRESHOLD."""
    val = 1.0 / (1.0 + math.exp(-STEEPNESS * (THRESHOLD - b)))
    return max(0.0, min(1.0, val))


def _split_sentences(text: str) -> list:
    parts = re.split(r'(?<=[.!?])\s+|\n+', text or '')
    return [p for p in (s.strip() for s in parts) if p]


def _label_for(pct: float) -> str:
    if pct >= 70:
        return 'AI'
    if pct < 40:
        return 'Human'
    return 'Mixed'


def _score_sentences(text: str, fallback_prob: float) -> list:
    """Per-sentence breakdown for the UI. Scores each long-enough sentence
    individually (bounded by MAX_SENTENCES_SCORED to cap CPU cost); short
    sentences inherit the chunk-level probability."""
    out = []
    scored = 0
    for sentence in _split_sentences(text):
        prob = fallback_prob
        if scored < MAX_SENTENCES_SCORED:
            res = _binoculars_b(sentence)
            if res is not None:
                prob = _b_to_prob(res[0])
                scored += 1
        out.append({
            'text': sentence,
            'ai_probability': round(prob, 4),
            'label': _label_for(prob * 100),
        })
    return out


def _explain(b: float, prob: float, n_tokens: int) -> str:
    pct = round(prob * 100)
    if pct >= 70:
        lean = 'likely AI-generated'
    elif pct < 40:
        lean = 'likely human-written'
    else:
        lean = 'mixed / inconclusive'
    return (
        f'Statistical (Binoculars) analysis over {n_tokens} tokens: score '
        f'{b:.3f} vs threshold {THRESHOLD:.3f} (lower = more machine-like) '
        f'→ {pct}% AI, {lean}. This is a perplexity-ratio signal, most reliable '
        f'as a cross-check alongside the language-model detectors; it can '
        f'over-flag non-native English and heavily edited text.'
    )


def call_binoculars(text: str, chunk_index: int = 1, total_chunks: int = 1) -> dict:
    """Standard provider entry point. Matches the call_X(text, chunk_index,
    total_chunks) -> result-dict contract used by services.detect_chunked."""
    _lazy_load()
    if _LOAD_ERROR:
        return error_result(
            f'Binoculars unavailable (install requirements-ml.txt): {_LOAD_ERROR}',
            'binoculars',
        )

    chunk = _binoculars_b(text)
    if chunk is None:
        return error_result('Text too short for statistical (Binoculars) analysis.', 'binoculars')

    b, n_tokens = chunk
    prob = _b_to_prob(b)
    ai_pct = round(prob * 100)

    return {
        'ai_probability': round(prob, 4),
        'human_probability': round(1 - prob, 4),
        'mixed_probability': 0.0,
        'verdict': verdict_from_pct(ai_pct),
        'explanation': _explain(b, prob, n_tokens),
        'sentences': _score_sentences(text, fallback_prob=prob),
        'provider': 'binoculars',
        'raw': {
            'binoculars_score': round(b, 5),
            'tokens': n_tokens,
            'threshold': THRESHOLD,
            'observer': OBSERVER_MODEL,
            'performer': PERFORMER_MODEL,
        },
        'error': None,
    }


def binoculars_raw_score(text: str):
    """Helper for threshold calibration — returns the raw Binoculars score B
    (or None if the text is too short). See BINOCULARS.md."""
    _lazy_load()
    if _LOAD_ERROR:
        raise RuntimeError(f'Binoculars unavailable: {_LOAD_ERROR}')
    res = _binoculars_b(text)
    return None if res is None else res[0]
