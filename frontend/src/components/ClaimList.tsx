"use client";

import { useState } from "react";
import type { Claim, ClaimStatus } from "@/lib/types";
import { StatusBadge } from "./StatusBadge";

const FILTERS: (ClaimStatus | "all")[] = ["all", "supported", "partially_supported", "conflicting", "unsupported"];

export function ClaimList({ claims }: { claims: Claim[] }) {
  const [filter, setFilter] = useState<ClaimStatus | "all">("all");
  const visible = filter === "all" ? claims : claims.filter((c) => c.status === filter);

  if (claims.length === 0) {
    return <p className="text-sm text-white/50">No claims extracted yet.</p>;
  }

  return (
    <div>
      <div className="mb-3 flex flex-wrap gap-2">
        {FILTERS.map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`rounded-full border px-3 py-1 text-xs transition ${
              filter === f ? "border-accent bg-accent/10 text-accent" : "border-border text-white/50 hover:text-white"
            }`}
          >
            {f === "all" ? `All (${claims.length})` : `${f.replace(/_/g, " ")} (${claims.filter((c) => c.status === f).length})`}
          </button>
        ))}
      </div>
      <ul className="space-y-2">
        {visible.map((c) => (
          <li key={c.claim_id} className="rounded-lg border border-border bg-black/20 p-3">
            <div className="flex items-start justify-between gap-3">
              <p className="text-sm text-white/90">{c.text}</p>
              <StatusBadge status={c.status} />
            </div>
            <div className="mt-2 flex items-center gap-4 text-xs text-white/40">
              <span>confidence {(c.confidence * 100).toFixed(0)}%</span>
              <span>{c.supporting_evidence_ids.length} supporting</span>
              {c.conflicting_evidence_ids.length > 0 && (
                <span className="text-bad">{c.conflicting_evidence_ids.length} conflicting</span>
              )}
              <span className="italic">{c.kind}</span>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
