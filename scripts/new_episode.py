#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def validate_date(date: str) -> str:
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', date):
        raise SystemExit(f'Invalid date format: {date}\nExpected YYYY-MM-DD')
    return date


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def create_episode_from_template(template_path: Path, target_path: Path, date: str, title: str) -> None:
    if not template_path.exists():
        raise SystemExit(f'Episode template not found: {template_path}')
    if target_path.exists():
        raise SystemExit(f'Target already exists: {target_path}')

    text = template_path.read_text(encoding='utf-8')
    text = text.replace('YYYY-MM-DD', date)
    text, count = re.subn(r'^#\s+.*$', f'# {title}', text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise SystemExit('Template title heading not found')
    target_path.write_text(text, encoding='utf-8')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Create a new episode source file and initial rendered outputs.'
    )
    parser.add_argument('date', help='Episode date in YYYY-MM-DD format')
    parser.add_argument('title', nargs='?', default='新しいAIニュース回', help='Episode title')
    parser.add_argument(
        '--no-index',
        action='store_true',
        help='Skip updating index.html after creating the episode',
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    date = validate_date(args.date)
    title = args.title

    episodes_dir = ROOT / 'episodes'
    days_dir = ROOT / 'days'
    scripts_text_dir = ROOT / 'scripts_text'
    audio_dir = ROOT / 'assets' / 'audio'

    episodes_dir.mkdir(exist_ok=True)
    days_dir.mkdir(exist_ok=True)
    scripts_text_dir.mkdir(exist_ok=True)
    audio_dir.mkdir(parents=True, exist_ok=True)

    template_path = episodes_dir / '_template.md'
    episode_path = episodes_dir / f'{date}.md'

    create_episode_from_template(template_path, episode_path, date, title)
    run([sys.executable, str(ROOT / 'scripts' / 'render_episode.py'), date])
    if not args.no_index:
        run([sys.executable, str(ROOT / 'scripts' / 'update_index.py'), date])

    print('Created:')
    print(f'- episodes/{date}.md')
    print(f'- days/{date}.html')
    print(f'- scripts_text/{date}.txt')
    if args.no_index:
        print('- index.html was not updated (--no-index)')

    print('\nNext steps:')
    print(f'1. Edit episodes/{date}.md')
    print(f'2. Re-render: ./scripts/render_episode.py {date}')
    print(f'3. Render audio: ./scripts/render_audio.sh {date}')
    if not args.no_index:
        print('4. Review index.html')
        print('5. git add . && git commit && git push origin main')
    else:
        print(f'4. Update index later: ./scripts/update_index.py {date}')
        print('5. git add . && git commit && git push origin main')


if __name__ == '__main__':
    main()
