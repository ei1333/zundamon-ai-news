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
        'title': lines[0][2:].strip(),
        'summary': extract_section(text, 'Summary'),
    }


def update_index(date: str) -> None:
    episode = parse_episode(ROOT / 'episodes' / f'{date}.md')
    index_path = ROOT / 'index.html'
    text = index_path.read_text(encoding='utf-8')

    lead_pattern = r'(<p class="lead">\s*公開情報をもとに独自要約したAIニュースを、ずんだもんの声で1分前後にまとめる試作ページです。\s*)(.*?)(\s*</p>)'
    lead_replacement = rf'\1{date} の回では、{episode["summary"]}\3'
    text, count = re.subn(lead_pattern, lead_replacement, text, flags=re.DOTALL)
    if count != 1:
        raise SystemExit('Could not update lead text in index.html')

    latest_pattern = r'<section class="card">\s*<h2>最新サンプル</h2>\s*<p>.*?</p>\s*<p><a class="button" href="days/.*?\.html">.*?</a></p>\s*</section>'
    latest_block = (
        f'<section class="card">\n'
        f'        <h2>最新サンプル</h2>\n'
        f'        <p>{date} の回です。</p>\n'
        f'        <p><a class="button" href="days/{date}.html">最新回を見る</a></p>\n'
        f'      </section>'
    )
    text, count = re.subn(latest_pattern, latest_block, text, count=1, flags=re.DOTALL)
    if count != 1:
        raise SystemExit('Could not update latest card in index.html')

    entry = f'          <li><a href="days/{date}.html">{date} | {episode["title"]}</a></li>\n'
    list_marker = '        <ul>\n'
    if entry not in text:
        pos = text.find(list_marker)
        if pos == -1:
            raise SystemExit('Could not find backnumber list in index.html')
        pos += len(list_marker)
        text = text[:pos] + entry + text[pos:]

    index_path.write_text(text, encoding='utf-8')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: ./scripts/update_index.py YYYY-MM-DD')
    update_index(sys.argv[1])
