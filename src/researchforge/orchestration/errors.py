"""Exceptions used to classify transient provider failures separately from programming bugs."""

from __future__ import annotations


class RetryableProviderError(Exception):
    """A transient provider/transport failure that is safe to retry."""
