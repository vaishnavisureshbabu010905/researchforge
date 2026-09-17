import type { ResearchPlan } from "@/lib/types";
import { StatusBadge } from "./StatusBadge";

const DOMAIN_LABEL: Record<string, string> = { web: "Web", technical: "Technical", academic: "Academic" };

export function ResearchPlanView({ plan }: { plan: ResearchPlan | null }) {
  if (!plan) {
    return <p className="text-sm text-white/50">The research plan will appear once planning completes.</p>;
  }

  return (
    <div>
      <p className="mb-3 text-sm text-white/70">{plan.objective}</p>
      <ul className="space-y-2">
        {plan.tasks.map((t) => (
          <li key={t.task_id} className="flex items-center justify-between gap-3 rounded-lg border border-border bg-black/20 p-3">
            <div className="min-w-0">
              <p className="truncate text-sm text-white/90">{t.subquestion}</p>
              <p className="text-xs text-white/40">
                {DOMAIN_LABEL[t.domain] ?? t.domain} agent
                {t.iteration > 0 ? ` · follow-up (iteration ${t.iteration})` : ""}
              </p>
            </div>
            <StatusBadge status={t.status} />
          </li>
        ))}
      </ul>
    </div>
  );
}
