"""
Shared utilities for all AI detector providers.
Contains: text chunking, prompt building, response parsing, chunked detection orchestration.
"""
import logging
import json as json_lib
import re
import time

logger = logging.getLogger(__name__)

# ─── Chunking parameters ──────────────────────────────────────────────────────
CHUNK_SIZE = 3000          # chars per chunk (~500 words)
MAX_CHUNKS = 15
MAX_TOTAL_CHARS = 50000
MIN_CHARS = 50


# ─── Text Chunking ────────────────────────────────────────────────────────────

def split_into_chunks(text: str) -> list:
    """Split text into sentence-respecting chunks of ~CHUNK_SIZE chars."""
    text = text[:MAX_TOTAL_CHARS].strip()
    if len(text) <= CHUNK_SIZE:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + CHUNK_SIZE
        if end >= len(text):
            chunks.append(text[start:].strip())
            break

        search_region = text[start + CHUNK_SIZE - 200: start + CHUNK_SIZE + 100]
        best_break = -1
        for m in re.finditer(r'[.!?]\s', search_region):
            best_break = m.end()

        if best_break > 0:
            actual_end = start + CHUNK_SIZE - 200 + best_break
        else:
            space_pos = text.rfind(' ', start + CHUNK_SIZE - 100, start + CHUNK_SIZE + 50)
            actual_end = space_pos if space_pos > start else start + CHUNK_SIZE

        chunk = text[start:actual_end].strip()
        if chunk:
            chunks.append(chunk)
        start = actual_end

    return chunks[:MAX_CHUNKS]


# ─── Prompts ──────────────────────────────────────────────────────────────────

def system_prompt() -> str:
    return (
        'You are an expert AI content detector calibrated against Turnitin-class '
        'detectors used by educational institutions (HABC, City & Guilds, university '
        'assessors). '
        'You analyse text across THREE independent dimensions: '
        '(A) prose-structure patterns typical of AI or AI-paraphrased writing, '
        '(B) content-specificity signals typical of lived human experience, and '
        '(C) HARD HUMAN SIGNALS — STRICTLY MECHANICAL: typos, non-native English '
        'grammar breaks, unconventional formatting, pre-2022 personal correspondence. '
        'Emotional content and polished personal anecdotes are Dimension B, NOT C. '
        'When A and B both score high, label as AI-paraphrased at 0.55-0.75 — '
        'this is the common case for student work run through ChatGPT. '
        'Apply the Dimension C cap (0.25) ONLY when multiple mechanical signals '
        'appear consistently. A polished document with personal anecdotes is NOT C. '
        'Always respond with valid JSON only — no markdown fences, no extra text.'
    )


def build_chunk_prompt(text: str, chunk_index: int = 1, total_chunks: int = 1) -> str:
    """Prompt for a single chunk of text."""
    chunk_note = ''
    if total_chunks > 1:
        chunk_note = (
            f'\nNote: This is section {chunk_index} of {total_chunks} from a '
            f'longer document. Analyse only this section.\n'
        )

    return f"""Analyse the following text section for AI-generated content.
{chunk_note}
TEXT TO ANALYSE:
---
{text}
---

Respond with ONLY this JSON (no markdown, no explanation outside JSON):
{{
  "ai_probability": <float 0.0-1.0, overall for this section>,
  "human_probability": <float 0.0-1.0>,
  "explanation": "<2-3 sentences: what specific signals led to your assessment>",
  "sentences": [
    {{"text": "<exact sentence from text>", "ai_probability": <float 0.0-1.0>, "label": "<AI|Human|Mixed>"}}
  ]
}}

{detection_rules()}"""


def build_full_doc_prompt(text: str) -> str:
    """Prompt for full-document analysis (used by Gemini 1M context)."""
    return f"""Analyse the following COMPLETE document for AI-generated content.

TEXT TO ANALYSE:
---
{text}
---

Respond with ONLY this JSON (no markdown, no explanation outside JSON):
{{
  "ai_probability": <float 0.0-1.0, overall for entire document>,
  "human_probability": <float 0.0-1.0>,
  "explanation": "<3-4 sentences: specific signals found and overall assessment>",
  "sentences": [
    {{"text": "<exact sentence from text>", "ai_probability": <float 0.0-1.0>, "label": "<AI|Human|Mixed>"}}
  ]
}}

{detection_rules()}
- This is a COMPLETE document, not a fragment"""


