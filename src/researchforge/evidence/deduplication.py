"""Exact and near-duplicate evidence detection.

Exact duplicates are collapsed by (domain, normalized title). Near-duplicates use
a cheap token-shingle Jaccard similarity over title+summary, which is enough to
catch syndicated/mirrored articles without pulling in an embedding model — see
docs/ARCHITECTURE.md#evidence--claim--citation-pipeline for the rationale.
"""

from __future__ import annotations

import re

from researchforge.models.evidence import Evidence

_NEAR_DUP_THRESHOLD = 0.60


def _shingles(text: str, k: int = 3) -> set[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    if len(tokens) < k:
        return {" ".join(tokens)} if tokens else set()
    return {" ".join(tokens[i : i + k]) for i in range(len(tokens) - k + 1)}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def deduplicate(evidence: list[Evidence]) -> tuple[list[Evidence], int, int]:
    """Returns (deduplicated_list, exact_duplicate_count, near_duplicate_count)."""
    seen_fingerprints: set[str] = set()
    kept: list[Evidence] = []
    kept_shingles: list[set[str]] = []
    exact_dupes = 0
    near_dupes = 0

    for item in evidence:
        fp = item.content_fingerprint()
        if fp in seen_fingerprints:
            exact_dupes += 1
            continue

        shingles = _shingles(f"{item.title} {item.summary}")
        is_near_dup = False
        for existing_shingles in kept_shingles:
            if _jaccard(shingles, existing_shingles) >= _NEAR_DUP_THRESHOLD:
                is_near_dup = True
                break

        if is_near_dup:
            near_dupes += 1
            continue

        seen_fingerprints.add(fp)
        kept.append(item)
        kept_shingles.append(shingles)

    return kept, exact_dupes, near_dupes
