#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
import sys

from episode_utils import (
    ROOT,
    build_head_html,
    build_tag_spans,
    escape_attr,
    escape_text,
    load_template,
    parse_episode_full,
)


def render_html(date: str, header: dict, items: list[dict]) -> str:
    item_html = []
    for item in items:
        item_html.append(
            '          <li>\n'
            '            <div class="episode-tags">\n'
            f'{build_tag_spans([item], indent="              ", category_key="Category", class_key="CategoryClass")}\n'
            '            </div>\n'
            f'            <h3>{escape_text(item["Headline"])}</h3>\n'
            f'            <p>{escape_text(item["Summary"])}</p>\n'
            f'            <p>出典: <a href="{escape_attr(item["SourceURL"])}">{escape_text(item["SourceName"])} </a></p>\n'
            '          </li>'
        )

    return load_template('day.html').format(
        head_html=build_head_html(
            title=f'{date} | ずんだもん1分AIニュース',
            description=header['summary'],
            url=f'https://ei1333.github.io/zundamon-ai-news/days/{date}.html',
            stylesheet_href='../assets/style.css',
            og_type='article',
            og_image_url=f'https://ei1333.github.io/zundamon-ai-news/assets/ogp-{date}.png',
        ),
        page_heading=escape_text(f'{date} のAIニュース'),
        intro_html=escape_text(header['intro']),
        audio_file=escape_attr(f'sample-news-{date}.wav'),
        summary_html=escape_text(header['summary']),
        items_html='\n'.join(item_html),
        closing_html=escape_text(header['closing']),
    )


def render_script(header: dict, items: list[dict]) -> str:
    lines = [header['script_intro'], '']
    for item in items:
        lines.append(item['Script'])
        lines.append('')
    lines.append(header['script_closing'])
    return '\n'.join(lines).strip() + '\n'


def main():
    if len(sys.argv) != 2:
        raise SystemExit('Usage: ./scripts/render_episode.py YYYY-MM-DD')

    date = sys.argv[1]
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', date):
        raise SystemExit('Expected YYYY-MM-DD')

    episode_path = ROOT / 'episodes' / f'{date}.md'
    if not episode_path.exists():
        raise SystemExit(f'Episode source not found: {episode_path}')

    header, items = parse_episode_full(episode_path)

    days_dir = ROOT / 'days'
    scripts_dir = ROOT / 'scripts_text'
    days_dir.mkdir(exist_ok=True)
    scripts_dir.mkdir(exist_ok=True)

    (days_dir / f'{date}.html').write_text(render_html(date, header, items), encoding='utf-8')
    (scripts_dir / f'{date}.txt').write_text(render_script(header, items), encoding='utf-8')

    subprocess.run(
        [
            sys.executable,
            str(ROOT / 'scripts' / 'render_ogp.py'),
            '--date',
            date,
            '--title',
            header['title'],
            '--summary',
            header['summary'],
        ],
        check=True,
    )

    print(f'Rendered: days/{date}.html')
    print(f'Rendered: scripts_text/{date}.txt')
    print(f'Rendered: assets/ogp-{date}.png')


if __name__ == '__main__':
    main()