def build_full_doc_prompt_v2(text: str) -> str:
    """V2 prompt: asks LLM for raw dimension scores. Python applies classification.

    Key insight: LLMs are bad at math but good at pattern recognition.
    Ask the LLM to SCORE each dimension, then let Python apply the matrix.
    """
    return f"""Analyse the following COMPLETE document for AI-generated content.

TEXT TO ANALYSE:
---
{text}
---

You MUST score THREE dimensions independently. Do NOT compute a final
ai_probability yourself — just report the raw dimension scores honestly.

Respond with ONLY this JSON (no markdown, no extra text):
{{
  "dimensions": {{
    "prose_structure_A": <float 0.0-1.0>,
    "content_specificity_B": <float 0.0-1.0>,
    "mechanical_signals_C": <float 0.0-1.0>
  }},
  "explanation": "<2-3 sentences: what specific signals you found for each dimension>",
  "c_signals_found": ["<list each specific mechanical signal found, e.g. 'typo: beliver', 'ESL grammar: dropped article in para 3', 'ASCII divider ======'>"],
  "sentences": [
    {{"text": "<exact sentence>", "ai_probability": <float 0.0-1.0>, "label": "<AI|Human|Mixed>"}}
  ]
}}

{detection_rules_v2()}
- This is a COMPLETE document, not a fragment
- Report dimension scores HONESTLY — the final classification is computed externally"""


