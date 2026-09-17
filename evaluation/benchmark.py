"""Benchmark runner: executes every question in evaluation/datasets/benchmark.json
against a live Orchestrator (mock providers by default) and reports metrics.

Usage:
    python evaluation/benchmark.py                 # mock providers, all questions
    python evaluation/benchmark.py --dataset path/to/custom.json
    python evaluation/benchmark.py --live           # use configured real providers instead of mock
    python evaluation/benchmark.py --output results.json

See evaluation/README.md / docs/EVALUATION.md for interpretation guidance.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from evaluation.metrics import BenchmarkResult, domain_coverage, relevance_score, summarize  # noqa: E402

from researchforge.config.settings import Settings  # noqa: E402
from researchforge.models.research import ResearchJobStatus, ResearchMode  # noqa: E402
from researchforge.orchestration.orchestrator import Orchestrator, new_job  # noqa: E402
from researchforge.orchestration.state import ResearchState  # noqa: E402
from researchforge.providers.llm.mock import MockLLMProvider  # noqa: E402
from researchforge.providers.mock import MockSearchProvider  # noqa: E402


async def run_question(orchestrator: Orchestrator, question: dict) -> BenchmarkResult:
    start = time.monotonic()
    job = new_job(question["query"], mode=ResearchMode(question["mode"]))
    state = ResearchState(job=job)

    try:
        result_state = await orchestrator.run(state)
    except Exception as exc:  # noqa: BLE001 - a single question failing must not crash the benchmark run
        return BenchmarkResult(
            question_id=question["id"],
            category=question["category"],
            query=question["query"],
            mode=question["mode"],
            status="error",
            quality_overall=0,
            evidence_coverage=0,
            source_quality=0,
            source_diversity=0,
            claim_support=0,
            citation_coverage=0,
            contradiction_handling=0,
            completeness=0,
            relevance=0,
            passed_min_quality=False,
            domain_coverage=0.0,
            duration_seconds=round(time.monotonic() - start, 2),
            error=str(exc),
        )

    duration = round(time.monotonic() - start, 2)
    report = result_state.report
    touched_domains = {e.research_domain.value for e in result_state.evidence}
    coverage = domain_coverage(question.get("expected_domains", []), touched_domains)
    relevance = relevance_score(question["query"], [e.summary for e in result_state.evidence])

    if report is None:
        return BenchmarkResult(
            question_id=question["id"],
            category=question["category"],
            query=question["query"],
            mode=question["mode"],
            status=result_state.job.status.value,
            quality_overall=0,
            evidence_coverage=0,
            source_quality=0,
            source_diversity=0,
            claim_support=0,
            citation_coverage=0,
            contradiction_handling=0,
            completeness=0,
            relevance=relevance,
            passed_min_quality=False,
            domain_coverage=coverage,
            duration_seconds=duration,
            error=result_state.job.error,
        )

    q = report.quality
    return BenchmarkResult(
        question_id=question["id"],
        category=question["category"],
        query=question["query"],
        mode=question["mode"],
        status=result_state.job.status.value,
        quality_overall=q.overall,
        evidence_coverage=q.evidence_coverage,
        source_quality=q.source_quality,
        source_diversity=q.source_diversity,
        claim_support=q.claim_support,
        citation_coverage=q.citation_coverage,
        contradiction_handling=q.contradiction_handling,
        completeness=q.completeness,
        relevance=relevance,
        passed_min_quality=q.overall >= question.get("min_quality", 0),
        domain_coverage=coverage,
        duration_seconds=duration,
        error=None if result_state.job.status != ResearchJobStatus.FAILED else result_state.job.error,
    )


async def run_benchmark(dataset_path: Path, *, live: bool) -> list[BenchmarkResult]:
    with open(dataset_path) as f:
        dataset = json.load(f)

    settings = Settings()
    if live:
        from researchforge.providers.factory import get_llm_provider, get_search_provider

        search = get_search_provider(settings)
        llm = get_llm_provider(settings)
    else:
        search = MockSearchProvider()
        llm = MockLLMProvider()

    orchestrator = Orchestrator(settings=settings, search=search, llm=llm)

    results = []
    for question in dataset["questions"]:
        print(f"Running {question['id']} ({question['category']}, {question['mode']})...", file=sys.stderr)
        result = await run_question(orchestrator, question)
        results.append(result)
        status_marker = "PASS" if result.passed_min_quality else "FAIL"
        print(f"  -> {status_marker} quality={result.quality_overall} ({result.duration_seconds}s)", file=sys.stderr)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the ResearchForge evaluation benchmark.")
    parser.add_argument(
        "--dataset", type=Path, default=Path(__file__).parent / "datasets" / "benchmark.json"
    )
    parser.add_argument("--live", action="store_true", help="Use configured real providers instead of mock ones.")
    parser.add_argument("--output", type=Path, default=None, help="Write full JSON results to this path.")
    args = parser.parse_args()

    results = asyncio.run(run_benchmark(args.dataset, live=args.live))
    summary = summarize(results)

    print("\n=== ResearchForge Evaluation Summary ===")
    for key, value in summary.items():
        print(f"{key}: {value}")

    if args.output:
        payload = {"summary": summary, "results": [r.__dict__ for r in results]}
        args.output.write_text(json.dumps(payload, indent=2))
        print(f"\nFull results written to {args.output}")

    if summary.get("pass_rate", 0) < 1.0:
        sys.exit(1)  # non-zero exit if any question failed its min_quality bar, for CI gating if desired


if __name__ == "__main__":
    main()
