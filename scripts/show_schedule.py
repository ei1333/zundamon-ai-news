#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from episode_utils import default_window_for
from schedule_utils import resolve_rule


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
    result['window'] = result.get('window') or default_window_for(args.date, result.get('coverage', 'weekly'))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print(f"date: {args.date}")
    print(f"weekday: {weekday}")
    for key in ['theme', 'coverage', 'window', 'speaker', 'site_theme']:
        if key in result:
            print(f"{key}: {result[key]}")
    for url in result.get('source_suggestions', []):
        print(f"source: {url}")


if __name__ == '__main__':
    main()
