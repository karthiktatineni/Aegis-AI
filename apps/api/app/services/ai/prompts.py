from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from app.models import Message
from app.schemas.chat import Citation


SYSTEM_PROMPT = """You are Aegis AI, a helpful, intelligent private AI assistant.
Respond naturally, concisely, and conversationally.
For casual greetings (such as "hello", "hi", "hey"), reply with a brief, friendly greeting (e.g. "Hello! How can I help you today?").
Do NOT state the date, time, system status, or environment configuration unless specifically asked by the user.

Conversation Continuity:
- Maintain dialogue continuity across turns.
- Answer follow-up requests and pronouns ("it", "this", "that", "the code for it") based on what was discussed in the immediately preceding message.

Knowledge & Sources:
- Use retrieved long-term memory and knowledge documents ONLY when directly relevant to the user's specific question.
- Cite sources accurately when retrieved knowledge documents or live news updates are provided."""


def is_temporal_query(query: str) -> bool:
    """Detect if query specifically asks about date, time, day, or clock."""
    q = query.lower()
    time_keywords = [
        "time", "date", "day", "clock", "timezone", "ist", "gmt", "utc",
        "what time", "what is the time", "what date", "what is today", "what day"
    ]
    return any(kw in q for kw in time_keywords)


def get_current_clock_info() -> str:
    """Return formatted real-time date and time in UTC and IST."""
    utc_now = datetime.now(timezone.utc)
    ist_offset = timezone(timedelta(hours=5, minutes=30))
    ist_now = datetime.now(ist_offset)
    return (
        f"- Current Date: {ist_now.strftime('%A, %B %d, %Y')}\n"
        f"- Current Time in India (IST): {ist_now.strftime('%I:%M:%S %p IST')} (UTC+5:30)\n"
        f"- Current Time (UTC): {utc_now.strftime('%H:%M:%S UTC')}"
    )


def build_chat_prompt(
    messages: list[Message],
    user_message: str,
    memories: list[str] | None = None,
    citations: list[Citation] | None = None,
    web_results: list[str] | None = None,
) -> list[dict[str, str]]:
    context_parts: list[str] = []

    # Only inject real-time clock when the user is actually asking about time/date
    if is_temporal_query(user_message):
        context_parts.append(
            f"Reference Clock (Use ONLY to answer date/time questions):\n{get_current_clock_info()}"
        )

    if web_results:
        context_parts.append("Real-Time Web & Live News Updates:\n" + "\n".join(f"- {w}" for w in web_results))
    if memories:
        context_parts.append("Relevant long-term memory:\n" + "\n".join(f"- {m}" for m in memories))
    if citations:
        source_lines = [
            f"[{index + 1}] {citation.filename}: {citation.excerpt}"
            for index, citation in enumerate(citations)
        ]
        context_parts.append("Retrieved knowledge:\n" + "\n".join(source_lines))

    system = SYSTEM_PROMPT
    if context_parts:
        system = f"{system}\n\n" + "\n\n".join(context_parts)

    prompt_messages = [{"role": "system", "content": system}]
    # Include up to the last 14 messages from the active thread to maintain strong conversation continuity
    prompt_messages.extend({"role": message.role, "content": message.content} for message in messages[-14:])
    prompt_messages.append({"role": "user", "content": user_message})
    return prompt_messages
