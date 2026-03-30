"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { Client } from "@langchain/langgraph-sdk";
import type { Thread, ThreadState } from "@langchain/langgraph-sdk";
import type { Message } from "@langchain/langgraph-sdk";
import {
  ArrowLeft,
  Loader2,
  AlertCircle,
  Bot,
  User,
  Wrench,
  Terminal,
  ChevronDown,
  ChevronRight,
  MessageSquare,
  RefreshCw,
  ScrollText,
} from "lucide-react";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

const LANGGRAPH_URL =
  process.env.NEXT_PUBLIC_LANGGRAPH_URL || "http://localhost:2024";

function getClient() {
  return new Client({ apiUrl: LANGGRAPH_URL });
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

// The state values this graph stores. Messages live under `values.messages`.
type GraphValues = { messages?: Message[] };

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Return a human-readable relative time string, e.g. "3 minutes ago". */
function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const s = Math.floor(diff / 1000);
  if (s < 60) return `${s}s ago`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

/** Extract plain text from a message's content (handles string or complex parts). */
function getTextContent(content: Message["content"]): string {
  if (typeof content === "string") return content;
  return content
    .filter((p): p is { type: "text"; text: string } => p.type === "text")
    .map((p) => p.text)
    .join("");
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

/** Coloured badge for thread status. */
function StatusBadge({ status }: { status: Thread["status"] }) {
  const styles: Record<typeof status, string> = {
    idle: "bg-green-100 text-green-700",
    busy: "bg-blue-100 text-blue-700",
    interrupted: "bg-yellow-100 text-yellow-700",
    error: "bg-red-100 text-red-700",
  };
  return (
    <span
      className={cn(
        "rounded px-1.5 py-0.5 text-xs font-medium",
        styles[status] ?? "bg-secondary text-secondary-foreground"
      )}
    >
      {status}
    </span>
  );
}

/** Collapsible section used for tool args / tool results. */
function Collapsible({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);
  return (
    <div className="mt-1">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
      >
        {open ? (
          <ChevronDown className="h-3 w-3" />
        ) : (
          <ChevronRight className="h-3 w-3" />
        )}
        {label}
      </button>
      {open && (
        <pre className="mt-1 overflow-x-auto rounded bg-secondary p-2 text-xs text-foreground">
          {children}
        </pre>
      )}
    </div>
  );
}

/** Renders a single message row — handles all LangGraph message types. */
function MessageRow({ message }: { message: Message }) {
  const { type } = message;

  // ── Tool result ──────────────────────────────────────────────────────────
  if (type === "tool") {
    const content = getTextContent(message.content);
    return (
      <div className="flex gap-3 rounded-lg border border-border bg-secondary/40 px-3 py-2">
        <Terminal className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
        <div className="min-w-0 flex-1">
          <p className="text-xs font-medium text-muted-foreground">
            Tool result
            {"tool_call_id" in message && (
              <span className="ml-1 font-mono opacity-60">
                · {(message as { tool_call_id: string }).tool_call_id.slice(0, 8)}
              </span>
            )}
          </p>
          <Collapsible label="Show output">
            {content || "(empty)"}
          </Collapsible>
        </div>
      </div>
    );
  }

  // ── AI message ────────────────────────────────────────────────────────────
  if (type === "ai") {
    const aiMsg = message as Message & {
      tool_calls?: Array<{ name: string; args: Record<string, unknown>; id?: string }>;
    };
    const toolCalls = aiMsg.tool_calls ?? [];
    const text = getTextContent(message.content);
    const hasText = text.trim().length > 0;

    return (
      <div className="flex gap-3">
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-secondary">
          <Bot className="h-4 w-4 text-primary" />
        </div>
        <div className="min-w-0 flex-1">
          {/* Tool-call steps (intermediate agent actions) */}
          {toolCalls.length > 0 && (
            <div className="space-y-1">
              {toolCalls.map((tc, i) => (
                <div
                  key={tc.id ?? i}
                  className="rounded-md border border-border bg-secondary/40 px-3 py-2"
                >
                  <div className="flex items-center gap-1.5">
                    <Wrench className="h-3.5 w-3.5 text-muted-foreground" />
                    <span className="text-xs font-semibold text-foreground">
                      {tc.name}
                    </span>
                    {tc.id && (
                      <span className="font-mono text-xs text-muted-foreground opacity-60">
                        · {tc.id.slice(0, 8)}
                      </span>
                    )}
                  </div>
                  <Collapsible label="Show args">
                    {JSON.stringify(tc.args, null, 2)}
                  </Collapsible>
                </div>
              ))}
            </div>
          )}
          {/* Final prose response */}
          {hasText && (
            <p
              className={cn(
                "whitespace-pre-wrap text-sm text-foreground",
                toolCalls.length > 0 && "mt-2"
              )}
            >
              {text}
            </p>
          )}
        </div>
      </div>
    );
  }

  // ── Human message ─────────────────────────────────────────────────────────
  if (type === "human") {
    return (
      <div className="flex gap-3">
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-secondary">
          <User className="h-4 w-4 text-secondary-foreground" />
        </div>
        <p className="flex-1 whitespace-pre-wrap text-sm text-foreground">
          {getTextContent(message.content)}
        </p>
      </div>
    );
  }

  // ── System / other internal messages — shown but de-emphasised ────────────
  return (
    <div className="rounded border border-dashed border-border px-3 py-2">
      <p className="text-xs text-muted-foreground">
        <span className="font-mono">[{type}]</span>{" "}
        {getTextContent(message.content) || "(no text content)"}
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Left panel — thread list
// ---------------------------------------------------------------------------

interface ThreadListProps {
  threads: Thread[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

function ThreadList({ threads, selectedId, onSelect }: ThreadListProps) {
  if (threads.length === 0) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-2 p-6 text-center">
        <MessageSquare className="h-8 w-8 text-muted-foreground" />
        <p className="text-sm text-muted-foreground">No threads yet</p>
      </div>
    );
  }

  return (
    <ul className="flex-1 overflow-y-auto divide-y divide-border">
      {threads.map((t) => {
        const values = t.values as GraphValues | undefined;
        const msgs = values?.messages ?? [];
        // Find last human message for a quick preview
        const lastHuman = [...msgs]
          .reverse()
          .find((m) => m.type === "human");
        const preview = lastHuman
          ? getTextContent(lastHuman.content).slice(0, 60)
          : null;

        return (
          <li key={t.thread_id}>
            <button
              onClick={() => onSelect(t.thread_id)}
              className={cn(
                "w-full px-4 py-3 text-left transition-colors hover:bg-secondary",
                selectedId === t.thread_id && "bg-secondary"
              )}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="truncate font-mono text-xs font-medium text-foreground">
                  {t.thread_id.slice(0, 16)}…
                </span>
                <StatusBadge status={t.status} />
              </div>
              {preview && (
                <p className="mt-0.5 truncate text-xs text-muted-foreground">
                  {preview}
                </p>
              )}
              <p className="mt-0.5 text-xs text-muted-foreground">
                {relativeTime(t.updated_at)} · {msgs.length} msg
                {msgs.length !== 1 ? "s" : ""}
              </p>
            </button>
          </li>
        );
      })}
    </ul>
  );
}

// ---------------------------------------------------------------------------
// Right panel — thread detail
// ---------------------------------------------------------------------------

interface ThreadDetailProps {
  threadId: string;
  state: ThreadState<GraphValues> | null;
  loading: boolean;
  error: string | null;
}

function ThreadDetail({ threadId, state, loading, error }: ThreadDetailProps) {
  if (loading) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-1 items-center justify-center p-8">
        <div className="flex items-start gap-2 text-destructive">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          <p className="text-sm">{error}</p>
        </div>
      </div>
    );
  }

  if (!state) return null;

  const messages = state.values?.messages ?? [];
  // Tasks that errored give us diagnostic info
  const erroredTasks = state.tasks.filter((t) => t.error);

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      {/* Detail header */}
      <div className="border-b border-border px-6 py-3">
        <p className="font-mono text-xs text-muted-foreground">
          Thread:{" "}
          <span className="text-foreground">{threadId}</span>
        </p>
        <p className="text-xs text-muted-foreground">
          {messages.length} message{messages.length !== 1 ? "s" : ""}
          {state.next.length > 0 && (
            <span className="ml-2 text-blue-600">
              · next: {state.next.join(", ")}
            </span>
          )}
        </p>
      </div>

      {/* Errored tasks banner */}
      {erroredTasks.length > 0 && (
        <div className="border-b border-destructive/30 bg-destructive/5 px-6 py-3">
          <div className="flex items-start gap-2">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-destructive" />
            <div>
              <p className="text-xs font-semibold text-destructive">
                {erroredTasks.length} task error
                {erroredTasks.length !== 1 ? "s" : ""}
              </p>
              {erroredTasks.map((t) => (
                <p key={t.id} className="mt-0.5 text-xs text-destructive/80">
                  <span className="font-mono">{t.name}</span>: {t.error}
                </p>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Message list */}
      {messages.length === 0 ? (
        <div className="flex flex-1 items-center justify-center p-8">
          <p className="text-sm text-muted-foreground">No messages in this thread.</p>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto px-6 py-4">
          <div className="space-y-4">
            {messages.map((msg, i) => (
              <MessageRow key={msg.id ?? `msg-${i}`} message={msg} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function AdminPage() {
  const client = getClient();

  // Thread list state
  const [threads, setThreads] = useState<Thread[]>([]);
  const [threadsLoading, setThreadsLoading] = useState(true);
  const [threadsError, setThreadsError] = useState<string | null>(null);

  // Selected thread detail state
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [threadState, setThreadState] =
    useState<ThreadState<GraphValues> | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);

  // Load thread list — called on mount and by the refresh button
  const loadThreads = useCallback(() => {
    setThreadsLoading(true);
    setThreadsError(null);
    client.threads
      .search({ limit: 50, sortBy: "updated_at", sortOrder: "desc" })
      .then(setThreads)
      .catch((err: unknown) => {
        const msg = err instanceof Error ? err.message : String(err);
        setThreadsError(`Failed to load threads: ${msg}`);
      })
      .finally(() => setThreadsLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => { loadThreads(); }, [loadThreads]);

  // Load detail when a thread is selected
  const handleSelectThread = useCallback(
    (id: string) => {
      setSelectedId(id);
      setThreadState(null);
      setDetailError(null);
      setDetailLoading(true);
      client.threads
        .getState<GraphValues>(id)
        .then(setThreadState)
        .catch((err: unknown) => {
          const msg = err instanceof Error ? err.message : String(err);
          setDetailError(`Failed to load thread: ${msg}`);
        })
        .finally(() => setDetailLoading(false));
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );

  return (
    <div className="flex h-dvh flex-col">
      {/* ── Header ── */}
      <header className="flex items-center gap-4 border-b border-border px-4 py-3">
        <Link
          href="/"
          className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Chat
        </Link>
        <h1 className="text-lg font-semibold">Support Admin</h1>
        <span className="text-xs text-muted-foreground">
          Conversation thread inspector
        </span>
        <Link
          href="/logs"
          className="ml-auto flex items-center justify-center rounded-lg p-1.5 text-muted-foreground hover:bg-secondary hover:text-foreground transition-colors"
          aria-label="Log Viewer"
        >
          <ScrollText className="h-4 w-4" />
        </Link>
      </header>

      {/* ── Body: two-panel layout ── */}
      <div className="flex flex-1 overflow-hidden">

        {/* Left panel — thread list */}
        <aside className="flex w-72 shrink-0 flex-col border-r border-border">
          <div className="flex items-center justify-between border-b border-border px-4 py-2">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Recent Threads
            </p>
            <button
              onClick={loadThreads}
              disabled={threadsLoading}
              className="flex items-center justify-center rounded p-1 text-muted-foreground hover:bg-secondary hover:text-foreground transition-colors disabled:opacity-50"
              aria-label="Refresh threads"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${threadsLoading ? "animate-spin" : ""}`} />
            </button>
          </div>

          {threadsLoading ? (
            <div className="flex flex-1 items-center justify-center">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : threadsError ? (
            <div className="p-4">
              <div className="flex items-start gap-2 text-destructive">
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                <p className="text-xs">{threadsError}</p>
              </div>
            </div>
          ) : (
            <ThreadList
              threads={threads}
              selectedId={selectedId}
              onSelect={handleSelectThread}
            />
          )}
        </aside>

        {/* Right panel — detail or empty state */}
        <main className="flex flex-1 flex-col overflow-hidden">
          {selectedId ? (
            <ThreadDetail
              threadId={selectedId}
              state={threadState}
              loading={detailLoading}
              error={detailError}
            />
          ) : (
            <div className="flex flex-1 flex-col items-center justify-center gap-3 p-8 text-center">
              <MessageSquare className="h-10 w-10 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">
                Select a thread on the left to inspect its conversation.
              </p>
            </div>
          )}
        </main>

      </div>
    </div>
  );
}
