"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { HistoryItem, ResearchMode } from "@/lib/types";
import { StatusBadge } from "@/components/StatusBadge";

const MODE_FILTERS: ("all" | ResearchMode)[] = ["all", "quick", "deep", "exhaustive"];

export default function HistoryPage() {
  const [items, setItems] = useState<HistoryItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [modeFilter, setModeFilter] = useState<"all" | ResearchMode>("all");

  useEffect(() => {
    api
      .getHistory()
      .then((res) => setItems(res.items))
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load history."));
  }, []);

  const visible = items?.filter((i) => modeFilter === "all" || i.mode === modeFilter) ?? null;

  return (
    <div>
      <h1 className="text-2xl font-semibold tracking-tight">Research History</h1>
      <p className="mt-1 text-sm text-white/50">Every research job this ResearchForge instance has run.</p>

      <div className="mt-6 flex gap-2">
        {MODE_FILTERS.map((m) => (
          <button
            key={m}
            onClick={() => setModeFilter(m)}
            className={`rounded-full border px-3 py-1 text-xs capitalize transition ${
              modeFilter === m ? "border-accent bg-accent/10 text-accent" : "border-border text-white/50 hover:text-white"
            }`}
          >
            {m}
          </button>
        ))}
      </div>

      {error && <p className="mt-6 text-sm text-bad">{error}</p>}
      {!error && visible === null && <p className="mt-6 text-sm text-white/40">Loading…</p>}
      {!error && visible !== null && visible.length === 0 && (
        <p className="mt-6 text-sm text-white/40">No research jobs match this filter yet.</p>
      )}

      {visible && visible.length > 0 && (
        <div className="mt-6 overflow-hidden rounded-xl border border-border">
          <table className="w-full text-left text-sm">
            <thead className="bg-panel text-xs uppercase tracking-wide text-white/40">
              <tr>
                <th className="px-4 py-3">Query</th>
                <th className="px-4 py-3">Mode</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Quality</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((item) => (
                <tr key={item.research_id} className="border-t border-border hover:bg-white/5">
                  <td className="max-w-md px-4 py-3">
                    <a href={`/research/${item.research_id}`} className="block truncate text-white/90 hover:text-accent">
                      {item.query}
                    </a>
                  </td>
                  <td className="px-4 py-3 capitalize text-white/60">{item.mode}</td>
                  <td className="px-4 py-3">
                    <StatusBadge status={item.status} />
                  </td>
                  <td className="px-4 py-3 text-white/60">{item.quality != null ? `${item.quality}/100` : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
