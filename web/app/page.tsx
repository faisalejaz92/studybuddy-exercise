"use client";

import {
  useState,
  useCallback,
  useSyncExternalStore,
  useRef,
  useEffect,
} from "react";
import type { Message } from "@langchain/langgraph-sdk";
import { useStream } from "@langchain/langgraph-sdk/react";
import { Messages } from "@/components/chat/messages";
import { ChatInput, type ChatInputHandle } from "@/components/chat/input";
import { RefreshCw, User } from "lucide-react";

const USER_ID_KEY = "studybuddy_user_id";

function generateId(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID().slice(0, 8);
  }
  return Math.random().toString(16).slice(2, 10);
}

function getOrCreateUserId(): string {
  if (typeof window === "undefined") return "";
  let userId = localStorage.getItem(USER_ID_KEY);
  if (!userId) {
    userId = `user-${generateId()}`;
    localStorage.setItem(USER_ID_KEY, userId);
  }
  return userId;
}

function subscribeToStorage(callback: () => void) {
  window.addEventListener("storage", callback);
  return () => window.removeEventListener("storage", callback);
}

type ChatState = {
  messages: Message[];
};

type ChatBag = {
  ConfigurableType: { user_id: string };
};

export default function ChatPage() {
  const [threadId, setThreadId] = useState<string | null>(null);
  const [showUserPopup, setShowUserPopup] = useState(false);
  const chatInputRef = useRef<ChatInputHandle>(null);
  const wasLoadingRef = useRef(false);

  const userId = useSyncExternalStore(
    subscribeToStorage,
    getOrCreateUserId,
    () => ""
  );

  const assistantId = process.env.NEXT_PUBLIC_ASSISTANT_ID || "studybuddy";

  const stream = useStream<ChatState, ChatBag>({
    apiUrl: process.env.NEXT_PUBLIC_LANGGRAPH_URL || "http://localhost:2024",
    assistantId,
    messagesKey: "messages",
    threadId: threadId ?? undefined,
    onThreadId: setThreadId,
  });

  const messages: Message[] = stream.messages;
  const { submit, isLoading } = stream;
  const error = stream.error as Error | null;

  const handleSubmit = useCallback(
    (content: string) => {
      if (!userId) return;
      submit(
        { messages: [{ type: "human", content }] },
        { config: { configurable: { user_id: userId } } }
      );
    },
    [submit, userId]
  );

  const handleNewChat = useCallback(() => {
    setThreadId(null);
  }, []);

  useEffect(() => {
    if (wasLoadingRef.current && !isLoading) {
      chatInputRef.current?.focus();
    }
    wasLoadingRef.current = isLoading;
  }, [isLoading]);

  return (
    <div className="flex h-dvh flex-col">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-border px-4 py-3">
        <h1 className="text-lg font-semibold">StudyBuddy</h1>
        <div className="flex items-center gap-3">
          {userId && (
            <div className="relative">
              <button
                onClick={() => setShowUserPopup(!showUserPopup)}
                className="flex items-center justify-center rounded-lg p-1.5 text-muted-foreground hover:bg-secondary hover:text-foreground transition-colors"
                aria-label="User ID"
              >
                <User className="h-4 w-4" />
              </button>
              {showUserPopup && (
                <>
                  <div
                    className="fixed inset-0 z-10"
                    onClick={() => setShowUserPopup(false)}
                  />
                  <div className="absolute right-0 top-full mt-1 z-20 rounded-lg bg-card border border-border shadow-lg px-3 py-2">
                    <p className="text-xs text-muted-foreground whitespace-nowrap">
                      {userId}
                    </p>
                  </div>
                </>
              )}
            </div>
          )}
          {threadId && (
            <span className="text-xs text-muted-foreground">
              Thread: {threadId.slice(0, 8)}...
            </span>
          )}
          <button
            onClick={handleNewChat}
            className="flex items-center justify-center rounded-lg p-1.5 text-muted-foreground hover:bg-secondary hover:text-foreground transition-colors"
            aria-label="New Chat"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </header>

      <Messages messages={messages} isLoading={isLoading} />

      {error && (
        <div className="mx-4 mb-2 rounded-lg bg-destructive/10 px-4 py-2 text-sm text-destructive">
          <strong>Error:</strong>{" "}
          {error instanceof Error ? error.message : String(error)}
        </div>
      )}

      <ChatInput
        ref={chatInputRef}
        onSubmit={handleSubmit}
        disabled={isLoading || !userId}
        placeholder={
          isLoading ? "Waiting for response..." : "Ask about your study notes..."
        }
      />
    </div>
  );
}
