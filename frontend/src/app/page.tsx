"use client";

import { useDocuments } from "@/hooks/use-documents";
import { useAuth } from "@/hooks/use-auth";
import ProtectedRoute from "@/components/auth/protected-route";
import { ChatLayout } from "@/components/chat/chat-layout";
import { Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { MessageBubble } from "@/components/chat/message-bubble";
import { TypingIndicator } from "@/components/chat/typing-indicator";
import { useChatStream } from "@/hooks/use-chat-stream";
import { useState, useRef, useEffect } from "react";
import { cn } from "@/lib/utils";

export default function Home() {
  const { documents, loading: docsLoading } = useDocuments();
  const { user } = useAuth();
  const [input, setInput] = useState("");
  const { messages, isStreaming, sendMessage } = useChatStream();
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isStreaming]);

  const handleSend = async () => {
    if (!input.trim() || isStreaming) return;
    const currentInput = input;
    setInput("");
    await sendMessage(currentInput);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <ProtectedRoute>
      <ChatLayout>
        <div className="flex h-full flex-col">
          {/* Messages Area */}
          <div
            ref={scrollRef}
            className="flex-1 overflow-y-auto"
          >
            {messages.length === 0 ? (
              <div className="mt-20 text-center space-y-4 max-w-3xl mx-auto px-4">
                <h2 className="text-3xl font-bold tracking-tight">
                  Hello, {user?.email?.split('@')[0]}
                </h2>
                <p className="text-zinc-500">
                  How can I help you today? I have access to {docsLoading ? "..." : documents.length} documents.
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-12">
                  <button
                    onClick={() => setInput("What is the policy for annual leave?")}
                    className="p-4 text-left rounded-xl border border-zinc-200 hover:bg-zinc-50 transition-colors dark:border-zinc-800 dark:hover:bg-zinc-900"
                  >
                    <p className="font-medium">Annual Leave Policy</p>
                    <p className="text-sm text-zinc-500">What is the policy for carry-over days?</p>
                  </button>
                  <button
                    onClick={() => setInput("Tell me about the project's technical stack.")}
                    className="p-4 text-left rounded-xl border border-zinc-200 hover:bg-zinc-50 transition-colors dark:border-zinc-800 dark:hover:bg-zinc-900"
                  >
                    <p className="font-medium">Technical Stack</p>
                    <p className="text-sm text-zinc-500">What databases are we using for RAG?</p>
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex flex-col pb-4">
                {messages.map((msg) => (
                  <MessageBubble key={msg.id} message={msg} />
                ))}
                {isStreaming && (
                  <div className="px-4 py-2">
                    <TypingIndicator />
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Input Area */}
          <div className="p-4 border-t bg-white dark:bg-zinc-950">
            <div className="max-w-3xl mx-auto relative">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyPress}
                disabled={isStreaming}
                placeholder="Ask a question about your documents..."
                className="pr-12 h-12 rounded-xl"
              />
              <Button
                onClick={handleSend}
                disabled={!input.trim() || isStreaming}
                size="icon"
                className="absolute right-1 top-1 h-10 w-10 rounded-lg transition-all"
              >
                <Send className={cn("h-5 w-5", isStreaming && "animate-pulse")} />
              </Button>
            </div>
            <p className="text-[10px] text-center mt-2 text-zinc-400">
              EKA can make mistakes. Check important info.
            </p>
          </div>
        </div>
      </ChatLayout>
    </ProtectedRoute>
  );
}