def detection_rules() -> str:
    """Shared detection rules used in both chunk and full-doc prompts.

    Calibrated against Turnitin: prose-structure patterns are judged
    independently of content-specificity so AI-paraphrased human drafts
    are flagged rather than being excused by personal references.
    """
    return """DETECTION RULES (follow strictly):

Score each sentence on THREE INDEPENDENT dimensions.

DIMENSION A — PROSE-STRUCTURE AI PATTERNS
A sentence scores HIGH on A if it exhibits any of these, regardless of
what it is talking about:
- Balanced, symmetrical clause construction (two or three clauses of
  near-equal length joined by conjunctions or commas)
- Uniform sentence length across 3+ consecutive sentences
- Polished transitional phrases: "Furthermore", "In addition", "Overall",
  "Moreover", "When we look at these frameworks together", "This shows
  that...", "It is important to note that...", "In my opinion, this..."
- Generic abstract closers: "this ensures...", "this helps us to...",
  "this supports...", "this reflects...", "this promotes..."
- Parallel list structure embedded in prose ("Regulation 9 is about X.
  Regulation 12 covers Y. Regulation 13 is Z.")
- Rhythmic tri-colon construction ("safe, effective, and person-centred")
- Abstract formal phrasing that would read identically for any
  organisation ("emphasises the importance of working in partnership
  with...", "sets out detailed expectations with respect to...")
- Hedged academic framing: "it could be argued that", "this may indicate"
- Encyclopaedic paraphrase of regulatory/legislative content
- Textbook-style definitions with no personal interpretation

DIMENSION B — CONTENT-SPECIFICITY HUMAN SIGNALS
A sentence scores HIGH on B if it contains any of these:
- Named individuals (even anonymised: "Mr B", "Mrs K", "our RM")
- Specific verifiable dates ("13 March 2026", "15 January 2025")
- Concrete numbers tied to a specific event ("230ml of tea", "45 minutes")
- Named internal systems/policies/documents ("Birdie", "CR100", "QQ24")
- Idiosyncratic phrasing, self-corrections, genuine digressions
- Emotional specificity tied to a concrete event (not generic sentiment)
- Real-world messiness or things that did not go to plan
- Typos, grammatical slips, informal conversational asides

DIMENSION C — HARD HUMAN SIGNALS (override floor, strict mechanical only)
A sentence scores HIGH on C ONLY if it contains MECHANICAL signals that
modern LLMs do not emit. Polished personal narrative is NOT Dimension C.
Emotional content is NOT Dimension C. Named people and real dates are
NOT Dimension C — those are Dimension B.

Dimension C signals (must be MECHANICAL, not just personal):
- Genuine spelling errors an LLM would not produce ("beliver",
  "apperiance", "vegitrain", "recieve", "seperately", "definately")
- Non-native English grammar that breaks standard rules ("I won't get
  happiness when going to restaurant", "he does not give the freedom",
  dropped articles in unusual places, wrong preposition choices,
  subject-verb disagreement, tense errors in a consistent pattern)
- Mid-sentence self-corrections with visible restart ("I thought — or
  rather I assumed — that...", "She said, I mean, she told me...")
- Unconventional punctuation that a polishing pass would remove
  (ASCII dividers like "======" or "-----", numbered lists with
  "1.)" style, double spaces, run-on sentences without commas,
  excessive ellipsis "...")
- Explicit pre-2022 timestamps on personal correspondence (old emails,
  diary entries, letters) where the writer refers to their own past
  life events — modern LLMs did not exist before late 2022

WHAT IS NOT DIMENSION C (common confusions):
- A well-written personal story with named people and real dates →
  that's Dimension B content. A polished anecdote is still polished.
- Emotional language ("I was consumed by CQC registration",
  "I felt under pressure") → that's Dimension B, not C.
  AI writes about emotions all the time.
- First-person voice alone → AI writes in first person routinely.
- Specific internal references ("Birdie", "Regulation 17", "our RM") →
  that's Dimension B. LLMs happily invent or paraphrase these.

CLASSIFICATION RULE (CRITICAL — do not deviate):

Step 1: Compute document-level C score — STRICT threshold.
  - C ≥ 0.7 requires AT LEAST TWO distinct MECHANICAL signal types
    from the Dimension C list appearing multiple times across the doc.
    One typo is not enough. One ASCII divider is not enough.
  - If C ≥ 0.7:
      ai_probability is CAPPED AT 0.25. Label "Human" or "Mixed".
      This is the pre-LLM-era / ESL-writer floor. Use it sparingly.
  - If C is 0.4-0.7 (some mechanical signals but not overwhelming):
      Do NOT cap. Apply the A/B matrix normally. Mechanical signals
      may lower the score by a few points but do not override Dim A.

Step 2: Apply the A/B matrix:
  - A ≥ 0.6 AND B ≥ 0.6  →  label "AI" (AI-paraphrased human draft),
                            ai_probability 0.55 - 0.75.
                            THIS IS THE CRITICAL CASE for academic work.
                            Polished prose with named people, real dates,
                            and personal anecdotes IS STILL AI-paraphrased.
                            Do NOT let B (personal content) rescue A.
                            TutorCare/Turnitin score these 60-80%.
  - A ≥ 0.7 AND B < 0.4  →  label "AI", ai_probability 0.75 - 0.90
  - A < 0.4 AND B ≥ 0.6  →  label "Human", ai_probability < 0.20
  - A < 0.4 AND B < 0.4  →  label "Mixed", ai_probability 0.35 - 0.55
  - Otherwise             →  label "Mixed", ai_probability 0.40 - 0.60

CALIBRATION ANCHORS (aim to match these):

Anchor 1 — Padmaja-style (formal regulatory coursework, ESL author,
  first-person anecdotes, real dates, named people, some parallel
  regulatory lists): TARGET 20-40% AI. Turnitin gave this 33%.
  DO NOT score this above 50%.

Anchor 2 — AI-paraphrased academic work (uniform polished prose,
  "Furthermore / In addition / Overall" transitions every 2-3 sentences,
  balanced tri-colon constructions, textbook-style definitions with
  light personal framing sprinkled in): TARGET 65-85% AI.
  Turnitin gave this 79%.

Anchor 3 — ESL personal writing / pre-LLM-era email (short choppy
  sentences, typos, emotional register, ASCII dividers, numbered lists,
  some parallel emphasis from list structure): TARGET 0-15% AI.
  A pre-2022 email CANNOT be AI regardless of structural features.
  DO NOT score this above 20%.

BOUNDARY PRINCIPLES:
- Formal/regulatory topic alone is NOT AI evidence.
- Parallel structure from list formatting or emphatic repetition is NOT
  AI evidence by itself. AI tells need uniform sentence length AND
  polished transitions AND generic closers TOGETHER.
- KEY ANTI-PATTERN: Polished first-person narrative with "Furthermore /
  In addition / Overall" transitions, balanced clause construction,
  and textbook-style framing is AI-PARAPHRASED, not human — even when
  it contains named people, real dates, specific company names, and
  emotional reflection. A student who asks ChatGPT to "rewrite my draft
  in professional academic style" produces exactly this output. Score
  60-80% AI on documents matching this pattern.
- Dimension C (mechanical signals) is a HIGH BAR. Require multiple
  distinct signal types before applying the 0.25 cap. A polished
  document with one or two personal touches does NOT qualify.
- When uncertain between "AI" (0.60) and "Mixed" (0.50), lean toward
  the higher score IF Dimension A is strong. Under-flagging AI-paraphrased
  academic work harms assessment integrity just as much as over-flagging
  human work harms individual students.

OUTPUT RULES:
- Include EVERY sentence from the input text in the sentences array.
- ai_probability for the whole chunk = the weighted average of sentence
  scores (longer sentences weigh more), then apply the Dimension C cap
  at document level.
- In the explanation, cite at least ONE specific pattern observed. If
  flagging as AI, cite a Dimension A pattern (e.g. "balanced tri-colon
  in para 3", "Furthermore/In addition every 2-3 sentences"). If scoring
  low, cite a Dimension C signal (e.g. "ESL grammar in sentence 2",
  "typo 'beliver' indicates human draft", "pre-2022 personal email").
- Dimension C signals ARE valid reasons to lower the score. Humans who
  write formally can still be humans — typos, ESL grammar, and emotional
  specificity are reliable human markers that should pull scores down.
"""


