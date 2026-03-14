#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from episode_utils import ROOT, load_theme
from schedule_utils import load_schedule


def main() -> None:
    theme_dir = ROOT / 'config' / 'themes'
    for path in sorted(theme_dir.glob('*.json')):
        load_theme(path.stem)
        print(f'OK theme: {path.name}')

    load_schedule()
    print('OK schedule: config/schedule.json')


if __name__ == '__main__':
    main()
