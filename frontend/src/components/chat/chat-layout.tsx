"use client";

import { useState } from "react";
import { Sidebar } from "./sidebar";
import { Conversation } from "@/types/chat";
import { Menu } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ChatLayoutProps {
  children: React.ReactNode;
}

const MOCK_CONVERSATIONS: Conversation[] = [
  {
    id: "1",
    title: "Annual Leave Policy",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: "2",
    title: "Technical Stack Overview",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: "3",
    title: "HR Onboarding FAQ",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

export function ChatLayout({ children }: ChatLayoutProps) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [activeConversationId, setActiveConversationId] = useState<string | undefined>();
  const [conversations] = useState<Conversation[]>(MOCK_CONVERSATIONS);

  const toggleSidebar = () => setIsSidebarOpen(!isSidebarOpen);

  const handleNewChat = () => {
    setActiveConversationId(undefined);
    // Logic to clear chat area would be handled by children reacting to state or routing
  };

  return (
    <div className="flex h-screen w-full overflow-hidden bg-white dark:bg-zinc-950">
      <Sidebar
        conversations={conversations}
        activeId={activeConversationId}
        onSelect={setActiveConversationId}
        onNewChat={handleNewChat}
        isOpen={isSidebarOpen}
        onToggle={toggleSidebar}
      />

      <div className="flex flex-1 flex-col overflow-hidden relative">
        <header className="flex h-14 items-center border-b px-4 lg:hidden">
          <Button variant="ghost" size="icon" onClick={toggleSidebar}>
            <Menu className="h-5 w-5" />
          </Button>
          <span className="ml-4 font-semibold">EKA Assistant</span>
        </header>

        <main className="flex-1 overflow-hidden relative">
          {children}
        </main>
      </div>

      {/* Mobile Overlay */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 lg:hidden"
          onClick={toggleSidebar}
        />
      )}
    </div>
  );
}
