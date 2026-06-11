"use client";

import { Message } from "@/types/chat";
import { cn } from "@/lib/utils";
import { MarkdownRenderer } from "./markdown-renderer";
import { User, Bot, Copy, ThumbsUp, ThumbsDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { SourcePopover } from "./source-popover";
import { TypingIndicator } from "./typing-indicator";

interface MessageBubbleProps {
  message: Message;
  isStreaming?: boolean;
}

export function MessageBubble({ message, isStreaming }: MessageBubbleProps) {
  const isAssistant = message.role === 'assistant';

  const copyToClipboard = () => {
    navigator.clipboard.writeText(message.content);
    toast.success("Copied to clipboard");
  };

  return (
    <div
      className={cn(
        "group flex w-full items-start gap-4 py-8",
        isAssistant ? "bg-zinc-50/50 dark:bg-zinc-900/50" : "bg-white dark:bg-zinc-950"
      )}
    >
      <div className="container mx-auto max-w-3xl px-4 flex gap-4">
        <div className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border text-sm font-medium",
          isAssistant
            ? "bg-blue-600 border-blue-600 text-white"
            : "bg-white border-zinc-200 text-zinc-600 dark:bg-zinc-800 dark:border-zinc-700 dark:text-zinc-400"
        )}>
          {isAssistant ? <Bot className="h-5 w-5" /> : <User className="h-5 w-5" />}
        </div>

        <div className="flex-1 space-y-2 overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-zinc-500">
              {isAssistant ? "Assistant" : "You"}
            </span>
            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <Button variant="ghost" size="icon" className="h-8 w-8" onClick={copyToClipboard}>
                <Copy className="h-4 w-4" />
              </Button>
              {isAssistant && (
                <>
                  <Button variant="ghost" size="icon" className="h-8 w-8">
                    <ThumbsUp className="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="icon" className="h-8 w-8">
                    <ThumbsDown className="h-4 w-4" />
                  </Button>
                </>
              )}
            </div>
          </div>

          {isAssistant && isStreaming && message.content === "" ? (
            <TypingIndicator />
          ) : (
            <MarkdownRenderer content={message.content} citations={message.citations} />
          )}

          {message.citations && message.citations.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-2">
              <span className="text-xs font-medium text-zinc-400 w-full">Sources:</span>
              {message.citations.map((citation) => (
                <SourcePopover key={citation.id} citation={citation}>
                  <button
                    className="inline-flex items-center gap-1 rounded-full bg-zinc-100 px-2 py-0.5 text-[10px] font-medium text-zinc-600 hover:bg-zinc-200 dark:bg-zinc-800 dark:text-zinc-400 dark:hover:bg-zinc-700 transition-colors"
                  >
                    [{citation.id}] {citation.source} {citation.page ? `p.${citation.page}` : ''}
                  </button>
                </SourcePopover>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
