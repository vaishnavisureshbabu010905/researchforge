"use client";

export default function GlobalError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <div className="card">
      <h1 className="text-lg font-medium text-bad">Something went wrong</h1>
      <p className="mt-2 text-sm text-white/50">{error.message || "An unexpected error occurred."}</p>
      <button onClick={reset} className="mt-4 rounded-md bg-accent px-4 py-2 text-sm text-white">
        Try again
      </button>
    </div>
  );
}
