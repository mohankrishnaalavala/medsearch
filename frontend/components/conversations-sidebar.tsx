"use client";

import { FC, useState, useEffect } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Clock, Plus, Trash2, Edit2, MessageSquare } from "lucide-react";
import { getConversations, deleteConversation, renameConversation } from "@/lib/utils/search-history";
import { ConversationMetadata } from "@/lib/types/search-history";
import { formatDistanceToNow } from "date-fns";

interface ConversationsSidebarProps {
  currentConversationId?: string;
  onConversationSelect: (conversationId: string) => void;
  onNewChat: () => void;
}

export const ConversationsSidebar: FC<ConversationsSidebarProps> = ({
  currentConversationId,
  onConversationSelect,
  onNewChat,
}) => {
  const [conversations, setConversations] = useState<ConversationMetadata[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");

  // Load conversations from localStorage
  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = () => {
    const loaded = getConversations();
    setConversations(loaded);
  };

  const handleDelete = (conversationId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm("Are you sure you want to delete this conversation?")) {
      deleteConversation(conversationId);
      loadConversations();
      // If deleting current conversation, start a new chat
      if (conversationId === currentConversationId) {
        onNewChat();
      }
    }
  };

  const handleRename = (conversationId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const conversation = conversations.find((c) => c.id === conversationId);
    if (conversation) {
      setEditingId(conversationId);
      setEditTitle(conversation.title);
    }
  };

  const handleSaveRename = (conversationId: string) => {
    if (editTitle.trim()) {
      renameConversation(conversationId, editTitle.trim());
      loadConversations();
    }
    setEditingId(null);
    setEditTitle("");
  };

  const handleCancelRename = () => {
    setEditingId(null);
    setEditTitle("");
  };

  // Filter conversations based on search query
  const filteredConversations = conversations.filter((conv) =>
    conv.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    conv.lastQuery?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <aside className="hidden md:flex w-64 shrink-0 border-r border-border flex-col bg-sidebar dark:bg-sidebar">
      <div className="p-4 border-b border-sidebar-border">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold">Conversations</h2>
          <Button
            variant="ghost"
            size="icon"
            onClick={onNewChat}
            aria-label="Start new chat"
            className="h-8 w-8"
          >
            <Plus className="h-4 w-4" />
          </Button>
        </div>
        <Input
          placeholder="Search..."
          className="h-9 bg-background dark:bg-background"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>
      <ScrollArea className="flex-1">
        <div className="p-2 space-y-1">
          {filteredConversations.length === 0 ? (
            <div className="p-4 text-center text-sm text-muted-foreground">
              <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-50" />
              {searchQuery ? "No conversations found" : "No conversations yet"}
            </div>
          ) : (
            filteredConversations.map((conv) => (
              <div
                key={conv.id}
                className={`group relative rounded-md transition-colors ${
                  conv.id === currentConversationId
                    ? "bg-sidebar-accent"
                    : "hover:bg-sidebar-accent"
                }`}
              >
                {editingId === conv.id ? (
                  <div className="p-3" onClick={(e) => e.stopPropagation()}>
                    <Input
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          handleSaveRename(conv.id);
                        } else if (e.key === "Escape") {
                          handleCancelRename();
                        }
                      }}
                      onBlur={() => handleSaveRename(conv.id)}
                      autoFocus
                      className="h-8 text-sm"
                    />
                  </div>
                ) : (
                  <button
                    className="w-full text-left p-3"
                    aria-label={`Open conversation: ${conv.title}`}
                    onClick={() => onConversationSelect(conv.id)}
                  >
                    <div className="text-sm font-medium line-clamp-1 text-sidebar-foreground dark:text-sidebar-foreground pr-16">
                      {conv.title}
                    </div>
                    {conv.lastQuery && (
                      <div className="text-xs text-muted-foreground line-clamp-1 mt-0.5">
                        {conv.lastQuery}
                      </div>
                    )}
                    <div className="mt-1.5 flex items-center gap-2 text-[11px] text-muted-foreground">
                      <Clock className="w-3 h-3" />
                      <span>{formatDistanceToNow(conv.updatedAt, { addSuffix: true })}</span>
                      <span>•</span>
                      <span>{conv.messageCount} messages</span>
                    </div>
                    <div className="absolute top-3 right-3 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={(e) => handleRename(conv.id, e)}
                        aria-label="Rename conversation"
                        className="h-6 w-6"
                      >
                        <Edit2 className="h-3 w-3" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={(e) => handleDelete(conv.id, e)}
                        aria-label="Delete conversation"
                        className="h-6 w-6 text-destructive hover:text-destructive"
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                  </button>
                )}
              </div>
            ))
          )}
        </div>
      </ScrollArea>
    </aside>
  );
};