# ─── V2: Dimension-Report Rules + Python Classification ──────────────────────

def detection_rules_v2() -> str:
    """Slimmer rules for V2 dimension-report prompt.

    The LLM only needs to SCORE dimensions, not apply classification.
    Classification logic lives in apply_classification_rules().
    """
    return """SCORING RULES (follow strictly):

Score the ENTIRE DOCUMENT on three independent dimensions.

DIMENSION A — PROSE-STRUCTURE AI PATTERNS (0.0 = no AI patterns, 1.0 = heavily AI)
High A signals:
- Balanced, symmetrical clause construction throughout
- Uniform sentence length across 3+ consecutive sentences
- Polished transitions: "Furthermore", "In addition", "Overall", "Moreover"
- Generic abstract closers: "this ensures...", "this supports..."
- Parallel list structure in prose ("Regulation 9 is... Regulation 12 covers...")
- Rhythmic tri-colon construction ("safe, effective, and person-centred")
- Textbook-style definitions with no personal interpretation
- Encyclopaedic paraphrase of regulatory content
Low A signals:
- Variable sentence lengths, mix of short and long
- Informal transitions or no transitions at all
- Sentences that start with "But", "And", "So" informally
- Run-on sentences, fragments, or missing connectors

DIMENSION B — CONTENT-SPECIFICITY HUMAN SIGNALS (0.0 = generic, 1.0 = deeply specific)
High B signals:
- Named individuals ("Mr B", "Mrs K", "our Care Manager")
- Specific dates tied to events ("13 March 2026", "15 January 2025")
- Concrete numbers ("230ml of tea", "45 minutes", "87 years old")
- Named systems/policies ("Birdie", "CR100", "QCS")
- Personal anecdotes with real-world messiness
- Emotional reflection on specific events
IMPORTANT: B can be HIGH even in AI-paraphrased documents. A student who
feeds their real notes into ChatGPT produces text that is high-A AND high-B.
High B does NOT mean human.

DIMENSION C — MECHANICAL HUMAN SIGNALS (0.0 = no mechanical signals, 1.0 = many)
C is STRICTLY about mechanical artefacts that LLMs cannot produce:
- Genuine spelling errors ("beliver", "apperiance", "vegitrain")
- Non-native English grammar breaks (dropped articles, wrong prepositions,
  "I won't get happiness when going to restaurant")
- Mid-sentence self-corrections or visible restarts
- Unconventional formatting (ASCII dividers ======, "1.)" numbering)
- Pre-2022 timestamps on personal correspondence

WHAT IS NOT C:
- Polished personal stories → Dimension B
- Emotional language → Dimension B
- First-person voice → not evidence of anything (AI does this too)
- Named references to real systems → Dimension B

FOR c_signals_found: List EVERY specific mechanical signal you find.
If you find none, return an empty list []. Be honest.

SCORING THE SENTENCES:
- Score each sentence's ai_probability independently based on its own
  prose structure (Dimension A patterns at sentence level).
- Label: "AI" if sentence-level A > 0.6, "Human" if < 0.3, "Mixed" otherwise.
- Include EVERY sentence from the input text.
"""


