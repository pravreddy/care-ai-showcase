"""
Chatbot AI Service — Groq-powered conversations for lead capture.

Uses the SAME Groq API key as ai_detector:
  - AI Detector:  llama-3.3-70b-versatile (accurate, 6K tokens/min)
  - Chatbot:      llama-3.1-8b-instant    (fast, 131K tokens/min — no rate limits)

The AI's job:
  1. Greet visitors warmly, answer questions about SignSimple
  2. Naturally collect: first name, last name
  3. Offer to send info by email (collects email without being pushy)
  4. Decide the right offer based on conversation context
  5. Extract structured data from the conversation
"""
import json
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

GROQ_API_KEY = getattr(settings, 'GROQ_API_KEY', '')
GROQ_CHATBOT_MODEL = getattr(settings, 'GROQ_CHATBOT_MODEL', 'llama-3.1-8b-instant')
GROQ_API_URL = 'https://api.groq.com/openai/v1/chat/completions'

SYSTEM_PROMPT = """You are SignSimple's friendly AI assistant on signsimple.co.uk.

SignSimple is a UK-based PDF document signing platform by Avyangah Technologies Limited.
Features: legally binding e-signatures, document templates, team management, sales & invoicing, AI content detection.
Plans: Free (10 docs/mo), Starter £2.50/mo (100 docs), Professional £10/mo (1000 docs).

YOUR GOAL: Have a natural, helpful conversation. When appropriate, collect the visitor's name and email so you can send them a special offer.

RULES:
- Be warm, professional, and conversational — NOT robotic
- Answer product questions honestly and helpfully
- After 2-3 exchanges, naturally ask for their name (e.g. "By the way, I didn't catch your name!")
- Once you have their name, offer to send them details by email
- NEVER ask for phone number
- NEVER be pushy — if they don't want to share info, respect that and keep helping
- When you have both name and email, mention the special £1 offer for 6 months
- Keep responses SHORT (2-3 sentences max) — this is a chat, not an essay

SPECIAL OFFER (mention when you have their email):
"We have a special offer right now — you can try the full Starter plan for just £1 for 6 months.
That includes 100 document signatures and 100 AI content scans per month.
I'll send your personal discount code to your email — it's valid for 7 days."

DETECTING CONTEXT (use this to decide the offer tier):
- Individual just browsing → 3 months free trial
- Small business with specific use case → 6 months (main offer)
- Company mentioning team/staff → 12 months + team seats
- Already using a competitor → 6 months + migration help"""

EXTRACTION_PROMPT = """Extract any personal information shared by the visitor in this conversation.
Return ONLY valid JSON, no other text:
{
  "first_name": "",
  "last_name": "",
  "email": "",
  "company": "",
  "use_case": "",
  "visitor_type": "individual|small_business|company|competitor_user",
  "ready_for_offer": true/false,
  "suggested_plan": "STARTER|PROFESSIONAL",
  "suggested_duration_days": 90|180|365,
  "conversation_summary": "1-2 sentence summary of what they want"
}

Only fill in fields that were explicitly mentioned. Leave empty string if not mentioned.
Set ready_for_offer to true only if you have both name AND email."""


def chat_reply(messages: list, session_context: dict = None) -> dict:
    """
    Send conversation to Groq and get AI reply.

    Args:
        messages: list of {"role": "user"|"assistant", "content": "..."}
        session_context: optional dict with extracted info so far

    Returns:
        {"reply": "AI response text", "error": None} or {"reply": None, "error": "..."}
    """
    if not GROQ_API_KEY:
        return {
            'reply': "I'm having a quick technical issue. Please try again in a moment!",
            'error': 'GROQ_API_KEY not configured',
        }

    # Build the full message list with system prompt
    full_messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]

    # Add context about what we already know
    if session_context:
        context_parts = []
        if session_context.get('first_name'):
            context_parts.append(f"Visitor's name: {session_context['first_name']} {session_context.get('last_name', '')}")
        if session_context.get('email'):
            context_parts.append(f"Visitor's email: {session_context['email']}")
        if session_context.get('company'):
            context_parts.append(f"Company: {session_context['company']}")
        if context_parts:
            full_messages.append({
                'role': 'system',
                'content': f"Info already collected: {'; '.join(context_parts)}. Don't ask for these again.",
            })

    full_messages.extend(messages)

    try:
        response = requests.post(
            GROQ_API_URL,
            headers={
                'Authorization': f'Bearer {GROQ_API_KEY}',
                'Content-Type': 'application/json',
            },
            json={
                'model': GROQ_CHATBOT_MODEL,
                'messages': full_messages,
                'temperature': 0.7,
                'max_tokens': 300,
            },
            timeout=30,
        )

        if response.status_code == 429:
            return {
                'reply': "We're quite busy right now! Please try again in a moment.",
                'error': 'Rate limited',
            }

        response.raise_for_status()
        data = response.json()
        reply = data['choices'][0]['message']['content'].strip()

        return {'reply': reply, 'error': None}

    except requests.exceptions.Timeout:
        return {'reply': "Sorry, I'm a bit slow right now. Could you try again?", 'error': 'Timeout'}
    except requests.exceptions.RequestException as e:
        logger.error(f'Chatbot Groq error: {e}')
        return {'reply': "I'm having a technical issue. Please try again shortly!", 'error': str(e)}


def extract_visitor_info(messages: list) -> dict:
    """
    Extract structured visitor info from the conversation.
    Called after each message to check if we have enough info to generate a coupon.

    Returns dict with: first_name, last_name, email, company, use_case,
                       visitor_type, ready_for_offer, suggested_plan, suggested_duration_days
    """
    if not GROQ_API_KEY:
        return {}

    # Use the fast model for extraction (structured JSON task)
    extraction_model = getattr(settings, 'GROQ_MODEL', 'llama-3.1-8b-instant')

    conversation_text = "\n".join(
        f"{'Visitor' if m['role'] == 'user' else 'AI'}: {m['content']}"
        for m in messages
        if m['role'] in ('user', 'assistant')
    )

    try:
        response = requests.post(
            GROQ_API_URL,
            headers={
                'Authorization': f'Bearer {GROQ_API_KEY}',
                'Content-Type': 'application/json',
            },
            json={
                'model': extraction_model,
                'messages': [
                    {'role': 'system', 'content': 'You extract structured data from conversations. Respond with valid JSON only.'},
                    {'role': 'user', 'content': f"{EXTRACTION_PROMPT}\n\nCONVERSATION:\n{conversation_text}"},
                ],
                'temperature': 0,
                'max_tokens': 300,
            },
            timeout=15,
        )
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content'].strip()

        # Parse JSON (handle markdown fences)
        if content.startswith('```'):
            content = content.split('```')[1]
            if content.startswith('json'):
                content = content[4:]
        return json.loads(content.strip())

    except (requests.exceptions.RequestException, json.JSONDecodeError, KeyError, IndexError) as e:
        logger.warning(f'Chatbot extraction error: {e}')
        return {}
