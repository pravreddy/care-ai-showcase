"""
Care AI Engine - Clinical Notes AI Service
Takes a transcript and produces:
  1. A professional clinical summary
  2. Extracted medical actions (e.g., "Give paracetamol at 8pm")
  3. Flagged concerns (e.g., "Client refused medication")
  4. A structured care note ready for CQC documentation

This is what makes your app worth £10/month.
"""

import time
import json
from typing import Optional

from app.core.logging import get_logger
from app.services.llm_service import llm_service, LLMError

logger = get_logger("clinical_notes")

SUMMARY_SYSTEM_PROMPT = """You are a UK clinical documentation assistant for care workers.
You convert voice note transcripts into professional, CQC-compliant care notes.

Your output MUST be valid JSON with this exact structure:
{
  "summary": "A clear 2-4 sentence clinical summary of the care visit/observation",
  "actions": [
    {
      "action": "What needs to be done",
      "priority": "urgent|routine|info",
      "time": "When (if mentioned, otherwise null)",
      "medication": "Medication name (if relevant, otherwise null)"
    }
  ],
  "concerns": [
    "Any safeguarding concerns, refusals, changes in condition, or risks noted"
  ],
  "vitals_mentioned": {
    "blood_pressure": "value if mentioned, otherwise null",
    "temperature": "value if mentioned, otherwise null",
    "pulse": "value if mentioned, otherwise null",
    "blood_sugar": "value if mentioned, otherwise null",
    "oxygen": "value if mentioned, otherwise null",
    "weight": "value if mentioned, otherwise null",
    "pain_level": "value if mentioned, otherwise null"
  },
  "mood_and_behaviour": "Client's mood and behaviour if mentioned, otherwise null",
  "food_and_fluid": "What the client ate/drank if mentioned, otherwise null",
  "mobility": "Mobility observations if mentioned, otherwise null",
  "personal_care": "Personal care provided if mentioned, otherwise null"
}

RULES:
1. Use UK English spelling throughout.
2. Be factual — only include what was actually said in the transcript.
3. Mark actions as "urgent" if they involve: falls, chest pain, breathing difficulty,
   unresponsiveness, severe pain, medication errors, or safeguarding.
4. Mark actions as "routine" for: scheduled medication, GP appointments, care plan updates.
5. Mark actions as "info" for: general observations, mood notes, food intake.
6. If the transcript is unclear or garbled, note this in the summary.
7. Extract ALL medication names and dosages mentioned.
8. ALWAYS output valid JSON. No markdown, no explanation, just the JSON object."""


QUICK_SUMMARY_PROMPT = """You are a UK care documentation assistant.
Summarise this voice note transcript into a brief, professional care note (3-5 sentences).
Use UK English. Be factual. Only include what was actually said.
If medication, actions, or concerns are mentioned, highlight them.
Output ONLY the summary text, nothing else."""


