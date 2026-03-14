#!/usr/bin/env python3
from __future__ import annotations

import argparse
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


def main() -> None:
    parser = argparse.ArgumentParser(description='Show the configured publishing schedule for a date.')
    parser.add_argument('date', help='Date in YYYY-MM-DD format')
    parser.add_argument('--json', action='store_true', help='Print the resolved rule as JSON')
    args = parser.parse_args()

    weekday, rule = resolve_rule(args.date)
    result = {
        'date': args.date,
        'weekday': weekday,
        **rule,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print(f"date: {args.date}")
    print(f"weekday: {weekday}")
    for key in ['theme', 'coverage', 'speaker', 'site_theme']:
        if key in result:
            print(f"{key}: {result[key]}")


if __name__ == '__main__':
    main()
