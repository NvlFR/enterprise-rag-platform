"use client";

import { useDocuments } from "@/hooks/use-documents";
import { useAuth } from "@/hooks/use-auth";
import ProtectedRoute from "@/components/auth/protected-route";
import { ChatLayout } from "@/components/chat/chat-layout";
import { Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { MessageBubble } from "@/components/chat/message-bubble";
import { Message } from "@/types/chat";
import { useState } from "react";

const MOCK_MESSAGES: Message[] = [
  {
    id: "1",
    conversation_id: "1",
    role: "user",
    content: "What is the policy for annual leave?",
    timestamp: new Date().toISOString(),
  },
  {
    id: "2",
    conversation_id: "1",
    role: "assistant",
    content: "According to the **HR Handbook 2024**, employees are entitled to 20 days of paid annual leave per year. Here are some key points:\n\n- **Accrual:** Leave is accrued monthly.\n- **Carry-over:** You can carry over up to 5 days to the next year.\n- **Approval:** Requests must be submitted at least 2 weeks in advance.\n\nYou can manage your leave through the internal portal.\n\n```python\ndef calculate_remaining_leave(total, used):\n    return total - used\n```",
    timestamp: new Date().toISOString(),
    citations: [
      { id: 1, source: "HR_Handbook_2024.pdf", page: 12, text: "Full-time employees receive 20 days..." }
    ]
  }
];

export default function Home() {
  const { documents, loading } = useDocuments();
  const { user } = useAuth();
  const [messages] = useState<Message[]>(MOCK_MESSAGES);

  return (
    <ProtectedRoute>
      <ChatLayout>
        <div className="flex h-full flex-col">
          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto">
            {messages.length === 0 ? (
              <div className="mt-20 text-center space-y-4 max-w-3xl mx-auto px-4">
                <h2 className="text-3xl font-bold tracking-tight">
                  Hello, {user?.email?.split('@')[0]}
                </h2>
                <p className="text-zinc-500">
                  How can I help you today? I have access to {loading ? "..." : documents.length} documents.
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-12">
                  <button className="p-4 text-left rounded-xl border border-zinc-200 hover:bg-zinc-50 transition-colors dark:border-zinc-800 dark:hover:bg-zinc-900">
                    <p className="font-medium">Annual Leave Policy</p>
                    <p className="text-sm text-zinc-500">What is the policy for carry-over days?</p>
                  </button>
                  <button className="p-4 text-left rounded-xl border border-zinc-200 hover:bg-zinc-50 transition-colors dark:border-zinc-800 dark:hover:bg-zinc-900">
                    <p className="font-medium">Technical Stack</p>
                    <p className="text-sm text-zinc-500">What databases are we using for RAG?</p>
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex flex-col">
                {messages.map((msg) => (
                  <MessageBubble key={msg.id} message={msg} />
                ))}
              </div>
            )}
          </div>

          {/* Input Area */}
          <div className="p-4 border-t bg-white dark:bg-zinc-950">
            <div className="max-w-3xl mx-auto relative">
              <Input 
                placeholder="Ask a question about your documents..." 
                className="pr-12 h-12 rounded-xl"
              />
              <Button 
                size="icon" 
                className="absolute right-1 top-1 h-10 w-10 rounded-lg"
              >
                <Send className="h-5 w-5" />
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
