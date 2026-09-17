# ResearchForge Frontend

Next.js 14 (App Router) + TypeScript + Tailwind. Talks directly to the FastAPI
backend's REST + SSE endpoints (see `src/lib/api.ts`) — no BFF layer.

## Pages

- `/` — dashboard: start new research (query + mode selector), recent jobs
- `/research/[id]` — live workspace: progress, plan, agent activity, event
  timeline, sources, claims, ad-hoc claim verification, and the final report
  once synthesis completes
- `/history` — full research history with mode filtering

## Development

```bash
npm install
npm run dev       # http://localhost:3000, expects the backend on :8000
```

Set `NEXT_PUBLIC_API_BASE_URL` (see `.env.example` at the repo root) if the
backend isn't on the default `http://localhost:8000`.

## Notes

- Not built/executed in the authoring sandbox (no npm registry access there) —
  see `docs/PROGRESS.md` for what was and wasn't verified.
- No component library beyond Tailwind utility classes; kept dependency-light
  intentionally.
