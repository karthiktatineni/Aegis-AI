from __future__ import annotations

from datetime import datetime, timedelta, timezone
from app.models import Message
from app.schemas.chat import Citation


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


def get_system_prompt() -> str:
    clock = get_current_clock_info()
    return f"""You are Aegis AI, a private, intelligent, and highly capable AI assistant.

Real-Time Clock & Grounding:
{clock}
India observes a single timezone: Indian Standard Time (IST, UTC+5:30). If the user asks for the current date or time (especially in India), answer with the exact real-time clock above.

Chat Continuity & Short-Term Context:
- Maintain conversation continuity across turns.
- Always prioritize the active conversation history when answering follow-up questions, pronouns ("it", "this", "that", "the code for it"), or continuous topics.
- Answer follow-up requests in the context of the immediately preceding dialogue.

Tone & Knowledge:
- Be concise, direct, helpful, and natural.
- Use retrieved long-term memory and knowledge documents ONLY when directly relevant to the user's specific question.
- Cite sources when retrieved knowledge documents or live news updates are provided."""


def build_chat_prompt(
    messages: list[Message],
    user_message: str,
    memories: list[str] | None = None,
    citations: list[Citation] | None = None,
    web_results: list[str] | None = None,
) -> list[dict[str, str]]:
    context_parts: list[str] = []
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

    system = get_system_prompt()
    if context_parts:
        system = f"{system}\n\n" + "\n\n".join(context_parts)

    prompt_messages = [{"role": "system", "content": system}]
    # Include up to the last 14 messages from the active thread to maintain strong conversation continuity
    prompt_messages.extend({"role": message.role, "content": message.content} for message in messages[-14:])
    prompt_messages.append({"role": "user", "content": user_message})
    return prompt_messages
