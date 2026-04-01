#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def fail(message: str) -> None:
    raise SystemExit(f'ERROR: {message}')


def warn(message: str) -> None:
    print(f'WARN: {message}')


def grep_check(pattern: str, *paths: str) -> bool:
    result = subprocess.run([
        'grep', '-R', '--line-number', '--exclude=_template.html', '--exclude=_template.md', pattern, *paths
    ], cwd=ROOT)
    return result.returncode == 0


def main() -> None:
    import sys
    sys.path.insert(0, str(ROOT / 'scripts'))
    from episode_utils import detect_episode_theme, extract_section, parse_episode_full
    from render_ogp import fit_episode_title_layout
    from validate_config import main as validate_config_main

    validate_config_main()

    if not (ROOT / 'index.html').exists():
        fail('index.html not found')
    for directory in ['episodes', 'days', 'assets/audio']:
        if not (ROOT / directory).exists():
            fail(f'{directory} not found')
    if not (ROOT / 'assets' / 'ogp.png').exists():
        fail('assets/ogp.png not found')

    if grep_check('YYYY-MM-DD', 'episodes', 'days', 'index.html'):
        fail('Unreplaced template marker YYYY-MM-DD found')
    if grep_check('{[A-Za-z0-9_][A-Za-z0-9_]*}', 'days', 'index.html'):
        fail('Unreplaced template placeholder found in rendered HTML')

    episode_sources = sorted(path for path in (ROOT / 'episodes').glob('*.md') if path.name != '_template.md')
    if not episode_sources:
        fail('No episode sources found')

    latest_date = episode_sources[-1].stem
    index_text = (ROOT / 'index.html').read_text(encoding='utf-8')
    if f'href="days/{latest_date}.html"' not in index_text:
        fail(f'index.html does not point to latest episode {latest_date}')

    for source in episode_sources:
        date = source.stem
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', date):
            fail(f'Unexpected episode source name: {source.name}')
        if not source.read_text(encoding='utf-8').strip():
            fail(f'Episode source is empty: {source}')

        required_files = [
            ROOT / 'days' / f'{date}.html',
            ROOT / 'scripts_text' / f'{date}.txt',
            ROOT / 'assets' / 'audio' / f'sample-news-{date}.wav',
            ROOT / 'assets' / f'ogp-{date}.png',
        ]
        for path in required_files:
            if not path.exists():
                fail(f'Missing generated file: {path.relative_to(ROOT)}')
            if path.stat().st_size == 0:
                fail(f'Generated file is empty: {path.relative_to(ROOT)}')

        text = source.read_text(encoding='utf-8')
        explicit_theme = extract_section(text, 'Theme').strip().lower()
        if not explicit_theme:
            fail(f'Episode theme must not be empty: {source}')
        coverage = extract_section(text, 'Coverage').strip().lower()
        if coverage not in {'daily', 'weekly'}:
            fail(f'Episode coverage must be one of daily/weekly: {source} (got: {coverage})')
        window = extract_section(text, 'Window').strip()
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}\.\.\d{4}-\d{2}-\d{2}', window):
            fail(f'Episode window must be YYYY-MM-DD..YYYY-MM-DD: {source} (got: {window})')

        document = parse_episode_full(source, theme_name=detect_episode_theme(source))
        if len(document.items) != 3:
            fail(f'Episode must contain exactly 3 items: {source}')
        if not document.header.title.strip():
            fail(f'Episode title is empty: {source}')
        for idx, item in enumerate(document.items, start=1):
            if not item.headline.strip():
                fail(f'Item {idx} headline is empty: {source}')
            if not item.summary.strip():
                fail(f'Item {idx} summary is empty: {source}')
            if not item.source_name.strip() or not item.source_url.strip():
                fail(f'Item {idx} source is incomplete: {source}')

        title = ' '.join(document.header.title.split())
        topics = [part.strip() for part in title.split('・') if part.strip()]
        title_lines, title_font_size = fit_episode_title_layout(title)
        if title_font_size <= 34:
            warn(f'{source.name}: title requires OGP font shrink to {title_font_size}pt')
        if len(topics) >= 4:
            warn(f'{source.name}: title has {len(topics)} topics; OGP may drop trailing topics')
        for idx, topic in enumerate(topics, start=1):
            if len(topic) > 18:
                warn(f'{source.name}: topic {idx} is {len(topic)} chars; OGP balance may degrade')

        day_html = (ROOT / 'days' / f'{date}.html').read_text(encoding='utf-8')
        if f'href="days/{date}.html"' not in index_text:
            fail(f'index.html does not link to days/{date}.html')
        if f'sample-news-{date}.wav' not in day_html:
            fail(f'days/{date}.html does not reference sample-news-{date}.wav')
        if f'assets/ogp-{date}.png' not in day_html and f'/assets/ogp-{date}.png' not in day_html:
            fail(f'days/{date}.html does not reference ogp-{date}.png')
        if '<meta property="og:type" content="article"' not in day_html:
            fail(f'days/{date}.html missing article og:type')
        if '<audio class="audio" controls' not in day_html:
            fail(f'days/{date}.html missing audio player')

    if '<meta property="og:type" content="website"' not in index_text:
        fail('index.html missing website og:type')
    if 'sample-news-' not in index_text:
        fail('index.html does not reference any episode audio')

    print('Validation OK')


if __name__ == '__main__':
    main()
