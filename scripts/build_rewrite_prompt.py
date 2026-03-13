#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROMPT_TEMPLATE_PATH = ROOT / 'prompts' / 'episode_rewrite_prompt.md'


def validate_date(date: str) -> str:
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', date):
        raise SystemExit(f'Invalid date format: {date}\nExpected YYYY-MM-DD')
    return date


def extract_template_text(markdown: str) -> str:
    marker = '## Prompt Template'
    if marker not in markdown:
        raise SystemExit(f'Missing section: {marker}')

    tail = markdown.split(marker, 1)[1]
    start = tail.find('```text')
    if start == -1:
        raise SystemExit('Missing ```text block in prompt template')
    start += len('```text')
    end = tail.find('```', start)
    if end == -1:
        raise SystemExit('Unterminated prompt template code block')
    return tail[start:end].strip()


def read_draft(args: argparse.Namespace) -> str:
    if args.draft_file:
        return Path(args.draft_file).read_text(encoding='utf-8').strip()
    if not sys.stdin.isatty():
        data = sys.stdin.read().strip()
        if data:
            return data
    raise SystemExit('Provide --draft-file or pipe draft markdown via stdin')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Build an LLM rewrite prompt from date/theme/draft markdown.'
    )
    parser.add_argument('date', help='Episode date in YYYY-MM-DD format')
    parser.add_argument('--theme', default='default', help='Theme name for prompt context')
    parser.add_argument('--title', help='Optional episode title hint for the prompt')
    parser.add_argument('--draft-file', help='Path to draft markdown. If omitted, reads stdin')
    parser.add_argument('--template', default=str(PROMPT_TEMPLATE_PATH), help='Prompt template markdown path')
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    date = validate_date(args.date)
    prompt_doc = Path(args.template).read_text(encoding='utf-8')
    template = extract_template_text(prompt_doc)
    draft_markdown = read_draft(args)
    episode_title = args.title or f'{date} のニュース回'

    prompt = template.format(
        episode_title=episode_title,
        theme_name=args.theme,
        date=date,
        draft_markdown=draft_markdown,
    )
    print(prompt)


if __name__ == '__main__':
    main()
