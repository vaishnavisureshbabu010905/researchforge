"use client";

import type { ResearchMode } from "@/lib/types";

const MODES: { value: ResearchMode; label: string; description: string }[] = [
  { value: "quick", label: "Quick", description: "Fast, fewer agents, lower latency. Good for simple questions." },
  { value: "deep", label: "Deep", description: "Specialized agents, verification, synthesis. Recommended default." },
  { value: "exhaustive", label: "Exhaustive", description: "Deeper decomposition, more iterations, strongest source diversity." },
];

export function ModeSelector({
  value,
  onChange,
  disabled,
}: {
  value: ResearchMode;
  onChange: (mode: ResearchMode) => void;
  disabled?: boolean;
}) {
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
      {MODES.map((m) => (
        <button
          key={m.value}
          type="button"
          disabled={disabled}
          onClick={() => onChange(m.value)}
          className={`rounded-lg border p-4 text-left transition disabled:cursor-not-allowed disabled:opacity-50 ${
            value === m.value ? "border-accent bg-accent/10" : "border-border bg-black/20 hover:border-white/30"
          }`}
        >
          <p className={`text-sm font-medium ${value === m.value ? "text-accent" : "text-white"}`}>{m.label}</p>
          <p className="mt-1 text-xs text-white/50">{m.description}</p>
        </button>
      ))}
    </div>
  );
}
