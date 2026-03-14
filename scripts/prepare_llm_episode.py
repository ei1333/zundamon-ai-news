#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from schedule_utils import resolve_rule

ROOT = Path(__file__).resolve().parent.parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Prepare draft + LLM prompt files for an episode.')
    parser.add_argument('date', help='Episode date in YYYY-MM-DD format')
    parser.add_argument('urls', nargs='*', help='Three source article URLs')
    parser.add_argument('--theme', help='Theme name. If omitted, resolves from schedule.')
    return parser.parse_args()


def run(cmd: list[str], *, stdout_path: Path | None = None) -> None:
    if stdout_path is None:
        subprocess.run(cmd, check=True)
        return
    with stdout_path.open('w', encoding='utf-8') as f:
        subprocess.run(cmd, check=True, stdout=f)


def main() -> None:
    args = parse_args()
    _, rule = resolve_rule(args.date)
    theme = args.theme or rule.get('theme', 'ai')

    if len(args.urls) not in (0, 3):
        raise SystemExit('Pass either zero URLs or exactly three URLs')

    if len(args.urls) == 0:
        print(f'Schedule for {args.date}:', file=sys.stderr)
        print(f'- theme: {theme}', file=sys.stderr)
        print(f'- coverage: {rule.get("coverage", "weekly")}', file=sys.stderr)
        print(f'- window: {rule.get("window", "") or "auto"}', file=sys.stderr)
        print('', file=sys.stderr)
        print('Source suggestions:', file=sys.stderr)
        for url in rule.get('source_suggestions', []):
            print(f'- {url}', file=sys.stderr)
        print('', file=sys.stderr)
        print('Pass 3 article URLs to continue.', file=sys.stderr)
        raise SystemExit(1)

    drafts_dir = ROOT / 'drafts'
    prompts_dir = ROOT / 'prompts' / 'generated'
    episodes_dir = ROOT / 'episodes'
    drafts_dir.mkdir(exist_ok=True)
    prompts_dir.mkdir(parents=True, exist_ok=True)
    episodes_dir.mkdir(exist_ok=True)

    draft_out = drafts_dir / f'{args.date}.{theme}.draft.md'
    prompt_out = prompts_dir / f'{args.date}.{theme}.prompt.txt'
    episode_out = episodes_dir / f'{args.date}.md'

    if episode_out.exists():
        raise SystemExit(f'Episode already exists: {episode_out}')

    print(f'==> Building draft: {draft_out.relative_to(ROOT)}')
    run([
        sys.executable,
        str(ROOT / 'scripts' / 'draft_from_urls.py'),
        '--theme',
        theme,
        '--stdout',
        args.date,
        *args.urls,
    ], stdout_path=draft_out)

    print(f'==> Building LLM prompt: {prompt_out.relative_to(ROOT)}')
    run([
        sys.executable,
        str(ROOT / 'scripts' / 'build_rewrite_prompt.py'),
        args.date,
        '--theme',
        theme,
        '--draft-file',
        str(draft_out),
    ], stdout_path=prompt_out)

    print('==> Prepared files')
    print(f'- Draft:  {draft_out.relative_to(ROOT)}')
    print(f'- Prompt: {prompt_out.relative_to(ROOT)}')
    print('')
    print('Next steps:')
    print(f'1. Send {prompt_out.relative_to(ROOT)} to your LLM')
    print(f'2. Save the returned Markdown to {episode_out.relative_to(ROOT)}')
    print(f'3. Run: ./scripts/build_episode.sh {args.date}')


if __name__ == '__main__':
    main()
