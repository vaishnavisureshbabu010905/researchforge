# ResearchForge Evaluation

A small, labeled benchmark for exercising ResearchForge end-to-end and tracking
quality over time. See `docs/EVALUATION.md` for the metric definitions and how
to interpret results; this file is the "how to run it" quick reference.

## Running

```bash
# From the repo root, with the package installed (`pip install -e .`):
python evaluation/benchmark.py

# Write full per-question results to a file:
python evaluation/benchmark.py --output evaluation/results.json

# Against a custom dataset:
python evaluation/benchmark.py --dataset path/to/my_questions.json

# Against real configured providers instead of mocks (costs money / needs API keys):
python evaluation/benchmark.py --live
```

By default the benchmark runs entirely against `MockSearchProvider` +
`MockLLMProvider`, so it requires no API keys and is deterministic — this is the
mode CI would use if evaluation were wired into the pipeline (it currently is
not; see docs/EVALUATION.md limitations).

## Dataset

`datasets/benchmark.json` — six questions spanning the categories called for in
the project spec: technology comparison, product comparison, a scientific
question, a historical question, a software-architecture question, and a
current-events-style question. Each entry has:

```json
{
  "id": "tech-comparison-1",
  "category": "technology_comparison",
  "query": "...",
  "mode": "deep",
  "expected_domains": ["technical", "web"],
  "min_quality": 40
}
```

`expected_domains` and `min_quality` are the only "ground truth" — this is a
smoke-test-and-regression benchmark, not a human-graded correctness benchmark
(see docs/EVALUATION.md for why that distinction matters).

## Output

The runner prints a per-question pass/fail line as it goes, then a summary:

```
=== ResearchForge Evaluation Summary ===
count: 6
pass_rate: 1.0
avg_quality_overall: 52.3
avg_evidence_coverage: 61.0
...
```

`--output` additionally writes the full per-question `BenchmarkResult` records
as JSON for later analysis or diffing between runs (e.g. before/after a change
to the credibility scorer).

## Adding a question

Append an entry to `datasets/benchmark.json` with a unique `id`. Keep queries
specific enough that the mock provider's deterministic (but generic) content
still produces a meaningful signal — see `providers/mock.py` for how mock
content is generated.