def apply_classification_rules(dim_a: float, dim_b: float, dim_c: float,
                               c_signals: list = None) -> dict:
    """Apply classification matrix in Python. Deterministic and debuggable.

    Args:
        dim_a: Prose-structure AI patterns (0.0-1.0)
        dim_b: Content-specificity human signals (0.0-1.0)
        dim_c: Mechanical human signals (0.0-1.0)
        c_signals: List of specific mechanical signals found

    Returns:
        dict with ai_probability, verdict, classification_reason
    """
    c_signals = c_signals or []
    num_c_signals = len(c_signals)

    # Step 1: Dimension C override (strict mechanical floor)
    # Requires C >= 0.7 AND at least 2 distinct signal types found
    if dim_c >= 0.7 and num_c_signals >= 2:
        ai_prob = min(0.15, dim_a * 0.2)  # Heavy cap, almost certainly human
        reason = (f'Dimension C override: {num_c_signals} mechanical human signals '
                  f'found ({", ".join(c_signals[:3])}). Document is likely human-written '
                  f'regardless of prose structure (A={dim_a:.2f}).')
        return {
            'ai_probability': round(ai_prob, 4),
            'verdict': 'LIKELY_HUMAN',
            'classification_reason': reason,
            'dimensions': {'A': dim_a, 'B': dim_b, 'C': dim_c},
        }

    # Step 2: A/B classification matrix
    if dim_a >= 0.6 and dim_b >= 0.6:
        # AI-paraphrased human draft — the common case for student work
        # Scale within 0.55-0.75 based on how strong A is
        ai_prob = 0.55 + (dim_a - 0.6) * 0.5  # A=0.6→0.55, A=0.8→0.65, A=1.0→0.75
        ai_prob = max(0.55, min(0.75, ai_prob))
        # Small C adjustment: if some mechanical signals, reduce slightly
        if dim_c >= 0.3 and num_c_signals >= 1:
            ai_prob -= 0.05
        reason = (f'A={dim_a:.2f} (polished prose) + B={dim_b:.2f} (specific content) '
                  f'→ AI-paraphrased human draft. TutorCare/Turnitin score this 60-80%.')
        verdict = 'LIKELY_AI' if ai_prob >= 0.70 else 'POSSIBLY_AI'
        return {
            'ai_probability': round(ai_prob, 4),
            'verdict': verdict,
            'classification_reason': reason,
            'dimensions': {'A': dim_a, 'B': dim_b, 'C': dim_c},
        }

    if dim_a >= 0.7 and dim_b < 0.4:
        # Pure AI — polished prose with no real content
        ai_prob = 0.75 + (dim_a - 0.7) * 0.5  # A=0.7→0.75, A=1.0→0.90
        ai_prob = max(0.75, min(0.90, ai_prob))
        reason = (f'A={dim_a:.2f} (strong AI patterns) + B={dim_b:.2f} (generic content) '
                  f'→ likely AI-generated text.')
        return {
            'ai_probability': round(ai_prob, 4),
            'verdict': 'LIKELY_AI',
            'classification_reason': reason,
            'dimensions': {'A': dim_a, 'B': dim_b, 'C': dim_c},
        }

    if dim_a < 0.4 and dim_b >= 0.6:
        # Human writing with specific content
        ai_prob = dim_a * 0.4  # A=0.0→0.0, A=0.3→0.12, A=0.39→0.16
        # C signals make it even more human
        if dim_c >= 0.3:
            ai_prob *= 0.5
        reason = (f'A={dim_a:.2f} (low AI patterns) + B={dim_b:.2f} (specific content) '
                  f'→ likely human-written.')
        return {
            'ai_probability': round(max(0, ai_prob), 4),
            'verdict': 'LIKELY_HUMAN',
            'classification_reason': reason,
            'dimensions': {'A': dim_a, 'B': dim_b, 'C': dim_c},
        }

    if dim_a < 0.4 and dim_b < 0.4:
        # Low on both — generic but not obviously AI
        ai_prob = 0.35 + dim_a * 0.5  # maps 0.0-0.4 → 0.35-0.55
        reason = (f'A={dim_a:.2f} + B={dim_b:.2f} → Mixed signals, insufficient '
                  f'evidence for confident classification.')
        return {
            'ai_probability': round(ai_prob, 4),
            'verdict': 'POSSIBLY_AI',
            'classification_reason': reason,
            'dimensions': {'A': dim_a, 'B': dim_b, 'C': dim_c},
        }

    # Catch-all: moderate signals on both dimensions
    ai_prob = 0.40 + dim_a * 0.3  # maps toward middle
    if dim_c >= 0.3 and num_c_signals >= 1:
        ai_prob -= 0.05
    reason = (f'A={dim_a:.2f} + B={dim_b:.2f} + C={dim_c:.2f} '
              f'→ Mixed signals, borderline classification.')
    return {
        'ai_probability': round(max(0, min(1, ai_prob)), 4),
        'verdict': 'POSSIBLY_AI',
        'classification_reason': reason,
        'dimensions': {'A': dim_a, 'B': dim_b, 'C': dim_c},
    }


