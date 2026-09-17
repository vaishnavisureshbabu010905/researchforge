// Mirrors src/researchforge/models/*.py and api/schemas.py.
// Kept as one file since the frontend intentionally consumes the API's JSON
// shape directly rather than generating a client — see docs/PROGRESS.md for
// why (no codegen pipeline was set up in this pass).

export type ResearchMode = "quick" | "deep" | "exhaustive";

export type ResearchJobStatus =
  | "pending"
  | "planning"
  | "researching"
  | "analyzing"
  | "iterating"
  | "synthesizing"
  | "validating"
  | "completed"
  | "partial"
  | "failed";

export interface ResearchTask {
  task_id: string;
  subquestion: string;
  domain: "web" | "technical" | "academic";
  priority: number;
  status: string;
  iteration: number;
  error?: string | null;
}

export interface ResearchPlan {
  plan_id: string;
  objective: string;
  subquestions: string[];
  required_domains: string[];
  tasks: ResearchTask[];
  iteration: number;
}

export interface CredibilityAssessment {
  score: number;
  reasons: string[];
}

export interface Evidence {
  evidence_id: string;
  title: string;
  url: string;
  domain: string;
  source_type: string;
  research_domain: string;
  extracted_content: string;
  summary: string;
  relevance_score: number;
  credibility: CredibilityAssessment;
  publication_date: string | null;
  retrieved_at: string;
  research_task_id: string;
  supporting_claim_ids: string[];
  metadata: Record<string, string>;
}

export type ClaimStatus = "supported" | "partially_supported" | "conflicting" | "unsupported";

export interface Claim {
  claim_id: string;
  text: string;
  kind: "fact" | "inference" | "opinion" | "recommendation";
  importance: number;
  status: ClaimStatus;
  confidence: number;
  supporting_evidence_ids: string[];
  conflicting_evidence_ids: string[];
  citation_ids: string[];
  research_task_id: string | null;
}

export interface QualityBreakdown {
  overall: number;
  evidence_coverage: number;
  source_quality: number;
  source_diversity: number;
  claim_support: number;
  citation_coverage: number;
  contradiction_handling: number;
  completeness: number;
  freshness: number;
  recommend_another_iteration: boolean;
  notes: string[];
}

export interface CitationValidation {
  total_citations: number;
  valid_citations: number;
  invalid_citation_refs: string[];
  coverage_percent: number;
}

export interface ResearchReport {
  report_id: string;
  research_id: string;
  query: string;
  executive_summary: string;
  methodology: string;
  key_findings: string[];
  detailed_analysis: string;
  limitations: string[];
  confidence_assessment: string;
  claims: Claim[];
  evidence: Evidence[];
  citation_validation: CitationValidation;
  quality: QualityBreakdown;
  generated_at: string;
}

export interface ResearchStatus {
  research_id: string;
  query: string;
  mode: ResearchMode;
  status: ResearchJobStatus;
  iteration_count: number;
  plan: ResearchPlan | null;
  error: string | null;
}

export interface ResearchEvent {
  event_id: string;
  research_id: string;
  event_type: string;
  message: string;
  data: Record<string, unknown>;
  timestamp: string;
}

export interface HistoryItem {
  research_id: string;
  query: string;
  mode: ResearchMode;
  status: string;
  quality: number | null;
}
