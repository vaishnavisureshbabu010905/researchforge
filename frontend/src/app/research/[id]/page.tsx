"use client";

import { useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import type { ResearchEvent, ResearchReport, ResearchStatus } from "@/lib/types";
import { StatusBadge } from "@/components/StatusBadge";
import { ProgressSteps } from "@/components/ProgressSteps";
import { EventTimeline } from "@/components/EventTimeline";
import { AgentActivity } from "@/components/AgentActivity";
import { ResearchPlanView } from "@/components/ResearchPlanView";
import { EvidenceList } from "@/components/EvidenceList";
import { ClaimList } from "@/components/ClaimList";
import { ReportView } from "@/components/ReportView";
import { ClaimVerifyBox } from "@/components/ClaimVerifyBox";

const TERMINAL_STATUSES = new Set(["completed", "failed", "partial"]);

type Tab = "overview" | "sources" | "claims" | "report";

export default function ResearchWorkspacePage() {
  const params = useParams<{ id: string }>();
  const researchId = params.id;

  const [status, setStatus] = useState<ResearchStatus | null>(null);
  const [events, setEvents] = useState<ResearchEvent[]>([]);
  const [report, setReport] = useState<ResearchReport | null>(null);
  const [sourceCount, setSourceCount] = useState(0);
  const [claimCount, setClaimCount] = useState(0);
  const [tab, setTab] = useState<Tab>("overview");
  const [notFound, setNotFound] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Initial + polling status fetch (backstops the SSE stream and covers page reloads).
  useEffect(() => {
    let cancelled = false;

    async function poll() {
      try {
        const s = await api.getStatus(researchId);
        if (cancelled) return;
        setStatus(s);
        if (TERMINAL_STATUSES.has(s.status)) {
          if (pollRef.current) clearInterval(pollRef.current);
          if (s.status === "completed") {
            const { report } = await api.getReport(researchId);
            if (!cancelled) setReport(report);
          }
        }
      } catch {
        if (!cancelled) setNotFound(true);
      }
    }

    poll();
    pollRef.current = setInterval(poll, 3000);
    return () => {
      cancelled = true;
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [researchId]);

  // Live SSE stream for the event timeline / agent activity.
  useEffect(() => {
    const source = api.streamEvents(researchId, (event) => {
      setEvents((prev) => (prev.some((e) => e.event_id === event.event_id) ? prev : [...prev, event]));
    });
    return () => source.close();
  }, [researchId]);

  // Lightweight polling for source/claim counts while the job is still in-flight.
  useEffect(() => {
    if (!status || TERMINAL_STATUSES.has(status.status)) return;
    const id = setInterval(async () => {
      try {
        const [sources, claims] = await Promise.all([api.getSources(researchId), api.getClaims(researchId)]);
        setSourceCount(sources.count);
        setClaimCount(claims.count);
      } catch {
        // job may not have produced evidence/claims yet — ignore transient errors
      }
    }, 2500);
    return () => clearInterval(id);
  }, [status, researchId]);

  if (notFound) {
    return (
      <div className="card">
        <p className="text-sm text-white/70">No research job found with id <code>{researchId}</code>.</p>
        <a href="/" className="mt-3 inline-block text-sm text-accent hover:underline">
          Start a new research question
        </a>
      </div>
    );
  }

  if (!status) {
    return <p className="text-sm text-white/40">Loading research job…</p>;
  }

  const isRunning = !TERMINAL_STATUSES.has(status.status);

  return (
    <div className="space-y-6">
      <div className="card">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="truncate text-lg font-medium text-white">{status.query}</p>
            <p className="mt-1 text-xs text-white/40">
              {status.mode} mode · iteration {status.iteration_count}
            </p>
          </div>
          <StatusBadge status={status.status} />
        </div>
        <div className="mt-4">
          <ProgressSteps status={status.status} />
        </div>
        {status.error && <p className="mt-3 text-sm text-bad">{status.error}</p>}
      </div>

      <div className="flex gap-2 border-b border-border">
        {(["overview", "sources", "claims", "report"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-3 py-2 text-sm capitalize transition ${
              tab === t ? "border-b-2 border-accent text-white" : "text-white/40 hover:text-white/70"
            }`}
          >
            {t}
            {t === "sources" && sourceCount > 0 && ` (${sourceCount})`}
            {t === "claims" && claimCount > 0 && ` (${claimCount})`}
          </button>
        ))}
      </div>

      {tab === "overview" && (
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="space-y-6 lg:col-span-2">
            <div className="card">
              <h3 className="mb-3 text-sm font-medium text-white/60">Research Plan</h3>
              <ResearchPlanView plan={status.plan} />
            </div>
            <div className="card">
              <h3 className="mb-3 text-sm font-medium text-white/60">Event Timeline</h3>
              <EventTimeline events={events} />
            </div>
          </div>
          <div className="space-y-6">
            <div className="card">
              <h3 className="mb-3 text-sm font-medium text-white/60">Agent Activity</h3>
              <AgentActivity events={events} />
            </div>
            {isRunning && (
              <div className="card">
                <p className="text-sm text-white/60">
                  Research in progress — sources and claims will appear as they&apos;re collected. This page updates live.
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {tab === "sources" && (
        <div className="card">
          <SourcesTab researchId={researchId} />
        </div>
      )}

      {tab === "claims" && (
        <div className="space-y-6">
          <div className="card">
            <ClaimsTab researchId={researchId} />
          </div>
          <ClaimVerifyBox researchId={researchId} />
        </div>
      )}

      {tab === "report" &&
        (report ? (
          <ReportView report={report} />
        ) : (
          <div className="card">
            <p className="text-sm text-white/50">
              {isRunning
                ? "The final report will appear here once synthesis and validation complete."
                : "No report is available for this job (it may have failed before synthesis)."}
            </p>
          </div>
        ))}
    </div>
  );
}

function SourcesTab({ researchId }: { researchId: string }) {
  const [sources, setSources] = useState<Awaited<ReturnType<typeof api.getSources>> | null>(null);
  useEffect(() => {
    let active = true;
    const load = () => api.getSources(researchId).then((r) => active && setSources(r)).catch(() => {});
    load();
    const id = setInterval(load, 3000);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, [researchId]);

  if (!sources) return <p className="text-sm text-white/40">Loading sources…</p>;
  return <EvidenceList evidence={sources.sources} />;
}

function ClaimsTab({ researchId }: { researchId: string }) {
  const [claims, setClaims] = useState<Awaited<ReturnType<typeof api.getClaims>> | null>(null);
  useEffect(() => {
    let active = true;
    const load = () => api.getClaims(researchId).then((r) => active && setClaims(r)).catch(() => {});
    load();
    const id = setInterval(load, 3000);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, [researchId]);

  if (!claims) return <p className="text-sm text-white/40">Loading claims…</p>;
  return <ClaimList claims={claims.claims} />;
}
