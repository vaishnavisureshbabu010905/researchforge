import type { ResearchEvent } from "@/lib/types";

const AGENT_LABELS: Record<string, string> = {
  web: "Web Research Agent",
  technical: "Technical Research Agent",
  academic: "Academic Research Agent",
};

/** Derives a simple "what is each agent doing right now" view from the raw event
 * stream, rather than requiring a separate backend endpoint for it. */
export function AgentActivity({ events }: { events: ResearchEvent[] }) {
  const active = new Map<string, string>();

  for (const e of events) {
    if (e.event_type === "task_started" && typeof e.data.domain === "string") {
      active.set(e.data.domain, "researching");
    }
    if (e.event_type === "task_failed" && typeof e.data.task_id === "string") {
      // best-effort: we don't have the domain on failure events, so leave as-is
    }
    if (e.event_type === "synthesis_started") active.set("synthesizer", "synthesizing report");
    if (e.event_type === "citation_validation") active.set("citation_validator", "validating citations");
    if (e.event_type === "quality_evaluation") active.set("quality_evaluator", "scoring quality");
    if (e.event_type === "plan_created") active.set("planner", "plan created");
    if (e.event_type === "research_completed" || e.event_type === "research_failed") active.clear();
  }

  const entries = Array.from(active.entries());
  if (entries.length === 0) {
    return <p className="text-sm text-white/50">No agents currently active.</p>;
  }

  return (
    <ul className="space-y-2">
      {entries.map(([agent, activity]) => (
        <li key={agent} className="flex items-center gap-2 text-sm">
          <span className="h-2 w-2 shrink-0 animate-pulse rounded-full bg-accent" />
          <span className="text-white/80">{AGENT_LABELS[agent] ?? agent}</span>
          <span className="text-white/40">— {activity}</span>
        </li>
      ))}
    </ul>
  );
}
