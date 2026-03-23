#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class ResolvedSchedule:
    date: str
    weekday: str
    theme: str
    coverage: str
    window: str | None = None
    speaker: str = 'zundamon'
    site_theme: str = 'ai'

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
