import type { QualityBreakdown } from "@/lib/types";

function scoreColor(score: number) {
  if (score >= 75) return "text-good";
  if (score >= 50) return "text-warn";
  return "text-bad";
}

export function QualityScore({ quality }: { quality: QualityBreakdown }) {
  const rows: [string, number][] = [
    ["Evidence coverage", quality.evidence_coverage],
    ["Source quality", quality.source_quality],
    ["Source diversity", quality.source_diversity],
    ["Claim support", quality.claim_support],
    ["Citation coverage", quality.citation_coverage],
    ["Contradiction handling", quality.contradiction_handling],
    ["Completeness", quality.completeness],
    ["Freshness", quality.freshness],
  ];

  return (
    <div className="card">
      <div className="flex items-baseline justify-between">
        <h3 className="text-sm font-medium text-white/60">Research Quality</h3>
        <span className={`text-2xl font-semibold ${scoreColor(quality.overall)}`}>{quality.overall}/100</span>
      </div>
      <div className="mt-4 grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
        {rows.map(([label, value]) => (
          <div key={label} className="flex items-center justify-between">
            <span className="text-white/60">{label}</span>
            <span className={scoreColor(value)}>{value}</span>
          </div>
        ))}
      </div>
      {quality.notes.length > 0 && (
        <ul className="mt-4 space-y-1 border-t border-border pt-3 text-xs text-white/50">
          {quality.notes.map((note, i) => (
            <li key={i}>• {note}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
