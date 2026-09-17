"""In-process metrics collection.

Deliberately simple (a thread-safe counter/histogram store) rather than wiring a
full Prometheus client, to keep the dependency surface small; the interface is
narrow enough to swap in `prometheus_client` later without touching call sites.
"""

from __future__ import annotations

import threading
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class MetricsSnapshot:
    counters: dict[str, float]
    histograms: dict[str, list[float]]


class MetricsRegistry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: dict[str, float] = defaultdict(float)
        self._histograms: dict[str, list[float]] = defaultdict(list)

    def increment(self, name: str, value: float = 1.0, **labels: str) -> None:
        key = self._key(name, labels)
        with self._lock:
            self._counters[key] += value

    def observe(self, name: str, value: float, **labels: str) -> None:
        key = self._key(name, labels)
        with self._lock:
            self._histograms[key].append(value)

    def snapshot(self) -> MetricsSnapshot:
        with self._lock:
            return MetricsSnapshot(counters=dict(self._counters), histograms=dict(self._histograms))

    @staticmethod
    def _key(name: str, labels: dict[str, str]) -> str:
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"


registry = MetricsRegistry()


@dataclass
class Timer:
    """Usage: `with Timer("research.task_duration_seconds", domain="web") as t: ...`"""

    name: str
    labels: dict[str, str] = field(default_factory=dict)
    _start: float = 0.0

    def __enter__(self) -> "Timer":
        import time

        self._start = time.monotonic()
        return self

    def __exit__(self, *exc: object) -> None:
        import time

        registry.observe(self.name, time.monotonic() - self._start, **self.labels)
