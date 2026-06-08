"use client";

import { Plus, PanelLeft, Settings, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ConversationList } from "./conversation-list";
import { Conversation } from "@/types/chat";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { useAuth } from "@/hooks/use-auth";

interface SidebarProps {
  conversations: Conversation[];
  activeId?: string;
  onSelect: (id: string) => void;
  onNewChat: () => void;
  isOpen: boolean;
  onToggle: () => void;
}

export function Sidebar({
  conversations,
  activeId,
  onSelect,
  onNewChat,
  isOpen,
  onToggle,
}: SidebarProps) {
  const { user } = useAuth();

  return (
    <aside
      className={`fixed inset-y-0 left-0 z-40 flex w-72 flex-col border-r bg-zinc-50 transition-transform dark:bg-zinc-950 ${
        isOpen ? "translate-x-0" : "-translate-x-full"
      } lg:relative lg:translate-x-0`}
    >
      <div className="flex h-14 items-center justify-between px-4">
        <span className="text-lg font-bold tracking-tight">EKA Assistant</span>
        <Button variant="ghost" size="icon" onClick={onToggle} className="lg:hidden">
          <PanelLeft className="h-5 w-5" />
        </Button>
      </div>

      <div className="px-4 py-2">
        <Button onClick={onNewChat} className="w-full justify-start gap-2" variant="outline">
          <Plus className="h-4 w-4" />
          New Chat
        </Button>
      </div>

      <ScrollArea className="flex-1 py-2">
        <ConversationList
          conversations={conversations}
          activeId={activeId}
          onSelect={onSelect}
        />
      </ScrollArea>

      <div className="mt-auto p-4 space-y-4">
        <Separator />
        <div className="flex items-center gap-3 px-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400">
            <User className="h-4 w-4" />
          </div>
          <div className="flex-1 overflow-hidden">
            <p className="text-sm font-medium truncate">{user?.email}</p>
            <p className="text-xs text-zinc-500 capitalize">{user?.role}</p>
          </div>
          <Button variant="ghost" size="icon" className="h-8 w-8">
            <Settings className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </aside>
  );
}
