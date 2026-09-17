import type {
  Claim,
  Evidence,
  HistoryItem,
  ResearchEvent,
  ResearchMode,
  ResearchReport,
  ResearchStatus,
} from "./types";

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    cache: "no-store",
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? body.error ?? detail;
    } catch {
      // response wasn't JSON; fall back to statusText
    }
    throw new Error(`${res.status} ${detail}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string; search_provider: string; llm_provider: string; version: string }>("/api/health"),

  createResearch: (query: string, mode: ResearchMode) =>
    request<{ research_id: string; status: string; mode: ResearchMode }>("/api/research", {
      method: "POST",
      body: JSON.stringify({ query, mode }),
    }),

  getStatus: (researchId: string) => request<ResearchStatus>(`/api/research/${researchId}/status`),

  getSources: (researchId: string) =>
    request<{ research_id: string; count: number; sources: Evidence[] }>(`/api/research/${researchId}/sources`),

  getClaims: (researchId: string) =>
    request<{ research_id: string; count: number; claims: Claim[] }>(`/api/research/${researchId}/claims`),

  getReport: (researchId: string) => request<{ report: ResearchReport }>(`/api/research/${researchId}/report`),

  getHistory: () => request<{ items: HistoryItem[] }>("/api/research/history"),

  verifyClaim: (claimText: string, researchId?: string) =>
    request<{ claim: Claim }>("/api/claims/verify", {
      method: "POST",
      body: JSON.stringify({ claim_text: claimText, research_id: researchId }),
    }),

  /** Opens an SSE connection to the research event stream. Caller owns the EventSource lifecycle. */
  streamEvents(researchId: string, onEvent: (event: ResearchEvent) => void, onError?: () => void): EventSource {
    const source = new EventSource(`${BASE_URL}/api/research/${researchId}/events`);
    const eventTypes = [
      "research_started",
      "plan_created",
      "task_started",
      "search_started",
      "source_found",
      "source_processed",
      "evidence_added",
      "claim_extracted",
      "claim_verified",
      "research_iteration_started",
      "research_gap_detected",
      "synthesis_started",
      "citation_validation",
      "quality_evaluation",
      "research_completed",
      "research_failed",
      "task_failed",
      "keepalive",
      "research_status",
    ];
    for (const type of eventTypes) {
      source.addEventListener(type, (e) => {
        try {
          const parsed = JSON.parse((e as MessageEvent).data);
          onEvent({ ...parsed, event_type: parsed.event_type ?? type });
        } catch {
          // keepalive / non-JSON frames are safe to ignore
        }
      });
    }
    if (onError) source.onerror = onError;
    return source;
  },
};
