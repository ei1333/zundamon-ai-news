#!/usr/bin/env python3
from __future__ import annotations

import sys

from episode_utils import ROOT, build_head_html, escape_attr, escape_text, load_template, parse_episode_summary


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
    return load_template('index_featured.html').format(
        date=escape_text(episode['date']),
        date_attr=escape_attr(episode['date']),
        title=escape_text(episode['title']),
        tags_html=render_episode_tags(episode['items'], '            ').rstrip(),
        headlines_html=render_headlines(episode['items'], '            '),
    )



def build_recent_html(episodes: list[dict[str, object]]) -> str:
    cards = []
    template = load_template('index_recent_card.html')
    for episode in episodes[1:3]:
        cards.append(
            template.format(
                date=escape_text(episode['date']),
                date_attr=escape_attr(episode['date']),
                title=escape_text(episode['title']),
                summary=escape_text(episode['summary']),
                tags_html=render_episode_tags(episode['items'], '              ').rstrip(),
                headlines_html=render_headlines(episode['items'], '              '),
            ).rstrip()
        )
    return '\n'.join(cards)



def build_backnumber_html(episodes: list[dict[str, object]]) -> str:
    template = load_template('index_backnumber_item.html')
    return ''.join(
        template.format(
            date=escape_text(episode['date']),
            date_attr=escape_attr(episode['date']),
            title=escape_text(episode['title']),
        )
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
        head_html=build_head_html(
            title='ずんだもん1分AIニュース',
            description='公開情報をもとに独自要約したAIニュースを、ずんだもんの声で1分前後にまとめてお届けします。',
            url='https://ei1333.github.io/zundamon-ai-news/',
            stylesheet_href='assets/style.css',
            og_type='website',
        ),
        featured_html=build_featured_html(latest),
        recent_html=build_recent_html(episodes),
        backnumber_html=build_backnumber_html(episodes),
    )
    index_path.write_text(html_text, encoding='utf-8')


if __name__ == '__main__':
    if len(sys.argv) > 2:
        raise SystemExit('Usage: ./scripts/update_index.py [YYYY-MM-DD]')
    update_index(sys.argv[1] if len(sys.argv) == 2 else None)
