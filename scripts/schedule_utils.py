#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEDULE_PATH = ROOT / 'config' / 'schedule.json'
WEEKDAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']


def load_schedule() -> dict:
    return json.loads(SCHEDULE_PATH.read_text(encoding='utf-8'))


def resolve_rule(date_text: str) -> tuple[str, dict]:
    date = datetime.strptime(date_text, '%Y-%m-%d')
    weekday = WEEKDAYS[date.weekday()]
    data = load_schedule()
    defaults = data.get('defaults', {})
    rule = dict(defaults)
    rule.update(data.get('weekday_rules', {}).get(weekday, {}))
    return weekday, rule
