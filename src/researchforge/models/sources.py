"""Source-related enums shared across evidence, claims, and reports."""

from __future__ import annotations

from enum import StrEnum


class SourceType(StrEnum):
    """What kind of thing a piece of evidence came from.

    Used by the credibility scorer (see evidence/credibility.py) as its primary
    signal — primary/official sources are weighted well above secondary commentary.
    """

    PRIMARY_DOCUMENTATION = "primary_documentation"  # official docs, standards, specs
    ACADEMIC_PAPER = "academic_paper"
    CODE_REPOSITORY = "code_repository"
    NEWS_ARTICLE = "news_article"
    ENGINEERING_BLOG = "engineering_blog"
    FORUM_DISCUSSION = "forum_discussion"
    GENERAL_WEB = "general_web"
    UNKNOWN = "unknown"


class ResearchDomain(StrEnum):
    """Which specialized agent a research task/source belongs to."""

    WEB = "web"
    TECHNICAL = "technical"
    ACADEMIC = "academic"
