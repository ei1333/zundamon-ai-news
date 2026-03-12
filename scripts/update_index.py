#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def extract_section(text: str, heading: str) -> str:
    pattern = rf'^## {re.escape(heading)}\n(.*?)(?=^## |\Z)'
    match = re.search(pattern, text, flags=re.MULTILINE | re.DOTALL)
    if not match:
        raise SystemExit(f'Missing section: {heading}')
    return match.group(1).strip()


def parse_episode(path: Path) -> dict[str, str]:
    text = path.read_text(encoding='utf-8').strip()
    lines = text.splitlines()
    if not lines or not lines[0].startswith('# '):
        raise SystemExit('Episode file must start with a # title')
    return {
        'date': path.stem,
        'title': lines[0][2:].strip(),
        'summary': extract_section(text, 'Summary'),
    }


def list_episodes() -> list[dict[str, str]]:
    paths = sorted(
        (ROOT / 'episodes').glob('*.md'),
        key=lambda p: p.stem,
        reverse=True,
    )
    return [parse_episode(path) for path in paths if path.name != '_template.md']


def update_index(target_date: str | None = None) -> None:
    episodes = list_episodes()
    if not episodes:
        raise SystemExit('No episodes found')

    latest = episodes[0]
    if target_date is not None:
        matched = [episode for episode in episodes if episode['date'] == target_date]
        if not matched:
            raise SystemExit(f'Episode not found for date: {target_date}')
        latest = matched[0]

    index_path = ROOT / 'index.html'
    text = index_path.read_text(encoding='utf-8')

    lead_pattern = r'<p class="lead">.*?</p>'
    lead_block = (
        f'<p class="lead">\n'
        f'          公開情報をもとに独自要約したAIニュースを、ずんだもんの声で1分前後にまとめる試作ページです。\n'
        f'          {latest["summary"]}\n'
        f'        </p>'
    )
    text, count = re.subn(lead_pattern, lead_block, text, count=1, flags=re.DOTALL)
    if count != 1:
        raise SystemExit('Could not update lead text in index.html')

    latest_pattern = r'<section class="card">\s*<h2>最新サンプル</h2>\s*<p>.*?</p>\s*<p><a class="button" href="days/.*?\.html">.*?</a></p>\s*</section>'
    latest_block = (
        f'<section class="card">\n'
        f'        <h2>最新サンプル</h2>\n'
        f'        <p>{latest["date"]} の回です。</p>\n'
        f'        <p><a class="button" href="days/{latest["date"]}.html">最新回を見る</a></p>\n'
        f'      </section>'
    )
    text, count = re.subn(latest_pattern, latest_block, text, count=1, flags=re.DOTALL)
    if count != 1:
        raise SystemExit('Could not update latest card in index.html')

    backnumber_pattern = r'(<section class="card">\s*<h2>バックナンバー</h2>\s*<ul>\n)(.*?)(\s*</ul>\s*</section>)'
    entries = ''.join(
        f'          <li><a href="days/{episode["date"]}.html">{episode["date"]} | {episode["title"]}</a></li>\n'
        for episode in episodes
    )
    text, count = re.subn(
        backnumber_pattern,
        lambda m: f'{m.group(1)}{entries}{m.group(3)}',
        text,
        count=1,
        flags=re.DOTALL,
    )
    if count != 1:
        raise SystemExit('Could not rebuild backnumber list in index.html')

    index_path.write_text(text, encoding='utf-8')


if __name__ == '__main__':
    if len(sys.argv) > 2:
        raise SystemExit('Usage: ./scripts/update_index.py [YYYY-MM-DD]')
    update_index(sys.argv[1] if len(sys.argv) == 2 else None)
