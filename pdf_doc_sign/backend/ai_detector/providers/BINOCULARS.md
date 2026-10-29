# Binoculars — local statistical AI detector

A perplexity-ratio AI detector that runs on your own server, added as the
`binoculars` provider in the existing `ai_detector` app. It complements the
LLM-judge providers (groq, gemini, …) rather than replacing them.

## What it is

Two small same-family models (a base "observer" and an instruct "performer"
that **share a tokenizer**) score how predictable the text is:

```
B(x) = mean observer NLL on the real tokens
       ÷ mean cross-entropy(performer distribution, observer log-probs)
```

- **Low B**  → predictable → more machine-like → higher `ai_probability`
- **High B** → less predictable → more human-like → lower `ai_probability`

The two-model *ratio* (Binoculars, Hans et al. 2024) is what makes it robust
versus naive single-model GPT-2 perplexity, which over-flags formal human
writing.

## Why it's worth having

It's an **independent** signal from the LLM judges. The best use isn't raw
accuracy — it's **confidence via agreement**: when Binoculars and the LLM
judge agree, you can trust the result more; when they diverge, show
"uncertain" instead of a number. The LLM judge is still better on the hard
"AI-paraphrased human draft" case (high prose-structure + high specificity),
which pure perplexity misses.

## Install

ML deps are kept out of the base image. Install where the detector runs
(usually the Celery worker):

```bash
pip install -r requirements-ml.txt
```

First call downloads the model pair (~0.7 GB for the default SmolLM2-360M
base+instruct). Each worker that loads the models holds ~3 GB resident — run
it on a dedicated/limited worker rather than every worker.

## Use

Pass `provider=binoculars` to the scan endpoints:

```
POST /api/ai-detector/scan-text/   { "text": "...", "provider": "binoculars" }
POST /api/ai-detector/scan/        (multipart: file=..., provider=binoculars)
```

`GET /api/ai-detector/providers/` reports it as available only when the ML
deps are importable.

## Settings (all optional)

| Setting                      | Default                                   | Notes                                   |
|------------------------------|-------------------------------------------|-----------------------------------------|
| `BINOCULARS_OBSERVER_MODEL`  | `HuggingFaceTB/SmolLM2-360M`              | base model                              |
| `BINOCULARS_PERFORMER_MODEL` | `HuggingFaceTB/SmolLM2-360M-Instruct`     | instruct twin, **same tokenizer**       |
| `BINOCULARS_THRESHOLD`       | `0.90`                                    | **calibrate this** (see below)          |
| `BINOCULARS_STEEPNESS`       | `8.0`                                     | sigmoid sharpness around the threshold  |
| `BINOCULARS_MAX_TOKENS`      | `512`                                     | per scoring window                      |
| `BINOCULARS_MAX_SENTENCES`   | `40`                                      | sentences scored individually per chunk |
| `BINOCULARS_DEVICE`          | `cpu`                                     | `cuda` if you add a GPU                  |

Bigger pairs (e.g. Qwen2.5-0.5B base+instruct, or 7B Falcon pairs on a GPU)
are more accurate but heavier. Keep observer/performer in the **same family**
so they share a tokenizer.

## Calibrate the threshold (do this before trusting scores)

The default `0.90` is a placeholder — the right value is specific to the model
pair. Collect a handful of known-human and known-AI texts and look at where
their raw scores separate:

```python
from ai_detector.providers.binoculars import binoculars_raw_score

for label, text in samples:        # samples you trust
    print(label, round(binoculars_raw_score(text), 3))
```

Human texts cluster at higher B, AI texts at lower B. Set
`BINOCULARS_THRESHOLD` between the two clusters. If you care more about *not*
false-accusing humans, push the threshold lower (fewer AI calls, fewer false
positives).

## Fairness / limitations (read this)

Perplexity-based detection **over-flags non-native English and heavily edited
text**. Given the care-sector coursework audience (many ESL writers), treat
the output as a probabilistic cross-check, never a verdict, and never the sole
basis for any decision about a person. This is the same caution the LLM-judge
prompt already encodes with its Dimension-C / ESL anchors.

## Possible next step (not built)

An `ensemble` provider that runs `binoculars` + one LLM judge and blends them
with disagreement-aware confidence (agree → confident; diverge → "uncertain").
That's the configuration where Binoculars adds the most value.
