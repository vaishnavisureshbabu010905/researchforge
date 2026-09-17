"use client";

import { useState } from "react";
import type { Evidence } from "@/lib/types";

function credibilityColor(score: number) {
  if (score >= 70) return "text-good";
  if (score >= 40) return "text-warn";
  return "text-bad";
}

export function EvidenceList({ evidence }: { evidence: Evidence[] }) {
  const [expanded, setExpanded] = useState<string | null>(null);
  const domains = new Set(evidence.map((e) => e.domain));

  if (evidence.length === 0) {
    return <p className="text-sm text-white/50">No sources collected yet.</p>;
  }

  return (
    <div>
      <p className="mb-3 text-xs text-white/40">
        {evidence.length} source{evidence.length !== 1 ? "s" : ""} across {domains.size} distinct domain
        {domains.size !== 1 ? "s" : ""}
      </p>
      <ul className="space-y-2">
        {evidence.map((e) => (
          <li key={e.evidence_id} className="rounded-lg border border-border bg-black/20 p-3">
            <button
              className="flex w-full items-start justify-between gap-4 text-left"
              onClick={() => setExpanded(expanded === e.evidence_id ? null : e.evidence_id)}
            >
              <div>
                <a
                  href={e.url}
                  target="_blank"
                  rel="noreferrer"
                  onClick={(ev) => ev.stopPropagation()}
                  className="text-sm font-medium text-white hover:text-accent"
                >
                  {e.title}
                </a>
                <p className="mt-0.5 text-xs text-white/40">
                  {e.domain} · {e.source_type.replace(/_/g, " ")}
                </p>
              </div>
              <span className={`shrink-0 text-sm font-medium ${credibilityColor(e.credibility.score)}`}>
                {e.credibility.score}/100
              </span>
            </button>
            {expanded === e.evidence_id && (
              <div className="mt-3 border-t border-border pt-3 text-xs text-white/60">
                <p className="mb-2">{e.summary}</p>
                <p className="font-medium text-white/40">Credibility factors:</p>
                <ul className="mt-1 list-inside list-disc space-y-0.5">
                  {e.credibility.reasons.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
