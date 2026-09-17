"""Academic Research Agent: papers, institutional sources, scientific evidence."""

from __future__ import annotations

from researchforge.agents.researcher import ResearcherAgent


class AcademicResearchAgent(ResearcherAgent):
    role = "academic_researcher"
    query_suffix = "research paper study arxiv peer-reviewed"
