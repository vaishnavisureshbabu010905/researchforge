"""Formats the evidence/source list for report rendering."""

from __future__ import annotations

from researchforge.models.evidence import Evidence


def format_sources_section(evidence: list[Evidence]) -> str:
    if not evidence:
        return "## Sources\n\n(no sources retrieved)"

    lines = ["## Sources", ""]
    for i, e in enumerate(evidence, start=1):
        date = e.publication_date.strftime("%Y-%m-%d") if e.publication_date else "date unknown"
        lines.append(
            f"{i}. [{e.title}]({e.url}) — {e.domain}, {date}, "
            f"credibility {e.credibility.score}/100 ({e.source_type.value})"
        )
    return "\n".join(lines)
