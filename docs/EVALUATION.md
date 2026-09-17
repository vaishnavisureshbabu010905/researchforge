# Evaluation

This document explains what ResearchForge's evaluation system measures, how to
run it, and — importantly — what it does *not* prove. See `evaluation/README.md`
for the quick command reference.

## Two different "evaluation" concepts in this codebase

It's easy to conflate these; they answer different questions.

1. **Live quality scoring** (`src/researchforge/evaluation/evaluator.py`) — runs
   *during* every research job, on that job's own evidence and claims, to decide
   whether to iterate again and to report a quality score to the user. No
   ground truth is available at this point; it scores internal consistency
   (evidence coverage, source diversity, claim support, citation coverage,
   etc.) — see `docs/ARCHITECTURE.md#quality-evaluation`.
2. **Benchmark evaluation** (`evaluation/` at the repo root) — runs *offline*,
   against a small labeled dataset, to check ResearchForge's behavior against
   expectations set in advance (`expected_domains`, `min_quality`) and to give
   a repeatable way to compare behavior across code changes.

## Metrics

From the live quality scorer, reported per question:

| Metric | What it measures |
|---|---|
| `evidence_coverage` | % of extracted claims that have at least one supporting evidence item |
| `source_quality` | average credibility score across all evidence |
| `source_diversity` | how many distinct domains contributed evidence (diminishing returns past 6) |
| `claim_support` | weighted score rewarding SUPPORTED > PARTIALLY_SUPPORTED > CONFLICTING > UNSUPPORTED |
| `citation_coverage` | % of citations in the report that resolve to real, retrieved evidence |
| `contradiction_handling` | % of CONFLICTING claims that actually carry documented conflicting evidence (i.e., conflicts aren't just mislabeled) |
| `completeness` | fraction of planned subquestions that produced at least one claim |
| `freshness` | recency-weighted score over evidence publication dates |

Benchmark-only additions (`evaluation/metrics.py`):

| Metric | What it measures |
|---|---|
| `relevance` | lexical-overlap proxy for whether collected evidence is actually about the query |
| `domain_coverage` | fraction of a question's `expected_domains` that were actually touched by research |
| `pass_rate` | fraction of questions whose `quality_overall` met their `min_quality` bar |

## How to run

```bash
python evaluation/benchmark.py
python evaluation/benchmark.py --output evaluation/results.json
python evaluation/benchmark.py --live   # real providers, costs money, needs API keys
```

## Interpreting results

- A **low pass rate against mock providers** almost always means a pipeline bug
  (e.g. a stage silently producing nothing), not "the AI is bad at research" —
  the mock providers are deterministic and designed to produce enough signal
  for claims/evidence/citations to flow through the whole pipeline.
- A **low pass rate against `--live` providers** is a genuine research-quality
  signal, but still only as good as this benchmark's six questions — treat it
  as a regression smoke test, not a comprehensive quality audit.
- `relevance` and `domain_coverage` are heuristics (lexical overlap, keyword
  domain classification), not semantic judgments. They catch gross failures
  ("research about the wrong topic entirely") far more reliably than they
  distinguish "good" from "great."

## Limitations

- Six questions is a smoke test, not statistically meaningful coverage of "is
  ResearchForge good at research." A real evaluation program would need dozens
  to hundreds of human-graded questions per category.
- There is no human-in-the-loop grading step — `min_quality` thresholds were
  chosen to be achievable by the mock pipeline, not calibrated against human
  judgments of report quality.
- The benchmark runner is **not wired into CI** (`.github/workflows/ci.yml`
  runs the pytest suite only). Running it against `--live` providers costs
  money and takes real wall-clock time, which doesn't belong in every PR; a
  reasonable next step would be a separate, manually-triggered or nightly
  workflow — see README.md#roadmap.
- `relevance_score` and `domain_coverage` are both simple heuristics (see
  `evaluation/metrics.py`); they were not validated against human judgment.
