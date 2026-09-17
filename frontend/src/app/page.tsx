"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { HistoryItem, ResearchMode } from "@/lib/types";
import { ModeSelector } from "@/components/ModeSelector";
import { StatusBadge } from "@/components/StatusBadge";

export default function DashboardPage() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState<ResearchMode>("deep");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recent, setRecent] = useState<HistoryItem[] | null>(null);

  useEffect(() => {
    api
      .getHistory()
      .then((res) => setRecent(res.items.slice(0, 5)))
      .catch(() => setRecent([]));
  }, []);

  async function handleSubmit() {
    if (query.trim().length < 8) {
      setError("Describe your research question in a bit more detail (at least 8 characters).");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const { research_id } = await api.createResearch(query.trim(), mode);
      router.push(`/research/${research_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not start research.");
      setSubmitting(false);
    }
  }

  const stats = recent
    ? {
        total: recent.length,
        completed: recent.filter((r) => r.status === "completed").length,
        avgQuality:
          recent.filter((r) => r.quality != null).length > 0
            ? Math.round(
                recent.filter((r) => r.quality != null).reduce((sum, r) => sum + (r.quality ?? 0), 0) /
                  recent.filter((r) => r.quality != null).length
              )
            : null,
      }
    : null;

  return (
    <div className="space-y-10">
      <section>
        <h1 className="text-2xl font-semibold tracking-tight">What do you want to research?</h1>
        <p className="mt-1 text-sm text-white/50">
          ResearchForge plans, researches in parallel, verifies claims, and produces a cited, quality-scored report.
        </p>

        <div className="card mt-6">
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g. Compare the current approaches to building AI coding agents. Analyze their architectures, tool-use patterns, memory strategies, strengths, weaknesses, and recent developments."
            rows={4}
            className="w-full resize-none rounded-md border border-border bg-black/30 p-3 text-sm outline-none focus:border-accent"
          />

          <div className="mt-4">
            <p className="mb-2 text-xs font-medium uppercase tracking-wide text-white/40">Research mode</p>
            <ModeSelector value={mode} onChange={setMode} disabled={submitting} />
          </div>

          {error && <p className="mt-3 text-sm text-bad">{error}</p>}

          <button
            onClick={handleSubmit}
            disabled={submitting}
            className="mt-5 w-full rounded-md bg-accent py-2.5 text-sm font-medium text-white transition hover:bg-accent/90 disabled:opacity-50 sm:w-auto sm:px-8"
          >
            {submitting ? "Starting research…" : "Start Research"}
          </button>
        </div>
      </section>

      <section>
        <div className="flex items-baseline justify-between">
          <h2 className="text-lg font-medium">Recent research</h2>
          <a href="/history" className="text-sm text-accent hover:underline">
            View all
          </a>
        </div>

        {recent === null && <p className="mt-4 text-sm text-white/40">Loading…</p>}

        {recent !== null && recent.length === 0 && (
          <p className="mt-4 text-sm text-white/40">No research yet — start your first question above.</p>
        )}

        {recent !== null && recent.length > 0 && (
          <>
            {stats && (
              <div className="mt-4 grid grid-cols-3 gap-4">
                <div className="card">
                  <p className="text-xs text-white/40">Jobs shown</p>
                  <p className="mt-1 text-xl font-semibold">{stats.total}</p>
                </div>
                <div className="card">
                  <p className="text-xs text-white/40">Completed</p>
                  <p className="mt-1 text-xl font-semibold">{stats.completed}</p>
                </div>
                <div className="card">
                  <p className="text-xs text-white/40">Avg. quality</p>
                  <p className="mt-1 text-xl font-semibold">{stats.avgQuality ?? "—"}</p>
                </div>
              </div>
            )}
            <ul className="mt-4 space-y-2">
              {recent.map((item) => (
                <li key={item.research_id}>
                  <a
                    href={`/research/${item.research_id}`}
                    className="flex items-center justify-between gap-3 rounded-lg border border-border bg-panel p-4 transition hover:border-white/30"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-sm text-white/90">{item.query}</p>
                      <p className="text-xs text-white/40">{item.mode} mode</p>
                    </div>
                    <div className="flex shrink-0 items-center gap-3">
                      {item.quality != null && <span className="text-sm text-white/60">{item.quality}/100</span>}
                      <StatusBadge status={item.status} />
                    </div>
                  </a>
                </li>
              ))}
            </ul>
          </>
        )}
      </section>
    </div>
  );
}
