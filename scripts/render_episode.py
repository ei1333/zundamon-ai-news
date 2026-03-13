#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
import sys

from episode_utils import (
    ROOT,
    build_head_html,
    build_tag_spans,
    detect_episode_theme,
    escape_attr,
    escape_text,
    load_template,
    load_theme,
    parse_episode_full,
)


def render_html(date: str, header: dict, items: list[dict], *, theme_name: str = 'ai') -> str:
    theme = load_theme(theme_name)
    day_theme = theme.get('day', {})
    coverage_label = '直近1週間' if header.get('coverage') == 'weekly' else '当日'
    page_heading_template = day_theme.get('page_heading_weekly' if header.get('coverage') == 'weekly' else 'page_heading', '{date} のニュース')
    item_html = []
    for item in items:
        item_html.append(
            '          <li>\n'
            '            <div class="episode-tags">\n'
            f'{build_tag_spans([item], indent="              ", category_key="Category", class_key="CategoryClass")}\n'
            '            </div>\n'
            f'            <h3>{escape_text(item["Headline"])}</h3>\n'
            f'            <p>{escape_text(item["Summary"])}</p>\n'
            f'            <p>{escape_text(day_theme.get("source_prefix", "出典:"))} <a href="{escape_attr(item["SourceURL"])}">{escape_text(item["SourceName"])} </a></p>\n'
            '          </li>'
        )

    site_url = theme.get('site_url', 'https://example.com/').rstrip('/')
    return load_template('day.html').format(
        head_html=build_head_html(
            title=f'{date} | {theme.get("site_name", "Site")}',
            description=header['summary'],
            url=f'{site_url}/days/{date}.html',
            stylesheet_href='../assets/style.css',
            og_type='article',
            og_image_url=f'{site_url}/assets/ogp-{date}.png',
            theme_name=theme_name,
        ),
        back_link=escape_text(day_theme.get('back_link', '← トップページへ戻る')),
        eyebrow=escape_text(day_theme.get('eyebrow_weekly' if header.get('coverage') == 'weekly' else 'eyebrow', '今日のエピソード')),
        page_heading=escape_text(page_heading_template.format(date=date, window=header.get('window', date))),
        theme_label=escape_text(theme.get('theme_label', theme.get('site_name', ''))),
        coverage_label=escape_text(coverage_label),
        window_label=escape_text(header.get('window', date)),
        intro_html=escape_text(header['intro']),
        audio_heading=escape_text(day_theme.get('audio_heading', '音声で聴く')),
        audio_file=escape_attr(f'sample-news-{date}.wav'),
        content_heading=escape_text(day_theme.get('content_heading', 'この回の内容')),
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Render one episode into HTML / script / OGP.')
    parser.add_argument('date', help='Episode date in YYYY-MM-DD format')
    parser.add_argument('--theme', help='Optional theme override. If omitted, uses ## Theme from the episode source.')
    return parser.parse_args()


def main():
    args = parse_args()
    date = args.date
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', date):
        raise SystemExit('Expected YYYY-MM-DD')

    episode_path = ROOT / 'episodes' / f'{date}.md'
    if not episode_path.exists():
        raise SystemExit(f'Episode source not found: {episode_path}')

    theme_name = args.theme or detect_episode_theme(episode_path)
    header, items = parse_episode_full(episode_path, theme_name=theme_name)

    days_dir = ROOT / 'days'
    scripts_dir = ROOT / 'scripts_text'
    days_dir.mkdir(exist_ok=True)
    scripts_dir.mkdir(exist_ok=True)

    (days_dir / f'{date}.html').write_text(render_html(date, header, items, theme_name=theme_name), encoding='utf-8')
    (scripts_dir / f'{date}.txt').write_text(render_script(header, items), encoding='utf-8')

    subprocess.run(
        [
            sys.executable,
            str(ROOT / 'scripts' / 'render_ogp.py'),
            '--theme',
            theme_name,
            '--date',
            date,
            '--title',
            header['title'],
        ],
        check=True,
    )

    print(f'Rendered: days/{date}.html')
    print(f'Rendered: scripts_text/{date}.txt')
    print(f'Rendered: assets/ogp-{date}.png')


if __name__ == '__main__':
    main()
