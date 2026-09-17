"use client";

import type { ResearchEvent } from "@/lib/types";

const ICONS: Record<string, string> = {
  research_started: "\u25B6", // ▶
  plan_created: "\u{1F5FA}", // 🗺
  task_started: "\u2699", // ⚙
  source_found: "\u{1F310}", // 🌐
  evidence_added: "\u{1F4DA}", // 📚
  claim_extracted: "\u{1F4CC}", // 📌
  research_gap_detected: "\u26A0", // ⚠
  research_iteration_started: "\u{1F501}", // 🔁
  synthesis_started: "\u270D", // ✍
  citation_validation: "\u2705", // ✅
  quality_evaluation: "\u{1F4CA}", // 📊
  research_completed: "\u{1F3C1}", // 🏁
  research_failed: "\u274C", // ❌
  task_failed: "\u274C",
};

function icon(type: string) {
  return ICONS[type] ?? "\u2022"; // •
}

export function EventTimeline({ events }: { events: ResearchEvent[] }) {
  if (events.length === 0) {
    return <p className="text-sm text-white/50">Waiting for the research job to start…</p>;
  }

  return (
    <ol className="max-h-96 space-y-2 overflow-y-auto pr-2">
      {[...events].reverse().map((e) => (
        <li key={e.event_id} className="flex items-start gap-3 text-sm">
          <span className="mt-0.5 w-5 shrink-0 text-center">{icon(e.event_type)}</span>
          <div className="min-w-0">
            <p className="truncate text-white/85">{e.message}</p>
            <p className="text-[11px] uppercase tracking-wide text-white/30">
              {e.event_type.replace(/_/g, " ")} · {new Date(e.timestamp).toLocaleTimeString()}
            </p>
          </div>
        </li>
      ))}
    </ol>
  );
}
