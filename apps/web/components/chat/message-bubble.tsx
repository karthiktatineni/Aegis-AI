"use client";

import { Check, Copy, Edit3, Save, X } from "lucide-react";
import * as React from "react";

import { MarkdownMessage } from "@/components/chat/markdown-message";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { Message } from "@/types/api";

export function MessageBubble({
  message,
  onUpdate
}: {
  message: Message;
  onUpdate: (message: Message) => void;
}) {
  const [editing, setEditing] = React.useState(false);
  const [value, setValue] = React.useState(message.content);
  const [copied, setCopied] = React.useState(false);
  const isUser = message.role === "user";

  async function save() {
    const updated = await api.editMessage(message.id, value);
    onUpdate(updated);
    setEditing(false);
  }

  async function copy() {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1200);
  }

  return (
    <article className={cn("group flex gap-3", isUser && "justify-end")}>
      <div
        className={cn(
          "max-w-[min(780px,92vw)] rounded-lg border px-4 py-3",
          isUser ? "bg-primary text-primary-foreground" : "bg-card"
        )}
      >
        <div className="mb-2 flex items-center justify-between gap-3">
          <Badge variant={isUser ? "accent" : "secondary"}>{isUser ? "You" : "Aegis"}</Badge>
          <div className="flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
            <Button variant="ghost" size="icon" onClick={copy}>
              {copied ? <Check className="size-4" /> : <Copy className="size-4" />}
              <span className="sr-only">Copy message</span>
            </Button>
            <Button variant="ghost" size="icon" onClick={() => setEditing(true)}>
              <Edit3 className="size-4" />
              <span className="sr-only">Edit message</span>
            </Button>
          </div>
        </div>
        {editing ? (
          <div className="space-y-2">
            <Textarea value={value} onChange={(event) => setValue(event.target.value)} className="min-h-32" />
            <div className="flex justify-end gap-2">
              <Button variant="ghost" size="sm" onClick={() => setEditing(false)}>
                <X className="size-4" />
                Cancel
              </Button>
              <Button size="sm" onClick={save}>
                <Save className="size-4" />
                Save
              </Button>
            </div>
          </div>
        ) : (
          <MarkdownMessage content={message.content} />
        )}
        {!!message.citations?.length && (
          <div className="mt-3 space-y-2 border-t pt-3">
            {message.citations.map((citation) => (
              <div key={citation.chunk_id} className="rounded-md bg-muted p-2 text-xs text-muted-foreground">
                <span className="font-medium text-foreground">{citation.filename}</span>
                <span className="ml-2">{Math.round(citation.score * 100)}%</span>
                <p className="mt-1 line-clamp-2">{citation.excerpt}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </article>
  );
}
