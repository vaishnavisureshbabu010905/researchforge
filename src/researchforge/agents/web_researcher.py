"""Web Research Agent: general web information and primary sources."""

from __future__ import annotations

from researchforge.agents.researcher import ResearcherAgent


class WebResearchAgent(ResearcherAgent):
    role = "web_researcher"
    query_suffix = ""
