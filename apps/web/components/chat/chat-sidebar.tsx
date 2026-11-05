"use client";

import { MessageSquarePlus, Pin, Search, Trash2 } from "lucide-react";
import * as React from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import type { Conversation } from "@/types/api";

export function ChatSidebar({
  conversations,
  activeId,
  search,
  onSearch,
  onNew,
  onSelect,
  onDelete,
}: {
  conversations: Conversation[];
  activeId?: string;
  search: string;
  onSearch: (value: string) => void;
  onNew: () => void;
  onSelect: (conversation: Conversation) => void;
  onDelete?: (conversationId: string) => void;
}) {
  return (
    <aside className="flex min-h-0 w-full flex-col border-r bg-card md:w-80">
      <div className="space-y-3 border-b p-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-sm font-semibold">Conversations</p>
            <p className="text-xs text-muted-foreground">{conversations.length} active threads</p>
          </div>
          <Button size="icon" onClick={onNew} title="New conversation">
            <MessageSquarePlus className="size-4" />
            <span className="sr-only">New chat</span>
          </Button>
        </div>
        <div className="relative">
          <Search className="pointer-events-none absolute left-2.5 top-2.5 size-4 text-muted-foreground" />
          <Input
            value={search}
            onChange={(event) => onSearch(event.target.value)}
            placeholder="Search chats"
            className="pl-8"
          />
        </div>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto p-2">
        {conversations.map((conversation) => (
          <div
            key={conversation.id}
            className={cn(
              "group mb-1 flex w-full items-start gap-2 rounded-md px-3 py-2 text-left transition-colors hover:bg-muted cursor-pointer",
              activeId === conversation.id && "bg-muted"
            )}
            onClick={() => onSelect(conversation)}
          >
            <div className="mt-1.5 size-2 shrink-0 rounded-full bg-primary" />
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <p className="truncate text-sm font-medium">{conversation.title}</p>
                {conversation.pinned && <Pin className="size-3 text-accent shrink-0" />}
              </div>
              <p className="mt-1 line-clamp-2 text-xs leading-5 text-muted-foreground">
                {conversation.messages.at(-1)?.content || conversation.summary || "No messages yet"}
              </p>
            </div>
            {onDelete && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  if (confirm(`Delete "${conversation.title}"?`)) {
                    onDelete(conversation.id);
                  }
                }}
                className="opacity-0 group-hover:opacity-100 p-1 text-muted-foreground hover:text-destructive transition-opacity shrink-0 rounded"
                title="Delete chat"
              >
                <Trash2 className="size-3.5" />
                <span className="sr-only">Delete</span>
              </button>
            )}
          </div>
        ))}
      </div>
    </aside>
  );
}
