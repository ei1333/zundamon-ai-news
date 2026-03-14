#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class IndexThemeFilter:
    theme_name: str
    label: str


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
    featured_episode: dict[str, object]
    recent_episodes: list[dict[str, object]] = field(default_factory=list)
    all_episodes: list[dict[str, object]] = field(default_factory=list)
    theme_filters: list[IndexThemeFilter] = field(default_factory=list)
