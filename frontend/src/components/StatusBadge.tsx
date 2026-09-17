const COLORS: Record<string, string> = {
  pending: "bg-white/10 text-white/70",
  planning: "bg-accent/20 text-accent",
  researching: "bg-accent/20 text-accent",
  analyzing: "bg-accent/20 text-accent",
  iterating: "bg-warn/20 text-warn",
  synthesizing: "bg-accent/20 text-accent",
  validating: "bg-accent/20 text-accent",
  completed: "bg-good/20 text-good",
  partial: "bg-warn/20 text-warn",
  failed: "bg-bad/20 text-bad",
  supported: "bg-good/20 text-good",
  partially_supported: "bg-warn/20 text-warn",
  conflicting: "bg-bad/20 text-bad",
  unsupported: "bg-white/10 text-white/60",
};

export function StatusBadge({ status }: { status: string }) {
  const cls = COLORS[status] ?? "bg-white/10 text-white/70";
  return <span className={`badge ${cls}`}>{status.replace(/_/g, " ")}</span>;
}
