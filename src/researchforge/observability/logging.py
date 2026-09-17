"""Structured logging.

Every log call is `logger.info(event_name, **fields)` — event-first, not a prose
message — so logs can be shipped as JSON and queried. Never pass secrets: this
module actively redacts common secret-shaped keys as a safety net.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

_REDACT_KEYS = {"api_key", "authorization", "token", "secret", "password"}


class _JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
        }
        extra = getattr(record, "fields", None)
        if extra:
            payload.update(_redact(extra))
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def _redact(fields: dict[str, Any]) -> dict[str, Any]:
    return {k: ("***REDACTED***" if any(s in k.lower() for s in _REDACT_KEYS) else v) for k, v in fields.items()}


class _StructuredLogger:
    """Thin wrapper giving `logger.info("event_name", field=value)` ergonomics."""

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    def _log(self, level: int, event: str, **fields: Any) -> None:
        self._logger.log(level, event, extra={"fields": fields})

    def debug(self, event: str, **fields: Any) -> None:
        self._log(logging.DEBUG, event, **fields)

    def info(self, event: str, **fields: Any) -> None:
        self._log(logging.INFO, event, **fields)

    def warning(self, event: str, **fields: Any) -> None:
        self._log(logging.WARNING, event, **fields)

    def error(self, event: str, **fields: Any) -> None:
        self._log(logging.ERROR, event, **fields)


_CONFIGURED = False


def configure_logging(level: str = "INFO", json_output: bool = True) -> None:
    global _CONFIGURED
    root = logging.getLogger("researchforge")
    root.setLevel(level)
    root.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JSONFormatter() if json_output else logging.Formatter("%(levelname)s %(name)s %(message)s"))
    root.addHandler(handler)
    root.propagate = False
    _CONFIGURED = True


def get_logger(name: str) -> _StructuredLogger:
    if not _CONFIGURED:
        configure_logging()
    return _StructuredLogger(logging.getLogger(name))
