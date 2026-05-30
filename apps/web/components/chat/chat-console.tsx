"use client";

import { Loader2, PanelRightOpen, SendHorizontal, Sparkles } from "lucide-react";
import * as React from "react";

import { ChatSidebar } from "@/components/chat/chat-sidebar";
import { MessageBubble } from "@/components/chat/message-bubble";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { api, streamChat } from "@/lib/api";
import type { Conversation, Message } from "@/types/api";

function optimisticMessage(conversationId: string, role: "user" | "assistant", content: string): Message {
  const now = new Date().toISOString();
  return {
    id: `${role}-${crypto.randomUUID()}`,
    conversation_id: conversationId,
    role,
    content,
    citations: [],
    created_at: now,
    updated_at: now
  };
}

export function ChatConsole() {
  const [conversations, setConversations] = React.useState<Conversation[]>([]);
  const [active, setActive] = React.useState<Conversation | null>(null);
  const [input, setInput] = React.useState("");
  const [search, setSearch] = React.useState("");
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const refresh = React.useCallback(async (query = "") => {
    try {
      const data = await api.listConversations(query);
      setConversations(data);
      setActive((current) => current ?? data[0] ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to reach API");
    }
  }, []);

  React.useEffect(() => {
    void refresh();
  }, [refresh]);

  async function createChat() {
    const conversation = await api.createConversation("New local session");
    setConversations((items) => [conversation, ...items]);
    setActive(conversation);
  }

  function updateActiveMessage(updated: Message) {
    setActive((conversation) => {
      if (!conversation) return conversation;
      return {
        ...conversation,
        messages: conversation.messages.map((message) => (message.id === updated.id ? updated : message))
      };
    });
  }

  async function send() {
    if (!active || !input.trim() || loading) return;
    const message = input.trim();
    setInput("");
    setLoading(true);
    setError(null);

    const userMessage = optimisticMessage(active.id, "user", message);
    const assistantMessage = optimisticMessage(active.id, "assistant", "");
    setActive((conversation) =>
      conversation
        ? { ...conversation, messages: [...conversation.messages, userMessage, assistantMessage] }
        : conversation
    );

    try {
      await streamChat(
        active.id,
        { message },
        {
          onToken: (token) => {
            setActive((conversation) => {
              if (!conversation) return conversation;
              return {
                ...conversation,
                messages: conversation.messages.map((item) =>
                  item.id === assistantMessage.id ? { ...item, content: item.content + token } : item
                )
              };
            });
          },
          onDone: () => {
            void refresh(search);
          }
        }
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Streaming failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="flex h-[calc(100vh-4rem)]">
      <div className="hidden md:flex">
        <ChatSidebar
          conversations={conversations}
          activeId={active?.id}
          search={search}
          onSearch={(value) => {
            setSearch(value);
            void refresh(value);
          }}
          onNew={createChat}
          onSelect={setActive}
        />
      </div>

      <div className="flex min-w-0 flex-1 flex-col">
        <div className="flex items-center justify-between border-b px-4 py-3">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <h1 className="truncate text-base font-semibold">{active?.title ?? "Aegis AI"}</h1>
              <Badge variant="outline">Streaming</Badge>
            </div>
            <p className="text-xs text-muted-foreground">Markdown, code, citations, edit history</p>
          </div>
          <Button variant="outline" size="sm" className="md:hidden" onClick={createChat}>
            <PanelRightOpen className="size-4" />
            New
          </Button>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto px-4 py-5">
          {!active ? (
            <Card className="mx-auto max-w-2xl">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Sparkles className="size-4 text-accent" />
                  Start a local session
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Button onClick={createChat}>Create conversation</Button>
              </CardContent>
            </Card>
          ) : (
            <div className="mx-auto flex max-w-4xl flex-col gap-4">
              {active.messages.map((message) => (
                <MessageBubble key={message.id} message={message} onUpdate={updateActiveMessage} />
              ))}
              {loading && (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="size-4 animate-spin" />
                  Generating
                </div>
              )}
            </div>
          )}
        </div>

        <div className="border-t bg-background p-4">
          <div className="mx-auto max-w-4xl space-y-2">
            {error && <p className="rounded-md border border-destructive/40 p-2 text-sm text-destructive">{error}</p>}
            <div className="flex items-end gap-2">
              <Textarea
                value={input}
                onChange={(event) => setInput(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
                    void send();
                  }
                }}
                placeholder="Ask Aegis"
                className="max-h-48 min-h-20 resize-none"
              />
              <Button size="icon" onClick={send} disabled={!active || loading || !input.trim()}>
                {loading ? <Loader2 className="size-4 animate-spin" /> : <SendHorizontal className="size-4" />}
                <span className="sr-only">Send message</span>
              </Button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
