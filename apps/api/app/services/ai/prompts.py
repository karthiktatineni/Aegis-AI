from app.models import Message
from app.schemas.chat import Citation


SYSTEM_PROMPT = """You are Aegis AI, a private local assistant.
Use retrieved memory and knowledge only when it is relevant. Cite sources when provided.
Be direct, technically precise, and transparent about uncertainty."""


def build_chat_prompt(
    messages: list[Message],
    user_message: str,
    memories: list[str],
    citations: list[Citation],
) -> list[dict[str, str]]:
    context_parts: list[str] = []
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
    prompt_messages.extend({"role": message.role, "content": message.content} for message in messages[-12:])
    prompt_messages.append({"role": "user", "content": user_message})
    return prompt_messages
