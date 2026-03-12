#!/usr/bin/env python3
from __future__ import annotations

import html
import sys

from episode_utils import ROOT, parse_episode_summary


def list_episodes() -> list[dict[str, str]]:
    paths = sorted((ROOT / 'episodes').glob('*.md'), key=lambda p: p.stem, reverse=True)
    return [parse_episode_summary(path) for path in paths if path.name != '_template.md']


def build_latest_cards(episodes: list[dict[str, object]]) -> str:
    cards = []
    for episode in episodes[1:3]:
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


def replace_between_markers(text: str, start_marker: str, end_marker: str, replacement: str) -> str:
    start = text.find(start_marker)
    end = text.find(end_marker)
    if start == -1 or end == -1 or end < start:
        raise SystemExit(f'Missing marker pair: {start_marker} / {end_marker}')
    after_start = start + len(start_marker)
    line_start = text.rfind('\n', 0, end) + 1
    closing_indent = text[line_start:end]
    return text[:after_start] + '\n' + replacement + '\n' + closing_indent + text[end:]


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

    lead_block = (
        '        <p class="lead">\n'
        '          公開情報をもとに独自要約したAIニュースを、ずんだもんの声で1分前後にまとめてお届けするページです。\n'
        '        </p>'
    )
    text = replace_between_markers(text, '<!-- INDEX_LEAD_START -->', '<!-- INDEX_LEAD_END -->', lead_block)

    featured_tags = ''.join(
        f'            <span class="episode-tag {item["category_class"]}">{html.escape(str(item["category_label"]))}</span>\n'
        for item in latest['items']
    )
    featured_headlines = '\n'.join(
        f'            <li>{html.escape(str(item["headline"]))}</li>' for item in latest['items']
    )
    latest_block = (
        f'      <section class="card featured-card">\n'
        f'        <div class="featured-copy">\n'
        f'          <p class="eyebrow">Latest Episode</p>\n'
        f'          <h2>最新回</h2>\n'
        f'          <div class="featured-meta">\n'
        f'            <span class="featured-duration">▶ 1 min</span>\n'
        f'            <span class="featured-date-label">{html.escape(latest["date"])} </span>\n'
        f'          </div>\n'
        f'          <div class="episode-tags">\n'
        f'{featured_tags}'
        f'          </div>\n'
        f'          <ul class="featured-headlines">\n'
        f'{featured_headlines}\n'
        f'          </ul>\n'
        f'          <audio class="featured-audio" controls preload="none">\n'
        f'            <source src="assets/audio/sample-news-{html.escape(str(latest["date"]))}.wav" type="audio/wav" />\n'
        f'            お使いのブラウザは audio 要素に対応していません。\n'
        f'          </audio>\n'
        f'          <div class="featured-actions">\n'
        f'            <a class="button" href="days/{html.escape(str(latest["date"]))}.html">最新回を見る</a>\n'
        f'          </div>\n'
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
    text = replace_between_markers(text, '<!-- FEATURED_EPISODE_START -->', '<!-- FEATURED_EPISODE_END -->', latest_block)

    latest_three_block = (
        '      <section class="card">\n'
        '        <h2>最近の回</h2>\n'
        '        <div class="episode-grid">\n'
        f'{build_latest_cards(episodes)}\n'
        '        </div>\n'
        '      </section>'
    )
    text = replace_between_markers(text, '<!-- RECENT_EPISODES_START -->', '<!-- RECENT_EPISODES_END -->', latest_three_block)

    entries = ''.join(
        f'          <li><a href="days/{html.escape(episode["date"])}.html">{html.escape(episode["date"])} | {html.escape(episode["title"])} </a></li>\n'
        for episode in episodes
    ).rstrip()
    backnumber_block = (
        '      <section class="card">\n'
        '        <h2>バックナンバー</h2>\n'
        '        <ul>\n'
        f'{entries}\n'
        '        </ul>\n'
        '      </section>'
    )
    text = replace_between_markers(text, '<!-- BACKNUMBER_START -->', '<!-- BACKNUMBER_END -->', backnumber_block)

    index_path.write_text(text, encoding='utf-8')


if __name__ == '__main__':
    if len(sys.argv) > 2:
        raise SystemExit('Usage: ./scripts/update_index.py [YYYY-MM-DD]')
    update_index(sys.argv[1] if len(sys.argv) == 2 else None)
