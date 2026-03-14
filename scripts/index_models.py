#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class IndexThemeFilter:
    theme_name: str
    label: str


@dataclass
class IndexEpisodeTagSummary:
    headline: str
    category_label: str
    category_class: str
    tags: list[dict[str, str]] = field(default_factory=list)


@dataclass
class IndexEpisodeSummary:
    date: str
    title: str
    summary: str
    coverage: str
    window: str
    theme_name: str
    theme_label: str
    items: list[IndexEpisodeTagSummary] = field(default_factory=list)


@dataclass
class IndexViewModel:
    site_theme_name: str
    hero_eyebrow: str
    hero_title: str
    hero_lead: str
    recent_heading: str
    backnumber_heading: str
    credits_heading: str
    credits_voice: str
    featured_episode: IndexEpisodeSummary
    recent_episodes: list[IndexEpisodeSummary] = field(default_factory=list)
    all_episodes: list[IndexEpisodeSummary] = field(default_factory=list)
    theme_filters: list[IndexThemeFilter] = field(default_factory=list)
