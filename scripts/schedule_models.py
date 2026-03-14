#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class ResolvedSchedule:
    date: str
    weekday: str
    theme: str
    coverage: str
    window: str | None = None
    speaker: str = 'zundamon'
    site_theme: str = 'ai'
    source_suggestions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
