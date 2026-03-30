"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  RefreshCw,
  ChevronDown,
  ChevronRight,
  AlertCircle,
  Loader2,
  Search,
  X,
  Play,
  Pause,
} from "lucide-react";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------------

const LOGS_URL =
  (process.env.NEXT_PUBLIC_LANGGRAPH_URL || "http://localhost:2024") + "/logs";

const AUTO_REFRESH_MS = 3000;

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface LogEntry {
  timestamp: string;
  level: string;
  logger: string;
  event: string;
  request_id?: string;
  tool_name?: string;
  status?: string;
  duration_ms?: number;
  error?: string;
  [key: string]: unknown;
}

interface LogsResponse {
  entries: LogEntry[];
  total: number;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const LEVEL_STYLES: Record<string, string> = {
  DEBUG:   "bg-gray-100 text-gray-600",
  INFO:    "bg-blue-100 text-blue-700",
  WARNING: "bg-yellow-100 text-yellow-700",
  ERROR:   "bg-red-100 text-red-700",
  CRITICAL:"bg-red-200 text-red-900 font-bold",
};

const LEVEL_ROW_HIGHLIGHT: Record<string, string> = {
  WARNING: "border-l-2 border-l-yellow-400",
  ERROR:   "border-l-2 border-l-red-500",
  CRITICAL:"border-l-2 border-l-red-700 bg-red-50/40",
};

/** Known fixed fields — everything else is shown in the expanded "extra" section */
const KNOWN_FIELDS = new Set([
  "timestamp", "level", "logger", "event",
  "request_id", "tool_name", "status", "duration_ms", "error",
]);

function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString("en-US", {
      hour12: false,
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      fractionalSecondDigits: 3,
    });
  } catch {
    return iso;
  }
}

function extraFields(entry: LogEntry): Record<string, unknown> {
  return Object.fromEntries(
    Object.entries(entry).filter(([k]) => !KNOWN_FIELDS.has(k))
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function LevelBadge({ level }: { level: string }) {
  return (
    <span
      className={cn(
        "rounded px-1.5 py-0.5 text-xs font-mono font-medium",
        LEVEL_STYLES[level.toUpperCase()] ?? "bg-secondary text-secondary-foreground"
      )}
    >
      {level}
    </span>
  );
}

function FilterInput({
  label,
  value,
  onChange,
  placeholder,
  monospace = false,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  monospace?: boolean;
}) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs font-medium text-muted-foreground">{label}</label>
      <div className="relative">
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className={cn(
            "h-8 w-full rounded-md border border-border bg-background px-2.5 text-sm outline-none",
            "focus:ring-1 focus:ring-ring placeholder:text-muted-foreground",
            monospace && "font-mono"
          )}
        />
        {value && (
          <button
            onClick={() => onChange("")}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
          >
            <X className="h-3 w-3" />
          </button>
        )}
      </div>
    </div>
  );
}

