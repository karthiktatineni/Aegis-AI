import type { Collection, Conversation, Message, ModelStatus, QuotaInfo, ServerHealth } from "@/types/api";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "https://karthiktatineni643--aegis-ai-fastapi-app.us-east.modal.run/api/v1";

export function buildApiUrl(path: string) {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE}${normalized}`;
}

/** Check health and server cold-start status */
export async function checkServerHealth(timeoutMs = 5000): Promise<{ ok: boolean; health?: ServerHealth }> {
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);

    // Try API v1 health first, fallback to root health
    const response = await fetch(buildApiUrl("/health"), {
      signal: controller.signal,
      cache: "no-store",
    }).catch(() =>
      fetch(`${API_BASE.replace(/\/api\/v1\/?$/, "")}/health`, {
        signal: controller.signal,
        cache: "no-store",
      })
    );
    clearTimeout(timer);

    if (response && response.ok) {
      const data = await response.json();
      return { ok: true, health: data };
    }
    return { ok: false };
  } catch {
    return { ok: false };
  }
}

/** Fetch daily GPU request quota status */
export async function fetchDailyQuota(): Promise<QuotaInfo | null> {
  try {
    const response = await fetch(buildApiUrl("/quota"), { cache: "no-store" });
    if (response.ok) {
      return (await response.json()) as QuotaInfo;
    }
  } catch {
    // Graceful fallback
  }
  return null;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const maxRetries = 3;
  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const response = await fetch(buildApiUrl(path), {
        ...init,
        headers: {
          "Content-Type": "application/json",
          ...(init?.headers ?? {}),
        },
      });

      // Cold start / proxy gateway errors (502, 503, 504) -> retry with backoff
      if ([502, 503, 504].includes(response.status) && attempt < maxRetries) {
        await new Promise((resolve) => setTimeout(resolve, 2000 * (attempt + 1)));
        continue;
      }

      if (!response.ok) {
        throw new Error(await response.text());
      }
      return (await response.json()) as T;
    } catch (err) {
      lastError = err instanceof Error ? err : new Error(String(err));
      if (attempt < maxRetries) {
        await new Promise((resolve) => setTimeout(resolve, 1500 * (attempt + 1)));
      }
    }
  }

  throw lastError ?? new Error("Request failed");
}

export const api = {
  listConversations: (query?: string) =>
    request<Conversation[]>(`/chat/conversations${query ? `?q=${encodeURIComponent(query)}` : ""}`),
  createConversation: (title = "New conversation") =>
    request<Conversation>("/chat/conversations", {
      method: "POST",
      body: JSON.stringify({ title }),
    }),
  deleteConversation: (conversationId: string) =>
    request<void>(`/chat/conversations/${conversationId}`, { method: "DELETE" }),
  editMessage: (messageId: string, content: string) =>
    request<Message>(`/chat/messages/${messageId}`, {
      method: "PATCH",
      body: JSON.stringify({ content }),
    }),
  listCollections: () => request<Collection[]>("/knowledge/collections"),
  createCollection: (payload: { name: string; description?: string; tags?: string[] }) =>
    request<Collection>("/knowledge/collections", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  searchKnowledge: (query: string, collection_ids: string[]) =>
    request<{ results: unknown[] }>("/knowledge/search", {
      method: "POST",
      body: JSON.stringify({ query, collection_ids }),
    }),
  modelStatus: () => request<ModelStatus>("/models"),
  getQuota: () => fetchDailyQuota(),
  resetQuota: () => request<QuotaInfo>("/quota/reset", { method: "POST" }),
};

export async function streamChat(
  conversationId: string,
  payload: { message: string; collection_ids?: string[]; use_memory?: boolean; use_rag?: boolean },
  handlers: {
    onToken: (token: string) => void;
    onDone?: (messageId: string) => void;
    onCitations?: (citations: unknown[]) => void;
    onError?: (message: string) => void;
    onStatusChange?: (status: "spinning_up" | "connected") => void;
  }
) {
  const maxRetries = 4;
  let response: Response | null = null;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      response = await fetch(buildApiUrl(`/chat/conversations/${conversationId}/stream`), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          collection_ids: [],
          use_memory: true,
          use_rag: true,
          ...payload,
        }),
      });

      // Cold-start detection: 502/503/504 means server is booting up on Modal / Cloudflare
      if ([502, 503, 504].includes(response.status) && attempt < maxRetries) {
        handlers.onStatusChange?.("spinning_up");
        await new Promise((resolve) => setTimeout(resolve, 3000));
        continue;
      }

      if (response.ok) {
        handlers.onStatusChange?.("connected");
        break;
      }

      // Check for 429 Daily GPU Limit Reached
      if (response.status === 429) {
        const errorText = await response.text();
        let message = "Daily GPU limit reached (5 requests/day). Resets at midnight UTC.";
        try {
          const parsed = JSON.parse(errorText);
          if (parsed.detail) message = parsed.detail;
        } catch {
          // Keep default message
        }
        handlers.onError?.(message);
        throw new Error(message);
      }

      throw new Error(await response.text());
    } catch (err) {
      if (attempt < maxRetries) {
        handlers.onStatusChange?.("spinning_up");
        await new Promise((resolve) => setTimeout(resolve, 3000));
      } else {
        throw err;
      }
    }
  }

  if (!response || !response.ok || !response.body) {
    throw new Error(response ? await response.text() : "Connection failed");
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
