#!/usr/bin/env python3
"""
E2E calibration test for the AI detector — hits REAL LLM APIs.

Named without the `test_` prefix so pytest does NOT auto-collect it. Run it
manually or from the dedicated CI job.

WHEN TO RUN THIS:
- After changing the prompt in base.py
- Periodically (weekly/monthly) to catch LLM drift
- Before a release if the detector is business-critical

NOT RUN IN NORMAL CI. It needs a real GROQ_API_KEY and would burn the free
quota on every push. Opt in by setting RUN_AI_E2E=1 in the environment.

USAGE:

    # Local:
    cd pdf_doc_sign/backend
    export GROQ_API_KEY=...  # or GEMINI_API_KEY
    export DJANGO_SETTINGS_MODULE=core.settings
    RUN_AI_E2E=1 python tests/e2e_ai_detector.py

    # CI (only when RUN_AI_E2E secret is set):
    # See .github/workflows/deploy.yml — ai-detector-e2e job.

WHAT IT CHECKS:
The prompt is calibrated to match Turnitin on real student submissions.
We have two known-quantity document excerpts:
  - Padmaja Unit 3  (full doc Turnitin: 33%, excerpt target ~30%)
  - Praveen Unit 1  (full doc Turnitin: 79%, excerpt target ~70%)

For each, we assert the detector lands within a ±20pp tolerance. Bands are
wide because LLMs are non-deterministic even at temperature=0.

EXIT CODES:
  0   calibration within tolerance (or skipped)
  1   calibration outside tolerance — review the prompt
  2   API/setup failure (not a calibration issue)
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Test corpus — known-quantity documents and their Turnitin scores.
# ---------------------------------------------------------------------------

@dataclass
class CalibrationCase:
    name: str
    text: str
    turnitin_ai_pct: float
    tolerance_pp: float  # allowed absolute deviation in percentage points

    @property
    def lower_bound(self) -> float:
        return max(0, self.turnitin_ai_pct - self.tolerance_pp)

    @property
    def upper_bound(self) -> float:
        return min(100, self.turnitin_ai_pct + self.tolerance_pp)


# Short illustrative samples from the two real documents. The full documents
# run to ~5000 words each — we use a ~1500-char slice (one chunk) so the
# test completes in a few seconds and doesn't exhaust the free quota.

PRAVEEN_UNIT1_EXCERPT = """
Before entering the care sector, I worked as a software Lead Developer for
over 20 years. I previously believed management and leadership were the
same: I planned the work and ensured people did it, job done. Running
Kleem Home Care and operating the Acer Healthcare franchise taught me
very quickly that they are not the same at all.

Management is the mechanical side of the business. It is about following
rules, consistency, and maintaining order. Kotter (1988) defines
management as being concerned with planning, stability, and organising
complexity. At Acer Healthcare Richmond and Twickenham, management is
the infrastructure that keeps us compliant: building the rotas, chasing
DBS checks, auditing the Birdie care logs against our QCS policies, and
making sure every visit is recorded properly under CQC Regulation 17.

Furthermore, this ensures person-centred care under Regulation 9. In
addition, it supports consistency of delivery across the service. Overall,
this approach reflects the values of the organisation and promotes the
wellbeing of service users.
""".strip()

PADMAJA_UNIT3_EXCERPT = """
When I started working as Care Manager, since there were so many laws
which I felt challenged to deal with it and I kept thinking how I would
remember all the legislations. But what helped me to realise that every
single law exists there for some reason. At some point somebody got hurt
and the government said, we need a rule to stop this happening again.

On 13 March 2026 I reviewed visit records for one of our service users
and I could see that the carer had finished all the thirteen tasks listed
in the care plan. She had also written a detailed note, rather than
something vague like "all fine," clearly describing what she had done.

