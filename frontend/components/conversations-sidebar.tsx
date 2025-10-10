"use client";

import { FC, useMemo } from "react";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Clock } from "lucide-react";

interface ConversationItem {
  id: string;
  title: string;
  subtitle?: string;
  updatedAt?: string;
}

export const ConversationsSidebar: FC = () => {
  // Stub: show a few example items; can be wired to real threads later
  const items: ConversationItem[] = useMemo(
    () => [
      { id: "1", title: "Type 2 diabetes treatments", subtitle: "Latest treatments for elderly patients", updatedAt: "2 hours ago" },
      { id: "2", title: "Heart disease clinical trials", subtitle: "Phase III trials for cardiovascular", updatedAt: "Yesterday" },
      { id: "3", title: "Immunotherapy interactions", subtitle: "Checkpoint inhibitor combinations", updatedAt: "3 days ago" },
    ],
    []
  );

  return (
    <aside className="hidden md:flex w-64 shrink-0 border-r border-border flex-col bg-sidebar">
      <div className="p-4 border-b border-sidebar-border">
        <h2 className="text-sm font-semibold mb-3">Conversations</h2>
        <Input placeholder="Search..." className="h-9 bg-background" />
      </div>
      <ScrollArea className="flex-1">
        <div className="p-2 space-y-1">
          {items.map((it) => (
            <button
              key={it.id}
              className="w-full text-left rounded-md hover:bg-sidebar-accent transition-colors p-3"
              aria-label={`Open conversation: ${it.title}`}
              onClick={() => console.debug('conversation_open', it.id)}
            >
              <div className="text-sm font-medium line-clamp-1 text-sidebar-foreground">{it.title}</div>
              {it.subtitle && (
                <div className="text-xs text-muted-foreground line-clamp-1 mt-0.5">{it.subtitle}</div>
              )}
              {it.updatedAt && (
                <div className="mt-1.5 flex items-center gap-1 text-[11px] text-muted-foreground">
                  <Clock className="w-3 h-3" />
                  <span>{it.updatedAt}</span>
                </div>
              )}
            </button>
          ))}
        </div>
      </ScrollArea>
    </aside>
  );
};

