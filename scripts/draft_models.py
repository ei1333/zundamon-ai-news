#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class DraftItem:
    headline: str
    summary: str
    source_name: str
    url: str
    category: str
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass
class ResolvedDraftContext:
    date: str
    theme_name: str
    coverage: str
    window: str
    draft_theme: dict[str, object]
    default_categories: list[str]
    category_rules: list[tuple[str, list[str]]]
    tag_rules: list[tuple[str, list[str]]]
