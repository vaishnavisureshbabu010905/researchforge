import type { ResearchJobStatus } from "@/lib/types";

const STEPS: ResearchJobStatus[] = [
  "planning",
  "researching",
  "analyzing",
  "synthesizing",
  "validating",
  "completed",
];

export function ProgressSteps({ status }: { status: ResearchJobStatus }) {
  if (status === "failed") {
    return <p className="text-sm text-bad">Research failed — see the event timeline for details.</p>;
  }

  // "iterating" and "partial" map onto nearby steps for display purposes.
  const effectiveStatus = status === "iterating" ? "researching" : status === "partial" ? "completed" : status;
  const currentIndex = STEPS.indexOf(effectiveStatus);

  return (
    <div className="flex items-center gap-1">
      {STEPS.map((step, i) => (
        <div key={step} className="flex flex-1 items-center gap-1">
          <div
            className={`h-1.5 flex-1 rounded-full ${
              i < currentIndex ? "bg-good" : i === currentIndex ? "bg-accent" : "bg-white/10"
            }`}
            title={step}
          />
        </div>
      ))}
    </div>
  );
}