# ─── Response Parsing ─────────────────────────────────────────────────────────

def parse_openai_response(raw: dict, provider: str) -> dict:
    """Parse OpenAI-compatible response (Groq, SiliconFlow, Grok, OpenAI, etc.)."""
    try:
        content = raw['choices'][0]['message']['content'].strip()
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
            'provider': provider,
            'raw': raw,
            'error': None,
        }
    except (KeyError, ValueError, IndexError, json_lib.JSONDecodeError) as e:
        logger.error(f'{provider} parse error: {e} | content: {raw}')
        return error_result(f'Unexpected {provider} response: {str(e)}', provider)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def verdict_from_pct(ai_pct: float) -> str:
    if ai_pct >= 70:
        return 'LIKELY_AI'
    elif ai_pct >= 40:
        return 'POSSIBLY_AI'
    return 'LIKELY_HUMAN'


def insufficient_text_result(provider: str) -> dict:
    return {
        'ai_probability': None, 'human_probability': None,
        'verdict': 'INSUFFICIENT_TEXT', 'explanation': None,
        'sentences': [], 'provider': provider, 'raw': [],
        'error': 'Not enough text (minimum 50 characters).',
    }


def error_result(message: str, provider: str) -> dict:
    return {
        'ai_probability': None, 'human_probability': None,
        'verdict': 'ERROR', 'explanation': None,
        'sentences': [], 'provider': provider, 'raw': [],
        'error': message,
    }


# ─── Chunked Detection Orchestration ──────────────────────────────────────────

