#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import socket
import urllib.error
from pathlib import Path

from draft_builder import build_episode_text, fallback_from_url
from draft_fetch import extract_description, extract_site_name, extract_title, fetch_url, finalize_headline
from draft_tagging import infer_category, infer_tags, pick_episode_title
from episode_utils import default_window_for, load_theme
from schedule_utils import resolve_rule

ROOT = Path(__file__).resolve().parent.parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Create an episode draft from article URLs.')
    parser.add_argument('date', help='Episode date in YYYY-MM-DD format')
    parser.add_argument('urls', nargs=3, help='Three source article URLs')
    parser.add_argument('--title', help='Override episode title')
    parser.add_argument('--theme', help='Theme name from config/themes/<name>.json. If omitted, resolves from schedule.')
    parser.add_argument('--coverage', choices=['daily', 'weekly'], help='Coverage window type for this draft. If omitted, resolves from schedule.')
    parser.add_argument('--window', help='Explicit window like YYYY-MM-DD..YYYY-MM-DD. Defaults from coverage/date or schedule.')
    parser.add_argument('--stdout', action='store_true', help='Print the draft instead of writing episodes/YYYY-MM-DD.md')
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', args.date):
        raise SystemExit('Expected YYYY-MM-DD')

    _, schedule_rule = resolve_rule(args.date)
    theme_name = args.theme or schedule_rule.get('theme', 'ai')
    coverage = args.coverage or schedule_rule.get('coverage', 'weekly')
    window = args.window or schedule_rule.get('window') or default_window_for(args.date, coverage)

    theme = load_theme(theme_name)
    draft_theme = theme.get('draft', {})
    default_categories = list(draft_theme.get('default_categories', ['透明性', '研究', 'インフラ']))
    category_rules = [
        (str(rule['label']), list(rule.get('keywords', [])))
        for rule in draft_theme.get('category_rules', [])
    ]
    tag_rules = [
        (str(rule['label']), list(rule.get('keywords', [])))
        for rule in draft_theme.get('tag_rules', [])
    ]

    items: list[dict[str, object]] = []
    for idx, url in enumerate(args.urls, start=1):
        fallback_category = default_categories[idx - 1]
        try:
            html_text = fetch_url(url)
            raw_title = extract_title(html_text)
            description = extract_description(html_text)
            title = finalize_headline(raw_title, theme_name, description=description)
            site_name = extract_site_name(html_text, url)
            primary_tag = infer_category(title, description, fallback_category, category_rules)
            items.append(
                {
                    'headline': title,
                    'summary': description,
                    'source_name': site_name,
                    'url': url,
                    'category': primary_tag,
                    'tags': infer_tags(title, description, primary_tag, tag_rules),
                }
            )
        except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
            items.append(fallback_from_url(url, fallback_category, str(exc), draft_theme, theme_name=theme_name))

    draft = build_episode_text(
        args.date,
        items,
        draft_theme,
        theme_name=theme_name,
        coverage=coverage,
        window=window,
        title=args.title,
        pick_title=pick_episode_title,
    )

    if args.stdout:
        print(draft)
        return

    out_path = ROOT / 'episodes' / f'{args.date}.md'
    if out_path.exists():
        raise SystemExit(f'Target already exists: {out_path}')
    out_path.write_text(draft, encoding='utf-8')

    print(f'Created: episodes/{args.date}.md')
    print('Review the generated summaries and tags before rendering.')
    print(json.dumps(items, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
