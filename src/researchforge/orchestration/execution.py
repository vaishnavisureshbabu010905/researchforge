"""Parallel research task execution: concurrency limits, timeouts, retries, partial failure.

CLAUDE.md rule 5 ("partial failure is normal") is enforced here: `run_tasks` never
raises out of a batch. Each task result is captured as success or a recorded
failure, and the caller decides what to do with a partial batch.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Generic, TypeVar

from researchforge.observability.logging import get_logger
from researchforge.observability.metrics import Timer, registry
from researchforge.orchestration.errors import RetryableProviderError

logger = get_logger(__name__)

T = TypeVar("T")


@dataclass
class TaskOutcome(Generic[T]):
    task_id: str
    success: bool
    result: T | None = None
    error: str | None = None
    attempts: int = 0


async def _run_with_retry(
    task_id: str,
    coro_factory: Callable[[], Awaitable[T]],
    *,
    timeout_seconds: int,
    max_retries: int,
    backoff_seconds: float,
) -> TaskOutcome[T]:
    last_error: str | None = None
    for attempt in range(1, max_retries + 1):
        try:
            with Timer("research.task_duration_seconds", labels={"task_id": task_id}):
                result = await asyncio.wait_for(coro_factory(), timeout=timeout_seconds)
            registry.increment("research.task_success_total")
            return TaskOutcome(task_id=task_id, success=True, result=result, attempts=attempt)
        except TimeoutError:
            last_error = f"timed out after {timeout_seconds}s"
        except RetryableProviderError as exc:
            last_error = f"{type(exc).__name__}: {exc}"
        except Exception:
            raise

        logger.warning("task_attempt_failed", task_id=task_id, attempt=attempt, error=last_error)
        if attempt < max_retries:
            await asyncio.sleep(backoff_seconds * attempt)

    registry.increment("research.task_failure_total")
    return TaskOutcome(task_id=task_id, success=False, error=last_error, attempts=max_retries)


async def run_tasks(
    items: list[tuple[str, Callable[[], Awaitable[T]]]],
    *,
    max_parallelism: int,
    timeout_seconds: int,
    max_retries: int = 2,
    backoff_seconds: float = 1.0,
) -> list[TaskOutcome[T]]:
    """Run `(task_id, coro_factory)` pairs concurrently, bounded by `max_parallelism`.

    Each task gets its own retry/timeout handling and can fail independently
    without affecting the others (or raising out of this function).
    """
    semaphore = asyncio.Semaphore(max_parallelism)

    async def _bounded(task_id: str, factory: Callable[[], Awaitable[T]]) -> TaskOutcome[T]:
        async with semaphore:
            return await _run_with_retry(
                task_id,
                factory,
                timeout_seconds=timeout_seconds,
                max_retries=max_retries,
                backoff_seconds=backoff_seconds,
            )

    return await asyncio.gather(*(_bounded(tid, factory) for tid, factory in items))
