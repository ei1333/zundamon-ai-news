#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EpisodeTag:
    label: str
    css_class: str


@dataclass
class EpisodeItem:
    headline: str
    summary: str
    source_name: str
    source_url: str
    category: str
    category_class: str
    tags: list[EpisodeTag] = field(default_factory=list)
    script: str = ''


@dataclass
class EpisodeHeader:
    title: str
    theme: str
    coverage: str
    window: str
    summary: str
    intro: str
    script_intro: str
    script_closing: str
    closing: str


@dataclass
class EpisodeDocument:
    header: EpisodeHeader
    items: list[EpisodeItem]
