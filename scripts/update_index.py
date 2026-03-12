#!/usr/bin/env python3
from __future__ import annotations

import html
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


def extract_subsection(text: str, heading: str) -> str:
    pattern = rf'^### {re.escape(heading)}\n(.*?)(?=^### |\Z)'
    match = re.search(pattern, text, flags=re.MULTILINE | re.DOTALL)
    if not match:
        raise SystemExit(f'Missing subsection: {heading}')
    return match.group(1).strip()


def normalize_category(label: str) -> tuple[str, str]:
    normalized = label.strip().lower()
    mapping = {
        '透明性': ('透明性', 'category-transparency'),
        'transparency': ('透明性', 'category-transparency'),
        '研究': ('研究', 'category-research'),
        'research': ('研究', 'category-research'),
        'インフラ': ('インフラ', 'category-infra'),
        'infra': ('インフラ', 'category-infra'),
        'infrastructure': ('インフラ', 'category-infra'),
        '安全性': ('安全性', 'category-safety'),
        'safety': ('安全性', 'category-safety'),
        '市場': ('市場', 'category-market'),
        'market': ('市場', 'category-market'),
    }
    return mapping.get(normalized, (label.strip() or 'AI', 'category-general'))


def default_category(idx: int) -> tuple[str, str]:
    mapping = {
        1: ('透明性', 'category-transparency'),
        2: ('研究', 'category-research'),
        3: ('インフラ', 'category-infra'),
    }
    return mapping.get(idx, ('AI', 'category-general'))


def parse_episode(path: Path) -> dict[str, object]:
    text = path.read_text(encoding='utf-8').strip()
    lines = text.splitlines()
    if not lines or not lines[0].startswith('# '):
        raise SystemExit('Episode file must start with a # title')

    items = []
    for idx in range(1, 4):
        item_block = extract_section(text, f'Item {idx}')
        category_text = extract_subsection(item_block, 'Category') if '### Category' in item_block else ''
        category_label, category_class = normalize_category(category_text)
        if not category_text:
            category_label, category_class = default_category(idx)
        items.append({
            'headline': extract_subsection(item_block, 'Headline'),
            'category_label': category_label,
            'category_class': category_class,
        })

    return {
        'date': path.stem,
        'title': lines[0][2:].strip(),
        'summary': extract_section(text, 'Summary'),
        'items': items,
    }


def list_episodes() -> list[dict[str, str]]:
    paths = sorted((ROOT / 'episodes').glob('*.md'), key=lambda p: p.stem, reverse=True)
    return [parse_episode(path) for path in paths if path.name != '_template.md']


def build_latest_cards(episodes: list[dict[str, object]]) -> str:
    cards = []
    for episode in episodes[:3]:
        date = html.escape(str(episode['date']))
        title = html.escape(str(episode['title']))
        summary = html.escape(str(episode['summary']))
        tags = ''.join(
            f'              <span class="episode-tag {item["category_class"]}">{html.escape(str(item["category_label"]))}</span>\n'
            for item in episode['items']
        )
        headlines = '\n'.join(
            f'              <li>{html.escape(str(item["headline"]))}</li>' for item in episode['items']
        )
        cards.append(
            '          <article class="episode-card">\n'
            f'            <p class="episode-date">{date}</p>\n'
            f'            <h3><a href="days/{date}.html">{title}</a></h3>\n'
            '            <div class="episode-tags">\n'
            f'{tags}'
            '            </div>\n'
            f'            <p class="episode-summary">{summary}</p>\n'
            '            <ul class="episode-headlines">\n'
            f'{headlines}\n'
            '            </ul>\n'
            '          </article>'
        )
    return '\n'.join(cards)


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
        f'          {html.escape(latest["summary"])}\n'
        f'        </p>'
    )
    text, count = re.subn(lead_pattern, lead_block, text, count=1, flags=re.DOTALL)
    if count != 1:
        raise SystemExit('Could not update lead text in index.html')

    latest_pattern = r'<section class="card featured-card">.*?</section>'
    featured_tags = ''.join(
        f'            <span class="episode-tag {item["category_class"]}">{html.escape(str(item["category_label"]))}</span>\n'
        for item in latest['items']
    )
    featured_headlines = '\n'.join(
        f'            <li>{html.escape(str(item["headline"]))}</li>' for item in latest['items']
    )
    latest_block = (
        f'<section class="card featured-card">\n'
        f'        <div class="featured-copy">\n'
        f'          <p class="eyebrow">Latest Episode</p>\n'
        f'          <h2>最新サンプル</h2>\n'
        f'          <div class="featured-meta">\n'
        f'            <span class="featured-duration">▶ 1 min</span>\n'
        f'            <span class="featured-date-label">{html.escape(latest["date"])} </span>\n'
        f'          </div>\n'
        f'          <p>{html.escape(str(latest["date"]))} の回です。</p>\n'
        f'          <div class="episode-tags">\n'
        f'{featured_tags}'
        f'          </div>\n'
        f'          <ul class="featured-headlines">\n'
        f'{featured_headlines}\n'
        f'          </ul>\n'
        f'          <div class="featured-actions">\n'
        f'            <a class="button" href="days/{html.escape(str(latest["date"]))}.html">最新回を見る</a>\n'
        f'          </div>\n'
        f'          <audio class="featured-audio" controls preload="none">\n'
        f'            <source src="assets/audio/sample-news-{html.escape(str(latest["date"]))}.wav" type="audio/wav" />\n'
        f'            お使いのブラウザは audio 要素に対応していません。\n'
        f'          </audio>\n'
        f'        </div>\n'
        f'        <div class="featured-visual" aria-hidden="true">\n'
        f'          <div class="featured-badge">ON AIR</div>\n'
        f'          <div class="featured-screen">\n'
        f'            <div class="featured-logo">ずんだもん<span>1分AIニュース</span></div>\n'
        f'            <p class="featured-screen-date">{html.escape(str(latest["date"]))}</p>\n'
        f'            <p class="featured-screen-title">{html.escape(str(latest["title"]))}</p>\n'
        f'            <div class="featured-wave"></div>\n'
        f'          </div>\n'
        f'        </div>\n'
        f'      </section>'
    )
    text, count = re.subn(latest_pattern, latest_block, text, count=1, flags=re.DOTALL)
    if count != 1:
        raise SystemExit('Could not update latest card in index.html')

    latest_three_pattern = r'<section class="card">\s*<h2>最新3回</h2>\s*<div class="episode-grid">\n.*?\s*</div>\s*</section>'
    latest_three_block = (
        '<section class="card">\n'
        '        <h2>最新3回</h2>\n'
        '        <div class="episode-grid">\n'
        f'{build_latest_cards(episodes)}\n'
        '        </div>\n'
        '      </section>'
    )
    text, count = re.subn(latest_three_pattern, latest_three_block, text, count=1, flags=re.DOTALL)
    if count != 1:
        raise SystemExit('Could not rebuild latest 3 episodes in index.html')

    backnumber_pattern = r'<section class="card">\s*<h2>バックナンバー</h2>\s*<ul>\n.*?\s*</ul>\s*</section>'
    entries = ''.join(
        f'          <li><a href="days/{html.escape(episode["date"])}.html">{html.escape(episode["date"])} | {html.escape(episode["title"])} </a></li>\n'
        for episode in episodes
    ).rstrip()
    backnumber_block = (
        '<section class="card">\n'
        '        <h2>バックナンバー</h2>\n'
        '        <ul>\n'
        f'{entries}\n'
        '        </ul>\n'
        '      </section>'
    )
    text, count = re.subn(
        backnumber_pattern,
        backnumber_block,
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
