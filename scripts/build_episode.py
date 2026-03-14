#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from schedule_utils import resolve_schedule

ROOT = Path(__file__).resolve().parent.parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Build episode outputs for a date.')
    parser.add_argument('date', help='Episode date in YYYY-MM-DD format')
    parser.add_argument('speaker', nargs='?', help='Speaker name override')
    return parser.parse_args()


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def main() -> None:
    args = parse_args()
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', args.date):
        raise SystemExit(f'Invalid date format: {args.date}\nExpected YYYY-MM-DD')

    schedule = resolve_schedule(args.date)
    speaker = args.speaker or schedule.speaker
    site_theme = schedule.site_theme

    if args.speaker is None:
        print(f'==> Using schedule for {args.date}')
        print(json.dumps(schedule.to_dict(), ensure_ascii=False, indent=2))

    print(f'==> Rendering episode outputs for {args.date}')
    run([sys.executable, str(ROOT / 'scripts' / 'render_episode.py'), args.date])

    print(f'==> Updating index (site theme: {site_theme})')
    run([sys.executable, str(ROOT / 'scripts' / 'update_index.py'), '--site-theme', site_theme])

    print(f'==> Rendering audio ({speaker})')
    run([str(ROOT / 'scripts' / 'render_audio.sh'), args.date, speaker])

    print('==> Validating site')
    run([str(ROOT / 'scripts' / 'validate.sh')])

    print('==> Done')
    print(f'Built episode: {args.date}')


if __name__ == '__main__':
    main()
