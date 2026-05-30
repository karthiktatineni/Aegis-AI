import type { Collection, Conversation, Message, ModelStatus } from "@/types/api";

export const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export function buildApiUrl(path: string) {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE}${normalized}`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(buildApiUrl(path), {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    }
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json() as Promise<T>;
}

export const api = {
  listConversations: (query?: string) =>
    request<Conversation[]>(`/chat/conversations${query ? `?q=${encodeURIComponent(query)}` : ""}`),
  createConversation: (title = "New conversation") =>
    request<Conversation>("/chat/conversations", {
      method: "POST",
      body: JSON.stringify({ title })
    }),
  editMessage: (messageId: string, content: string) =>
    request<Message>(`/chat/messages/${messageId}`, {
      method: "PATCH",
      body: JSON.stringify({ content })
    }),
  listCollections: () => request<Collection[]>("/knowledge/collections"),
  createCollection: (payload: { name: string; description?: string; tags?: string[] }) =>
    request<Collection>("/knowledge/collections", {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  searchKnowledge: (query: string, collection_ids: string[]) =>
    request<{ results: unknown[] }>("/knowledge/search", {
      method: "POST",
      body: JSON.stringify({ query, collection_ids })
    }),
  modelStatus: () => request<ModelStatus>("/models")
};

export async function streamChat(
  conversationId: string,
  payload: { message: string; collection_ids?: string[]; use_memory?: boolean; use_rag?: boolean },
  handlers: {
    onToken: (token: string) => void;
    onDone?: (messageId: string) => void;
    onCitations?: (citations: unknown[]) => void;
    onError?: (message: string) => void;
  }
) {
  const response = await fetch(buildApiUrl(`/chat/conversations/${conversationId}/stream`), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      collection_ids: [],
      use_memory: true,
      use_rag: true,
      ...payload
    })
  });
  if (!response.ok || !response.body) {
    throw new Error(await response.text());
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop() ?? "";
    for (const rawEvent of events) {
      const eventLine = rawEvent.split("\n").find((line) => line.startsWith("event:"));
      const dataLine = rawEvent.split("\n").find((line) => line.startsWith("data:"));
      if (!eventLine || !dataLine) continue;
      const event = eventLine.replace("event:", "").trim();
      const data = JSON.parse(dataLine.replace("data:", "").trim());
      if (event === "token") handlers.onToken(data.text);
      if (event === "citations") handlers.onCitations?.(data.citations);
      if (event === "done") handlers.onDone?.(data.message_id);
      if (event === "error") {
        const message = typeof data.message === "string" ? data.message : "Streaming failed";
        handlers.onError?.(message);
        throw new Error(message);
      }
    }
  }
}
