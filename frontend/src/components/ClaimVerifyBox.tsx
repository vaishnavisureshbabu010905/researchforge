"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import type { Claim } from "@/lib/types";
import { StatusBadge } from "./StatusBadge";

export function ClaimVerifyBox({ researchId }: { researchId?: string }) {
  const [text, setText] = useState("");
  const [result, setResult] = useState<Claim | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleVerify() {
    if (!text.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const { claim } = await api.verifyClaim(text.trim(), researchId);
      setResult(claim);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Verification failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card">
      <h3 className="text-sm font-medium text-white/60">Verify a Claim</h3>
      <p className="mt-1 text-xs text-white/40">
        {researchId
          ? "Checked against this research job's evidence pool."
          : "No research selected — runs a fresh, lightweight search."}
      </p>
      <div className="mt-3 flex gap-2">
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="e.g. Rust has a borrow checker"
          className="flex-1 rounded-md border border-border bg-black/30 px-3 py-2 text-sm outline-none focus:border-accent"
          onKeyDown={(e) => e.key === "Enter" && handleVerify()}
        />
        <button
          onClick={handleVerify}
          disabled={loading || !text.trim()}
          className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {loading ? "Checking…" : "Verify"}
        </button>
      </div>
      {error && <p className="mt-2 text-xs text-bad">{error}</p>}
      {result && (
        <div className="mt-3 rounded-lg border border-border bg-black/20 p-3">
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm text-white/90">{result.text}</p>
            <StatusBadge status={result.status} />
          </div>
          <p className="mt-2 text-xs text-white/40">
            confidence {(result.confidence * 100).toFixed(0)}% · {result.supporting_evidence_ids.length} supporting ·{" "}
            {result.conflicting_evidence_ids.length} conflicting
          </p>
        </div>
      )}
    </div>
  );
}
