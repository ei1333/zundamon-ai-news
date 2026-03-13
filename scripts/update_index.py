#!/usr/bin/env python3
from __future__ import annotations

import sys

from episode_utils import ROOT, escape_attr, escape_text, load_template, parse_episode_summary


def list_episodes() -> list[dict[str, str]]:
    paths = sorted((ROOT / 'episodes').glob('*.md'), key=lambda p: p.stem, reverse=True)
    return [parse_episode_summary(path) for path in paths if path.name != '_template.md']


def render_episode_tags(items: list[dict[str, object]], indent: str) -> str:
    return ''.join(
        f'{indent}<span class="episode-tag {escape_attr(item["category_class"])}">{escape_text(item["category_label"])}</span>\n'
        for item in items
    )



def render_headlines(items: list[dict[str, object]], indent: str) -> str:
    return '\n'.join(
        f'{indent}<li>{escape_text(item["headline"])}</li>' for item in items
    )



def build_featured_html(episode: dict[str, object]) -> str:
    date = escape_text(episode['date'])
    title = escape_text(episode['title'])
    tags = render_episode_tags(episode['items'], '            ')
    headlines = render_headlines(episode['items'], '            ')
    return (
        '      <section class="card featured-card">\n'
        '        <div class="featured-copy">\n'
        '          <p class="eyebrow">Latest Episode</p>\n'
        '          <h2>最新回</h2>\n'
        '          <div class="featured-meta">\n'
        '            <span class="featured-duration">▶ 1 min</span>\n'
        f'            <span class="featured-date-label">{date} </span>\n'
        '          </div>\n'
        '          <div class="episode-tags">\n'
        f'{tags}'
        '          </div>\n'
        '          <ul class="featured-headlines">\n'
        f'{headlines}\n'
        '          </ul>\n'
        '          <audio class="featured-audio" controls preload="none">\n'
        f'            <source src="assets/audio/sample-news-{escape_attr(episode["date"])}.wav" type="audio/wav" />\n'
        '            お使いのブラウザは audio 要素に対応していません。\n'
        '          </audio>\n'
        '          <div class="featured-actions">\n'
        f'            <a class="button" href="days/{escape_attr(episode["date"])}.html">最新回を見る</a>\n'
        '          </div>\n'
        '        </div>\n'
        '        <div class="featured-visual" aria-hidden="true">\n'
        '          <div class="featured-badge">ON AIR</div>\n'
        '          <div class="featured-screen">\n'
        '            <div class="featured-logo">ずんだもん<span>1分AIニュース</span></div>\n'
        f'            <p class="featured-screen-date">{date}</p>\n'
        f'            <p class="featured-screen-title">{title}</p>\n'
        '            <div class="featured-wave"></div>\n'
        '          </div>\n'
        '        </div>\n'
        '      </section>'
    )



def build_recent_html(episodes: list[dict[str, object]]) -> str:
    cards = []
    for episode in episodes[1:3]:
        date = escape_text(episode['date'])
        title = escape_text(episode['title'])
        summary = escape_text(episode['summary'])
        tags = render_episode_tags(episode['items'], '              ')
        headlines = render_headlines(episode['items'], '              ')
        cards.append(
            '          <article class="episode-card">\n'
            f'            <p class="episode-date">{date}</p>\n'
            f'            <h3><a href="days/{escape_attr(episode["date"])}.html">{title}</a></h3>\n'
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



def build_backnumber_html(episodes: list[dict[str, object]]) -> str:
    return ''.join(
        f'          <li><a href="days/{escape_attr(episode["date"])}.html">{escape_text(episode["date"])} | {escape_text(episode["title"])} </a></li>\n'
        for episode in episodes
    ).rstrip()



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
    html_text = load_template('index.html').format(
        og_image_url=escape_attr('https://ei1333.github.io/zundamon-ai-news/assets/ogp.svg'),
        featured_html=build_featured_html(latest),
        recent_html=build_recent_html(episodes),
        backnumber_html=build_backnumber_html(episodes),
    )
    index_path.write_text(html_text, encoding='utf-8')


if __name__ == '__main__':
    if len(sys.argv) > 2:
        raise SystemExit('Usage: ./scripts/update_index.py [YYYY-MM-DD]')
    update_index(sys.argv[1] if len(sys.argv) == 2 else None)
