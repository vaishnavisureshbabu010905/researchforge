import type { ResearchReport } from "@/lib/types";
import { QualityScore } from "./QualityScore";
import { EvidenceList } from "./EvidenceList";
import { ClaimList } from "./ClaimList";

export function ReportView({ report }: { report: ResearchReport }) {
  return (
    <div className="space-y-6">
      <div className="card">
        <h2 className="text-sm font-medium text-white/60">Executive Summary</h2>
        <p className="mt-2 text-sm leading-relaxed text-white/90">{report.executive_summary}</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <div className="card">
            <h2 className="text-sm font-medium text-white/60">Key Findings</h2>
            <ul className="mt-3 list-inside list-disc space-y-1.5 text-sm text-white/85">
              {report.key_findings.length > 0 ? (
                report.key_findings.map((f, i) => <li key={i}>{f}</li>)
              ) : (
                <li className="text-white/40">No strongly-supported findings were identified.</li>
              )}
            </ul>
          </div>

          <div className="card">
            <h2 className="text-sm font-medium text-white/60">Detailed Analysis</h2>
            <p className="mt-2 text-sm leading-relaxed text-white/80">{report.detailed_analysis}</p>
          </div>

          <div className="card">
            <h2 className="text-sm font-medium text-white/60">
              Claims <span className="text-white/30">({report.claims.length})</span>
            </h2>
            <div className="mt-3">
              <ClaimList claims={report.claims} />
            </div>
          </div>

          <div className="card">
            <h2 className="text-sm font-medium text-white/60">
              Sources <span className="text-white/30">({report.evidence.length})</span>
            </h2>
            <div className="mt-3">
              <EvidenceList evidence={report.evidence} />
            </div>
          </div>

          <div className="card">
            <h2 className="text-sm font-medium text-white/60">Limitations</h2>
            <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-white/70">
              {report.limitations.length > 0 ? (
                report.limitations.map((l, i) => <li key={i}>{l}</li>)
              ) : (
                <li className="text-white/40">None identified.</li>
              )}
            </ul>
          </div>

          <div className="card">
            <h2 className="text-sm font-medium text-white/60">Confidence Assessment</h2>
            <p className="mt-2 text-sm text-white/80">{report.confidence_assessment}</p>
          </div>
        </div>

        <div className="space-y-6">
          <QualityScore quality={report.quality} />
          <div className="card">
            <h3 className="text-sm font-medium text-white/60">Citation Coverage</h3>
            <p className="mt-2 text-2xl font-semibold text-white">
              {report.citation_validation.coverage_percent.toFixed(0)}%
            </p>
            <p className="mt-1 text-xs text-white/40">
              {report.citation_validation.valid_citations} of {report.citation_validation.total_citations} citations verified
              against retrieved evidence.
            </p>
            {report.citation_validation.invalid_citation_refs.length > 0 && (
              <ul className="mt-3 space-y-1 border-t border-border pt-3 text-xs text-bad">
                {report.citation_validation.invalid_citation_refs.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            )}
          </div>
          <div className="card">
            <h3 className="text-sm font-medium text-white/60">Methodology</h3>
            <p className="mt-2 text-xs leading-relaxed text-white/60">{report.methodology}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
