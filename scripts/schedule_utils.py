#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from episode_utils import default_window_for
from schedule_models import ResolvedSchedule

ROOT = Path(__file__).resolve().parent.parent
SCHEDULE_PATH = ROOT / 'config' / 'schedule.json'
WEEKDAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']


def validate_schedule_config(data: dict) -> dict:
    if not isinstance(data, dict):
        raise SystemExit('schedule.json must be an object')
    if 'defaults' not in data or 'weekday_rules' not in data:
        raise SystemExit('schedule.json must contain defaults and weekday_rules')
    if not isinstance(data.get('defaults'), dict):
        raise SystemExit('schedule.json defaults must be an object')
    if not isinstance(data.get('weekday_rules'), dict):
        raise SystemExit('schedule.json weekday_rules must be an object')
    for weekday, rule in data['weekday_rules'].items():
        if weekday not in WEEKDAYS:
            raise SystemExit(f'schedule.json has unknown weekday: {weekday}')
        if not isinstance(rule, dict):
            raise SystemExit(f'schedule.json weekday_rules.{weekday} must be an object')
        if 'source_suggestions' in rule and not isinstance(rule.get('source_suggestions'), list):
            raise SystemExit(f'schedule.json weekday_rules.{weekday}.source_suggestions must be a list')
    return data


def load_schedule() -> dict:
    return validate_schedule_config(json.loads(SCHEDULE_PATH.read_text(encoding='utf-8')))


def resolve_schedule(date_text: str) -> ResolvedSchedule:
    date = datetime.strptime(date_text, '%Y-%m-%d')
    weekday = WEEKDAYS[date.weekday()]
    data = load_schedule()
    defaults = data.get('defaults', {})
    rule = dict(defaults)
    rule.update(data.get('weekday_rules', {}).get(weekday, {}))
    coverage = str(rule.get('coverage', 'weekly'))
    return ResolvedSchedule(
        date=date_text,
        weekday=weekday,
        theme=str(rule.get('theme', 'ai')),
        coverage=coverage,
        window=rule.get('window') or default_window_for(date_text, coverage),
        speaker=str(rule.get('speaker', 'zundamon')),
        site_theme=str(rule.get('site_theme', 'ai')),
        source_suggestions=[str(url) for url in rule.get('source_suggestions', [])],
    )


def resolve_rule(date_text: str) -> tuple[str, dict]:
    schedule = resolve_schedule(date_text)
    data = schedule.to_dict()
    weekday = str(data.pop('weekday'))
    data.pop('date', None)
    return weekday, data
