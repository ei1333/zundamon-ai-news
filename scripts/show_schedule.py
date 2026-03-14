#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from schedule_utils import resolve_schedule


def main() -> None:
    parser = argparse.ArgumentParser(description='Show the configured publishing schedule for a date.')
    parser.add_argument('date', help='Date in YYYY-MM-DD format')
    parser.add_argument('--json', action='store_true', help='Print the resolved rule as JSON')
    args = parser.parse_args()

    result = resolve_schedule(args.date).to_dict()
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print(f"date: {result['date']}")
    print(f"weekday: {result['weekday']}")
    for key in ['theme', 'coverage', 'window', 'speaker', 'site_theme']:
        if key in result:
            print(f"{key}: {result[key]}")
    for url in result.get('source_suggestions', []):
        print(f"source: {url}")


if __name__ == '__main__':
    main()