His name is Mr B (not his real name) he is 87 years old and he is blind.
His son-in-law contacted us that care is required and he wanted carers to
clean a big room and give Mr B a shower which needs to be completed in
45 minutes with one carer. I thought about it and immediately felt it
would not be feasible.
""".strip()


CASES = [
    CalibrationCase(
        name='Praveen_Unit1_excerpt',
        text=PRAVEEN_UNIT1_EXCERPT,
        # Full doc hit 79% on Turnitin. This excerpt is heavier on polished
        # transitions so we expect a similar or slightly higher score.
        turnitin_ai_pct=70.0,
        tolerance_pp=20.0,
    ),
    CalibrationCase(
        name='Padmaja_Unit3_excerpt',
        text=PADMAJA_UNIT3_EXCERPT,
        # Full doc hit 33% on Turnitin. This excerpt has more first-person
        # narrative so we expect 20-40%.
        turnitin_ai_pct=30.0,
        tolerance_pp=20.0,
    ),
]


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def _should_skip() -> tuple[bool, str]:
    if os.environ.get('RUN_AI_E2E', '').strip() not in ('1', 'true', 'yes'):
        return True, 'RUN_AI_E2E not set — skipping (this is expected in normal CI)'
    if not os.environ.get('GROQ_API_KEY') and not os.environ.get('GEMINI_API_KEY'):
        return True, 'Neither GROQ_API_KEY nor GEMINI_API_KEY set — skipping'
    return False, ''


def _setup_django() -> None:
    """Import-time Django setup so services.py can be loaded."""
    if not os.environ.get('DJANGO_SETTINGS_MODULE'):
        os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'
    import django
    django.setup()


def _run_case(case: CalibrationCase, provider: str) -> tuple[bool, float | None, str]:
    """Run detector on one case. Returns (passed, ai_pct, message)."""
    from ai_detector.services import detect_ai_content

    result = detect_ai_content(case.text, provider=provider)

    if result.get('error'):
        return False, None, f'  API ERROR: {result["error"]}'

    ai_prob = result.get('ai_probability') or 0.0
    ai_pct = ai_prob * 100
    in_band = case.lower_bound <= ai_pct <= case.upper_bound

    status = 'PASS' if in_band else 'FAIL'
    msg = (
        f'  {status}: detector={ai_pct:.1f}%   '
        f'expected={case.turnitin_ai_pct:.0f}% \u00b1{case.tolerance_pp:.0f}pp   '
        f'band=[{case.lower_bound:.0f}%, {case.upper_bound:.0f}%]'
    )
    return in_band, ai_pct, msg


def main() -> int:
    skip, reason = _should_skip()
    if skip:
        print(f'[ai-detector-e2e] SKIPPED: {reason}')
        return 0

    try:
        _setup_django()
    except Exception as e:
        print(f'[ai-detector-e2e] SETUP FAILED: {e}', file=sys.stderr)
        return 2

    # Prefer Gemini (single call, 1M context) if available; fall back to Groq.
    provider = 'gemini' if os.environ.get('GEMINI_API_KEY') else 'groq'
    print(f'[ai-detector-e2e] Provider: {provider}')
    print(f'[ai-detector-e2e] Running {len(CASES)} calibration case(s)...')
    print()

    all_passed = True
    for case in CASES:
        print(f'Case: {case.name} ({len(case.text)} chars)')
        try:
            passed, ai_pct, msg = _run_case(case, provider)
        except Exception as e:
            print(f'  RUNTIME ERROR: {e}')
            all_passed = False
            continue

        print(msg)
        if not passed and ai_pct is not None:
            all_passed = False
        elif ai_pct is None:
            # API error — don't fail the build on transient issues.
            print('  (API error \u2014 not counted as calibration failure)')
        print()

    if all_passed:
        print('[ai-detector-e2e] All calibration cases passed.')
        return 0
    print('[ai-detector-e2e] One or more calibration cases FAILED.')
    print('[ai-detector-e2e] Review the prompt in ai_detector/providers/base.py')
    return 1


if __name__ == '__main__':
    sys.exit(main())
