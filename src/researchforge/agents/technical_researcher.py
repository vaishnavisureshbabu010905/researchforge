"""Technical Research Agent: GitHub, docs, engineering blogs, benchmarks, implementation details."""

from __future__ import annotations

from researchforge.agents.researcher import ResearcherAgent


class TechnicalResearchAgent(ResearcherAgent):
    role = "technical_researcher"
    query_suffix = "implementation architecture benchmark github documentation"
