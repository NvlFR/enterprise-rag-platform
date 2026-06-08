"use client";

import { Conversation } from "@/types/chat";
import { MessageSquare, MoreHorizontal } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

interface ConversationListProps {
  conversations: Conversation[];
  activeId?: string;
  onSelect: (id: string) => void;
}

export function ConversationList({ conversations, activeId, onSelect }: ConversationListProps) {
  return (
    <div className="space-y-1 px-2">
      {conversations.map((conversation) => (
        <div
          key={conversation.id}
          role="button"
          tabIndex={0}
          onClick={() => onSelect(conversation.id)}
          onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') onSelect(conversation.id); }}
          className={cn(
            "group flex w-full cursor-pointer items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors hover:bg-zinc-100 dark:hover:bg-zinc-800",
            activeId === conversation.id
              ? "bg-zinc-100 text-zinc-900 dark:bg-zinc-800 dark:text-zinc-50"
              : "text-zinc-600 dark:text-zinc-400"
          )}
        >
          <MessageSquare className="h-4 w-4 shrink-0" />
          <span className="flex-1 overflow-hidden text-ellipsis whitespace-nowrap text-left">
            {conversation.title}
          </span>
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6 opacity-0 group-hover:opacity-100"
          >
            <MoreHorizontal className="h-4 w-4" />
          </Button>
        </div>
      ))}
    </div>
  );
}