def detect_chunked(chunks: list, full_text: str, api_call_fn, provider: str) -> dict:
    """
    Analyse each chunk separately, then aggregate results.
    Handles rate limits based on provider type.
    """
    all_sentences = []
    chunk_scores = []
    chunk_errors = []
    explanations = []

    for i, chunk in enumerate(chunks):
        logger.info(f'  Chunk {i+1}/{len(chunks)}: {len(chunk)} chars')

        # Deep scan (70B) needs delays — runs in Celery so sleep is fine
        if i > 0 and provider == 'groq_deep':
            wait = 65
            logger.info(f'  Deep scan pause: {wait}s (70B model)')
            time.sleep(wait)

        result = None
        for attempt in range(3):
            result = api_call_fn(chunk, chunk_index=i + 1, total_chunks=len(chunks))
            error_msg = result.get('error', '')
            if '429' in str(error_msg) or 'rate' in str(error_msg).lower():
                if provider == 'groq_deep':
                    wait = 20 * (attempt + 1)
                    logger.warning(f'  Rate limited on chunk {i+1}, waiting {wait}s')
                    time.sleep(wait)
                    continue
                else:
                    logger.warning(f'  Rate limited on chunk {i+1}, skipping')
                    chunk_errors.append(error_msg)
                    result = None
                    break
            break

        try:
            if result is None:
                continue
            if result.get('error'):
                chunk_errors.append(result['error'])
                continue

            ai_prob = result.get('ai_probability', 0) or 0
            chunk_scores.append({'ai_probability': ai_prob, 'char_count': len(chunk)})

            chunk_sentences = result.get('sentences', [])
            if chunk_sentences:
                all_sentences.extend(chunk_sentences)
            if result.get('explanation'):
                explanations.append(result['explanation'])

        except Exception as e:
            logger.error(f'Chunk {i+1} failed: {e}')
            chunk_errors.append(str(e))

    if not chunk_scores:
        error_msg = '; '.join(chunk_errors[:3]) if chunk_errors else 'All chunks failed'
        return error_result(error_msg, provider)

    total_chars = sum(c['char_count'] for c in chunk_scores)
    weighted_ai = sum(
        c['ai_probability'] * c['char_count'] / total_chars
        for c in chunk_scores
    )

    ai_pct = round(weighted_ai * 100)
    ai_sentence_count = sum(1 for s in all_sentences if s.get('label') == 'AI')
    total_sentence_count = len(all_sentences)

    return {
        'ai_probability': round(weighted_ai, 4),
        'human_probability': round(1 - weighted_ai, 4),
        'mixed_probability': 0.0,
        'verdict': verdict_from_pct(ai_pct),
        'explanation': build_summary_explanation(
            ai_pct, ai_sentence_count, total_sentence_count, len(chunks), explanations
        ),
        'sentences': all_sentences,
        'provider': provider,
        'chunks_analysed': len(chunk_scores),
        'chunks_total': len(chunks),
        'chunks_failed': len(chunk_errors),
        'ai_sentence_count': ai_sentence_count,
        'total_sentence_count': total_sentence_count,
        'raw': {'chunk_scores': chunk_scores},
        'error': None,
    }


def detect_chunked_resumable(chunks, full_text, api_call_fn, provider,
                              skip_chunks=0, existing_sentences=None,
                              progress_callback=None):
    """
    Like detect_chunked but resumes from skip_chunks.
    Saves progress via callback. On 429, raises exception (Celery retries).
    """
    all_sentences = list(existing_sentences or [])
    chunk_scores = []
    chunk_errors = []
    explanations = []

    for i in range(skip_chunks):
        chunk_scores.append({
            'ai_probability': 0,
            'char_count': len(chunks[i]) if i < len(chunks) else 0,
        })

    for i in range(skip_chunks, len(chunks)):
        chunk = chunks[i]
        logger.info(f'  Chunk {i+1}/{len(chunks)}: {len(chunk)} chars (resumable)')

        if i > 0 and provider == 'groq_deep':
            logger.info(f'  Deep scan pause: 65s (70B model)')
            time.sleep(65)

        result = api_call_fn(chunk, chunk_index=i + 1, total_chunks=len(chunks))
        error_msg = result.get('error', '')

        if '429' in str(error_msg) or 'rate' in str(error_msg).lower():
            logger.warning(f'  Rate limited on chunk {i+1} — saving progress and raising for retry')
            if progress_callback:
                progress_callback(build_partial_result(
                    all_sentences, chunk_scores, chunks, explanations, provider, i
                ))
            raise Exception(f'Rate limited at chunk {i+1}/{len(chunks)}')

        if result.get('error'):
            chunk_errors.append(result['error'])
            continue

        ai_prob = result.get('ai_probability', 0) or 0
        chunk_scores.append({'ai_probability': ai_prob, 'char_count': len(chunk)})

        chunk_sentences = result.get('sentences', [])
        if chunk_sentences:
            all_sentences.extend(chunk_sentences)
        if result.get('explanation'):
            explanations.append(result['explanation'])

        if progress_callback:
            progress_callback(build_partial_result(
                all_sentences, chunk_scores, chunks, explanations, provider, i + 1
            ))

    if not chunk_scores:
        error_msg = '; '.join(chunk_errors[:3]) if chunk_errors else 'All chunks failed'
        return error_result(error_msg, provider)

    total_chars = sum(c['char_count'] for c in chunk_scores if c['char_count'] > 0)
    if total_chars == 0:
        return error_result('No text analysed', provider)

    weighted_ai = sum(
        c['ai_probability'] * c['char_count'] / total_chars
        for c in chunk_scores if c['char_count'] > 0
    )

    ai_pct = round(weighted_ai * 100)
    ai_sentence_count = sum(1 for s in all_sentences if s.get('label') == 'AI')
    total_sentence_count = len(all_sentences)

    return {
        'ai_probability': round(weighted_ai, 4),
        'human_probability': round(1 - weighted_ai, 4),
        'mixed_probability': 0.0,
        'verdict': verdict_from_pct(ai_pct),
        'explanation': build_summary_explanation(
            ai_pct, ai_sentence_count, total_sentence_count, len(chunks), explanations
        ),
        'sentences': all_sentences,
        'provider': provider,
        'chunks_analysed': len([c for c in chunk_scores if c['char_count'] > 0]),
        'chunks_total': len(chunks),
        'chunks_failed': len(chunk_errors),
        'ai_sentence_count': ai_sentence_count,
        'total_sentence_count': total_sentence_count,
        'raw': {'chunk_scores': chunk_scores},
        'error': None,
    }


