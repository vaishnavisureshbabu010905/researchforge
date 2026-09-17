from __future__ import annotations

import pytest

from researchforge.orchestration.errors import RetryableProviderError
from researchforge.orchestration.execution import run_tasks


@pytest.mark.asyncio
async def test_timer_labels_are_accepted_and_task_succeeds():
    async def work():
        return "ok"

    outcomes = await run_tasks(
        [("task-1", work)],
        max_parallelism=1,
        timeout_seconds=5,
        max_retries=1,
    )
    assert outcomes[0].success is True
    assert outcomes[0].result == "ok"


@pytest.mark.asyncio
async def test_retryable_provider_error_is_retried():
    attempts = 0

    async def work():
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RetryableProviderError("temporary")
        return "ok"

    outcomes = await run_tasks(
        [("task-1", work)],
        max_parallelism=1,
        timeout_seconds=5,
        max_retries=2,
        backoff_seconds=0,
    )
    assert outcomes[0].success is True
    assert attempts == 2


@pytest.mark.asyncio
async def test_programming_errors_are_not_classified_as_retryable():
    async def work():
        raise TypeError("internal bug")

    with pytest.raises(TypeError, match="internal bug"):
        await run_tasks(
            [("task-1", work)],
            max_parallelism=1,
            timeout_seconds=5,
            max_retries=3,
            backoff_seconds=0,
        )