/** A single expandable log row */
function LogRow({ entry }: { entry: LogEntry }) {
  const [expanded, setExpanded] = useState(false);
  const extras = extraFields(entry);
  const hasExtras = Object.keys(extras).length > 0 || entry.error;

  return (
    <>
      <tr
        onClick={() => hasExtras && setExpanded((v) => !v)}
        className={cn(
          "border-b border-border text-sm transition-colors",
          hasExtras && "cursor-pointer hover:bg-secondary/50",
          LEVEL_ROW_HIGHLIGHT[entry.level.toUpperCase()]
        )}
      >
        {/* Expand toggle */}
        <td className="w-6 px-2 py-2 text-muted-foreground">
          {hasExtras ? (
            expanded ? (
              <ChevronDown className="h-3.5 w-3.5" />
            ) : (
              <ChevronRight className="h-3.5 w-3.5" />
            )
          ) : null}
        </td>

        {/* Time */}
        <td className="whitespace-nowrap px-2 py-2 font-mono text-xs text-muted-foreground">
          {formatTime(entry.timestamp)}
        </td>

        {/* Level */}
        <td className="px-2 py-2">
          <LevelBadge level={entry.level} />
        </td>

        {/* Event */}
        <td className="px-2 py-2 font-mono text-xs text-foreground">
          {entry.event}
        </td>

        {/* Logger */}
        <td className="hidden px-2 py-2 font-mono text-xs text-muted-foreground md:table-cell">
          {entry.logger}
        </td>

        {/* request_id */}
        <td className="hidden px-2 py-2 font-mono text-xs text-muted-foreground lg:table-cell">
          {entry.request_id ? (
            <span title={entry.request_id}>
              {entry.request_id.slice(0, 8)}…
            </span>
          ) : (
            <span className="text-muted-foreground/40">—</span>
          )}
        </td>

        {/* duration */}
        <td className="hidden px-2 py-2 text-right font-mono text-xs text-muted-foreground xl:table-cell">
          {entry.duration_ms != null ? `${entry.duration_ms}ms` : ""}
        </td>
      </tr>

      {/* Expanded detail row */}
      {expanded && (
        <tr className="border-b border-border bg-secondary/30">
          <td colSpan={7} className="px-4 py-3">
            <div className="space-y-2 text-xs">
              {/* Error block */}
              {entry.error && (
                <div>
                  <p className="mb-1 font-semibold text-destructive">Error / Traceback</p>
                  <pre className="overflow-x-auto rounded bg-destructive/5 p-2 text-destructive/90 text-xs leading-relaxed">
                    {entry.error}
                  </pre>
                </div>
              )}

              {/* Full request_id */}
              {entry.request_id && (
                <div className="flex gap-2">
                  <span className="font-semibold text-muted-foreground w-24 shrink-0">request_id</span>
                  <span className="font-mono text-foreground">{entry.request_id}</span>
                </div>
              )}

              {/* Extra fields */}
              {Object.keys(extras).length > 0 && (
                <div>
                  <p className="mb-1 font-semibold text-muted-foreground">Extra fields</p>
                  <pre className="overflow-x-auto rounded bg-secondary p-2 text-foreground text-xs">
                    {JSON.stringify(extras, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function LogsPage() {
  // -- Filter state ----------------------------------------------------------
  const [levelFilter,     setLevelFilter]     = useState("");
  const [loggerFilter,    setLoggerFilter]    = useState("");
  const [requestIdFilter, setRequestIdFilter] = useState("");
  const [eventFilter,     setEventFilter]     = useState("");

  // -- Data state ------------------------------------------------------------
  const [entries,  setEntries]  = useState<LogEntry[]>([]);
  const [total,    setTotal]    = useState(0);
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState<string | null>(null);
  const [lastFetch, setLastFetch] = useState<Date | null>(null);

  // -- Auto-refresh ----------------------------------------------------------
  const [autoRefresh, setAutoRefresh] = useState(true);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // -- Fetch -----------------------------------------------------------------
  const fetchLogs = useCallback(async () => {
    setLoading(true);
    setError(null);

    const params = new URLSearchParams();
    if (levelFilter)     params.set("level",      levelFilter.toUpperCase());
    if (loggerFilter)    params.set("logger",     loggerFilter);
    if (requestIdFilter) params.set("request_id", requestIdFilter);
    if (eventFilter)     params.set("event",      eventFilter);
    params.set("limit", "500");

    try {
      const res = await fetch(`${LOGS_URL}?${params}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      const data: LogsResponse = await res.json();
      setEntries(data.entries);
      setTotal(data.total);
      setLastFetch(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, [levelFilter, loggerFilter, requestIdFilter, eventFilter]);

  // Fetch on mount and whenever filters change
  useEffect(() => { fetchLogs(); }, [fetchLogs]);

  // Auto-refresh timer
  useEffect(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    if (autoRefresh) {
      timerRef.current = setInterval(fetchLogs, AUTO_REFRESH_MS);
    }
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [autoRefresh, fetchLogs]);

  const clearFilters = useCallback(() => {
    setLevelFilter("");
    setLoggerFilter("");
    setRequestIdFilter("");
    setEventFilter("");
  }, []);

  const hasFilters = levelFilter || loggerFilter || requestIdFilter || eventFilter;

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
        <h1 className="text-lg font-semibold">Log Viewer</h1>
        <span className="text-xs text-muted-foreground hidden sm:inline">
          Live backend log stream
        </span>

        {/* Right controls */}
        <div className="ml-auto flex items-center gap-2">
          {lastFetch && (
            <span className="hidden text-xs text-muted-foreground sm:inline">
              {lastFetch.toLocaleTimeString()}
            </span>
          )}

          {/* Auto-refresh toggle */}
          <button
            onClick={() => setAutoRefresh((v) => !v)}
            className={cn(
              "flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium transition-colors",
              autoRefresh
                ? "bg-primary text-primary-foreground"
                : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
            )}
          >
            {autoRefresh ? <Pause className="h-3 w-3" /> : <Play className="h-3 w-3" />}
            {autoRefresh ? "Live" : "Paused"}
          </button>

          {/* Manual refresh */}
          <button
            onClick={fetchLogs}
            disabled={loading}
            className="flex items-center justify-center rounded-md p-1.5 text-muted-foreground hover:bg-secondary hover:text-foreground transition-colors disabled:opacity-50"
            aria-label="Refresh"
          >
            <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
          </button>
        </div>
      </header>

      {/* ── Filter bar ── */}
      <div className="border-b border-border bg-secondary/30 px-4 py-3">
        <div className="flex flex-wrap items-end gap-3">

          {/* Level select */}
          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-muted-foreground">Level</label>
            <select
              value={levelFilter}
              onChange={(e) => setLevelFilter(e.target.value)}
              className="h-8 rounded-md border border-border bg-background px-2 text-sm outline-none focus:ring-1 focus:ring-ring"
            >
              <option value="">All levels</option>
              <option value="DEBUG">DEBUG</option>
              <option value="INFO">INFO</option>
              <option value="WARNING">WARNING</option>
              <option value="ERROR">ERROR</option>
              <option value="CRITICAL">CRITICAL</option>
            </select>
          </div>

          <FilterInput
            label="Logger prefix"
            value={loggerFilter}
            onChange={setLoggerFilter}
            placeholder="e.g. graph.tools"
          />

          <FilterInput
            label="Request ID"
            value={requestIdFilter}
            onChange={setRequestIdFilter}
            placeholder="UUID prefix..."
            monospace
          />

          <FilterInput
            label="Event contains"
            value={eventFilter}
            onChange={setEventFilter}
            placeholder="e.g. tool.search"
          />

          {hasFilters && (
            <button
              onClick={clearFilters}
              className="flex h-8 items-center gap-1.5 self-end rounded-md border border-border px-3 text-xs text-muted-foreground hover:bg-secondary hover:text-foreground transition-colors"
            >
              <X className="h-3 w-3" />
              Clear
            </button>
          )}

          <span className="self-end pb-1 text-xs text-muted-foreground ml-auto">
            {total} entr{total !== 1 ? "ies" : "y"}
          </span>
        </div>
      </div>

      {/* ── Table ── */}
      <div className="flex-1 overflow-auto">
        {error ? (
          <div className="flex items-start gap-2 p-6 text-destructive">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <div>
              <p className="font-medium text-sm">Failed to fetch logs</p>
              <p className="mt-0.5 text-xs">{error}</p>
              <p className="mt-1 text-xs text-muted-foreground">
                Make sure the LangGraph server is running on port 2024.
              </p>
            </div>
          </div>
        ) : entries.length === 0 && !loading ? (
          <div className="flex flex-col items-center justify-center gap-3 py-20 text-center">
            <Search className="h-8 w-8 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">
              {hasFilters ? "No entries match the current filters." : "No log entries yet. Try using the app!"}
            </p>
          </div>
        ) : (
          <table className="w-full border-collapse text-sm">
            <thead className="sticky top-0 z-10 bg-background border-b border-border">
              <tr className="text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                <th className="w-6 px-2 py-2" />
                <th className="px-2 py-2">Time</th>
                <th className="px-2 py-2">Level</th>
                <th className="px-2 py-2">Event</th>
                <th className="hidden px-2 py-2 md:table-cell">Logger</th>
                <th className="hidden px-2 py-2 lg:table-cell">Request ID</th>
                <th className="hidden px-2 py-2 text-right xl:table-cell">Duration</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry, i) => (
                <LogRow key={`${entry.timestamp}-${i}`} entry={entry} />
              ))}
            </tbody>
          </table>
        )}

        {loading && entries.length === 0 && (
          <div className="flex items-center justify-center gap-2 py-12 text-muted-foreground">
            <Loader2 className="h-5 w-5 animate-spin" />
            <span className="text-sm">Loading logs…</span>
          </div>
        )}
      </div>
    </div>
  );
}
