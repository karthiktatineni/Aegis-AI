"use client";

import { Loader2, PanelRightOpen, SendHorizontal, Sparkles, Trash2 } from "lucide-react";
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
    updated_at: now,
  };
}

export function ChatConsole() {
  const [conversations, setConversations] = React.useState<Conversation[]>([]);
  const [active, setActive] = React.useState<Conversation | null>(null);
  const [input, setInput] = React.useState("");
  const [search, setSearch] = React.useState("");
  const [loading, setLoading] = React.useState(false);
  const [elapsedSeconds, setElapsedSeconds] = React.useState(0);
  const [serverSpinningUp, setServerSpinningUp] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const messagesEndRef = React.useRef<HTMLDivElement>(null);
  const scrollContainerRef = React.useRef<HTMLDivElement>(null);

  const scrollToBottom = React.useCallback((behavior: ScrollBehavior = "smooth") => {
    messagesEndRef.current?.scrollIntoView({ behavior });
  }, []);

  // Timer for request duration
  React.useEffect(() => {
    let timer: NodeJS.Timeout | undefined;
    if (loading) {
      setElapsedSeconds(0);
      timer = setInterval(() => {
        setElapsedSeconds((prev) => prev + 1);
      }, 1000);
    } else {
      setElapsedSeconds(0);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [loading]);

  // Auto scroll on new messages
  React.useEffect(() => {
    scrollToBottom();
  }, [active?.messages?.length, scrollToBottom]);

  const refresh = React.useCallback(async (query = "") => {
    try {
      const data = await api.listConversations(query);
      setConversations(data);
      setActive((current) => {
        if (!current) return data[0] ?? null;
        const found = data.find((c) => c.id === current.id);
        return found ?? data[0] ?? null;
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to reach API");
    }
  }, []);

  React.useEffect(() => {
    void refresh();
  }, [refresh]);

  async function createChat() {
    try {
      const conversation = await api.createConversation("New local session");
      setConversations((items) => [conversation, ...items]);
      setActive(conversation);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create conversation");
    }
  }

  async function deleteChat(conversationId: string) {
    try {
      await api.deleteConversation(conversationId);
      setConversations((items) => {
        const remaining = items.filter((c) => c.id !== conversationId);
        if (active?.id === conversationId) {
          setActive(remaining[0] ?? null);
        }
        return remaining;
      });
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete conversation");
    }
  }

  function updateActiveMessage(updated: Message) {
    setActive((conversation) => {
      if (!conversation) return conversation;
      return {
        ...conversation,
        messages: conversation.messages.map((message) => (message.id === updated.id ? updated : message)),
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

    // Scroll right after adding optimistic message
    setTimeout(() => scrollToBottom(), 50);

    try {
      await streamChat(
        active.id,
        { message },
        {
          onStatusChange: (status) => {
            setServerSpinningUp(status === "spinning_up");
          },
          onToken: (token) => {
            setServerSpinningUp(false);
            setActive((conversation) => {
              if (!conversation) return conversation;
              return {
                ...conversation,
                messages: conversation.messages.map((item) =>
                  item.id === assistantMessage.id ? { ...item, content: item.content + token } : item
                ),
              };
            });
            scrollToBottom("auto");
          },
          onDone: () => {
            setServerSpinningUp(false);
            void refresh(search);
          },
        }
      );
    } catch (err) {
      setServerSpinningUp(false);
      setError(err instanceof Error ? err.message : "Streaming failed");
    } finally {
      setLoading(false);
      setServerSpinningUp(false);
    }
  }

  return (
    <section className="flex h-full w-full overflow-hidden">
      <div className="hidden md:flex h-full shrink-0">
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
          onDelete={deleteChat}
        />
      </div>

      <div className="flex min-w-0 flex-1 flex-col h-full overflow-hidden">
        {/* Chat Header */}
        <div className="flex-none flex items-center justify-between border-b px-4 py-3 bg-card/40 backdrop-blur">
          <div className="min-w-0 flex-1 pr-3">
            <div className="flex items-center gap-2">
              <h1 className="truncate text-base font-semibold">{active?.title ?? "Aegis AI"}</h1>
              <Badge variant="outline">Streaming</Badge>
            </div>
            <p className="text-xs text-muted-foreground">Markdown, code, citations, edit history</p>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {active && (
              <Button
                variant="ghost"
                size="icon"
                onClick={() => {
                  if (confirm(`Delete this conversation ("${active.title}")?`)) {
                    void deleteChat(active.id);
                  }
                }}
                title="Delete current conversation"
                className="text-muted-foreground hover:text-destructive"
              >
                <Trash2 className="size-4" />
                <span className="sr-only">Delete conversation</span>
              </Button>
            )}
            <Button variant="outline" size="sm" className="md:hidden" onClick={createChat}>
              <PanelRightOpen className="size-4" />
              New
            </Button>
          </div>
        </div>

        {/* Message Area */}
        <div ref={scrollContainerRef} className="min-h-0 flex-1 overflow-y-auto px-4 py-5">
          {!active ? (
            <Card className="mx-auto max-w-2xl mt-12">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Sparkles className="size-4 text-accent" />
                  Start a conversation
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground mb-4">
                  Select an existing conversation from the sidebar or create a new session to begin.
                </p>
                <Button onClick={createChat}>Create conversation</Button>
              </CardContent>
            </Card>
          ) : (
            <div className="mx-auto flex max-w-4xl flex-col gap-4">
              {active.messages.map((message) => (
                <MessageBubble key={message.id} message={message} onUpdate={updateActiveMessage} />
              ))}
              {loading && (
                <div className="flex items-center gap-2.5 rounded-lg border border-primary/20 bg-muted/40 p-3 text-sm text-foreground">
                  <Loader2 className="size-4 animate-spin text-primary shrink-0" />
                  {serverSpinningUp ? (
                    <span>
                      <strong className="font-semibold text-amber-500 dark:text-amber-400">Server cold start ({elapsedSeconds}s)...</strong> Please wait while the Nvidia T4 GPU boots and loads model weights.
                    </span>
                  ) : (
                    <span className="text-muted-foreground">
                      Generating streaming response ({elapsedSeconds}s)...
                    </span>
                  )}
                </div>
              )}
              <div ref={messagesEndRef} className="h-1" />
            </div>
          )}
        </div>

        {/* Input Bar */}
        <div className="flex-none border-t bg-background p-4">
          <div className="mx-auto max-w-4xl space-y-2">
            {error && <p className="rounded-md border border-destructive/40 p-2 text-sm text-destructive">{error}</p>}
            <div className="flex items-end gap-2">
              <Textarea
                value={input}
                onChange={(event) => setInput(event.target.value)}
                onKeyDown={(event) => {
                  // Enter sends message, Shift+Enter creates a new line
                  if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault();
                    void send();
                  }
                }}
                placeholder="Ask Aegis... (Press Enter to send, Shift+Enter for new line)"
                className="max-h-48 min-h-20 resize-none"
              />
              <Button size="icon" onClick={send} disabled={!active || loading || !input.trim()} title="Send (Enter)">
                {loading ? <Loader2 className="size-4 animate-spin" /> : <SendHorizontal className="size-4" />}
                <span className="sr-only">Send message</span>
              </Button>
            </div>
            <p className="text-[11px] text-muted-foreground text-right pr-1">
              Press <kbd className="rounded border bg-muted px-1">Enter</kbd> to send, <kbd className="rounded border bg-muted px-1">Shift</kbd> + <kbd className="rounded border bg-muted px-1">Enter</kbd> for newline
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
