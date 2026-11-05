from app.models import Message
from app.schemas.chat import Citation


SYSTEM_PROMPT = """You are Aegis AI, a helpful, intelligent private AI assistant.
Respond naturally, concisely, and conversationally.
For casual greetings (such as "hello", "hi"), give a friendly greeting without citing internal configurations or unprompted memories.
Use retrieved long-term memory and knowledge ONLY when directly relevant to answering the user's specific request.
Cite sources accurately when retrieved knowledge documents are provided."""


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