async def generate_clinical_note(
    transcript: str,
    client_name: Optional[str] = None,
    note_type: str = "full",
) -> dict:
    """
    Generate a structured clinical note from a transcript.

    Args:
        transcript: The speech-to-text transcript
        client_name: Optional client name for context
        note_type: "full" for structured JSON, "quick" for text summary only

    Returns:
        Full structured note or quick text summary with metadata
    """
    start = time.monotonic()

    if not transcript or not transcript.strip():
        return {
            "success": False,
            "error": "Empty transcript — nothing to summarise",
        }

    # Build the user prompt
    context = ""
    if client_name:
        context = f"Client name: {client_name}\n"

    if note_type == "quick":
        # Quick summary — just text
        prompt = f"""{context}TRANSCRIPT:
{transcript}

Write a brief professional care note summary:"""

        try:
            result = await llm_service.generate(
                prompt=prompt,
                system_prompt=QUICK_SUMMARY_PROMPT,
                temperature=0.2,
            )

            processing_time_ms = (time.monotonic() - start) * 1000

            return {
                "success": True,
                "note_type": "quick",
                "summary": result["response"].strip(),
                "actions": [],
                "concerns": [],
                "processing_time_ms": round(processing_time_ms, 1),
            }
        except LLMError as e:
            return {"success": False, "error": f"AI processing failed: {str(e)}"}

    # Full structured note
    prompt = f"""{context}TRANSCRIPT:
{transcript}

Extract a structured clinical note as JSON:"""

    try:
        result = await llm_service.generate(
            prompt=prompt,
            system_prompt=SUMMARY_SYSTEM_PROMPT,
            temperature=0.1,  # Very low for structured output
        )

        processing_time_ms = (time.monotonic() - start) * 1000

        # Parse the JSON response
        raw_text = result["response"].strip()

        # Try to extract JSON from the response
        parsed = _parse_json_response(raw_text)

        if parsed:
            # Count urgent actions
            urgent_count = sum(
                1 for a in parsed.get("actions", [])
                if a.get("priority") == "urgent"
            )

            logger.info(
                "Clinical note generated",
                extra={
                    "actions_count": len(parsed.get("actions", [])),
                    "concerns_count": len(parsed.get("concerns", [])),
                    "urgent_count": urgent_count,
                    "processing_time_ms": round(processing_time_ms, 1),
                },
            )

            return {
                "success": True,
                "note_type": "full",
                "summary": parsed.get("summary", ""),
                "actions": parsed.get("actions", []),
                "concerns": parsed.get("concerns", []),
                "vitals_mentioned": parsed.get("vitals_mentioned", {}),
                "mood_and_behaviour": parsed.get("mood_and_behaviour"),
                "food_and_fluid": parsed.get("food_and_fluid"),
                "mobility": parsed.get("mobility"),
                "personal_care": parsed.get("personal_care"),
                "has_urgent_actions": urgent_count > 0,
                "processing_time_ms": round(processing_time_ms, 1),
            }
        else:
            # JSON parsing failed — return the raw text as a quick summary
            logger.warning("Failed to parse structured note, falling back to text")
            return {
                "success": True,
                "note_type": "quick_fallback",
                "summary": raw_text,
                "actions": [],
                "concerns": [],
                "processing_time_ms": round(processing_time_ms, 1),
            }

    except LLMError as e:
        return {"success": False, "error": f"AI processing failed: {str(e)}"}


def _parse_json_response(text: str) -> Optional[dict]:
    """
    Try to extract valid JSON from LLM response.
    LLMs sometimes wrap JSON in markdown code blocks.
    """
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code block
    if "```" in text:
        try:
            start = text.index("{")
            end = text.rindex("}") + 1
            return json.loads(text[start:end])
        except (ValueError, json.JSONDecodeError):
            pass

    # Try finding JSON object in the text
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end])
    except (ValueError, json.JSONDecodeError):
        pass

    return None


async def generate_handover_note(notes: list[dict]) -> dict:
    """
    Generate a shift handover summary from multiple care notes.
    Takes a list of clinical notes and produces a handover document.

    Used at end of shift to brief the next carer.
    """
    if not notes:
        return {"success": False, "error": "No notes provided"}

    notes_text = "\n\n".join(
        f"--- Note {i+1} (at {n.get('created_at', 'unknown time')}) ---\n"
        f"Summary: {n.get('summary', 'No summary')}\n"
        f"Actions: {json.dumps(n.get('actions', []))}\n"
        f"Concerns: {json.dumps(n.get('concerns', []))}"
        for i, n in enumerate(notes)
    )

    prompt = f"""Here are the care notes from today's shift:

{notes_text}

Write a professional shift handover note that:
1. Summarises key events and observations
2. Lists outstanding actions for the next carer
3. Highlights any urgent concerns
4. Notes any medication given or refused
5. Is concise (under 200 words)

Format as a clear handover note:"""

    try:
        result = await llm_service.generate(
            prompt=prompt,
            system_prompt="You are a UK care shift handover assistant. Write clear, professional handover notes in UK English.",
            temperature=0.2,
        )

        return {
            "success": True,
            "handover_note": result["response"].strip(),
            "notes_summarised": len(notes),
        }
    except LLMError as e:
        return {"success": False, "error": str(e)}