def build_summary_explanation(ai_pct, ai_sentences, total_sentences, num_chunks, explanations):
    """Build a Turnitin-style summary explanation."""
    parts = []
    parts.append(
        f'{ai_pct}% of the qualifying text was detected as likely AI-generated. '
        f'{ai_sentences} of {total_sentences} sentences were flagged across '
        f'{num_chunks} analysed section{"s" if num_chunks > 1 else ""}.'
    )

    if ai_pct >= 70:
        parts.append(
            'The text shows strong indicators of AI generation including '
            'uniform sentence structure, generic transitional phrases, and '
            'lack of personal voice or specific experiential detail.'
        )
    elif ai_pct >= 40:
        parts.append(
            'The text shows mixed signals. Some sections appear AI-generated '
            'while others contain personal voice and specific examples. '
            'Consider adding more personal experiences and specific details '
            'to the flagged sections.'
        )
    elif ai_pct >= 20:
        parts.append(
            'Most of the text appears human-written. A few sentences show '
            'patterns common in AI-generated text but this could be due to '
            'formal writing style. Scores under 20% have higher false positive rates.'
        )
    else:
        parts.append(
            'The text appears to be human-written with strong personal voice, '
            'specific examples, and natural language variation.'
        )

    if explanations:
        unique_points = []
        seen = set()
        for exp in explanations:
            first_sent = exp.split('.')[0].strip()
            key = first_sent[:50].lower()
            if key not in seen and len(unique_points) < 3:
                seen.add(key)
                unique_points.append(first_sent + '.')
        if unique_points:
            parts.append('Key observations: ' + ' '.join(unique_points))

    return ' '.join(parts)


def build_partial_result(sentences, chunk_scores, chunks, explanations, provider, chunks_done):
    """Build partial result dict for progress saving."""
    valid_scores = [c for c in chunk_scores if c['char_count'] > 0]
    total_chars = sum(c['char_count'] for c in valid_scores) or 1
    weighted_ai = sum(c['ai_probability'] * c['char_count'] / total_chars for c in valid_scores)
    ai_sentence_count = sum(1 for s in sentences if s.get('label') == 'AI')
    return {
        'sentences': sentences,
        'chunks_analysed': chunks_done,
        'chunks_total': len(chunks),
        'ai_sentence_count': ai_sentence_count,
        'total_sentence_count': len(sentences),
        'ai_probability': round(weighted_ai, 4),
        'human_probability': round(1 - weighted_ai, 4),
    }
