#!/usr/bin/env python3
from __future__ import annotations

import sys

from episode_utils import (
    ROOT,
    build_head_html,
    build_headline_items,
    build_tag_spans,
    escape_attr,
    escape_text,
    load_template,
    load_theme,
    parse_episode_summary,
)


def list_episodes() -> list[dict[str, str]]:
    paths = sorted((ROOT / 'episodes').glob('*.md'), key=lambda p: p.stem, reverse=True)
    return [parse_episode_summary(path) for path in paths if path.name != '_template.md']



def build_featured_html(episode: dict[str, object]) -> str:
    return load_template('index_featured.html').format(
        date=escape_text(episode['date']),
        date_attr=escape_attr(episode['date']),
        title=escape_text(episode['title']),
        tags_html=build_tag_spans(
            episode['items'], indent='            ', category_key='category_label', class_key='category_class'
        ),
        headlines_html=build_headline_items(
            episode['items'], indent='            ', headline_key='headline'
        ),
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
                tags_html=build_tag_spans(
                    episode['items'], indent='              ', category_key='category_label', class_key='category_class'
                ),
                headlines_html=build_headline_items(
                    episode['items'], indent='              ', headline_key='headline'
                ),
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
    theme = load_theme()
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
            title=theme['site_name'],
            description=theme['hero']['lead'],
            url=theme['site_url'],
            stylesheet_href='assets/style.css',
            og_type='website',
        ),
        hero_eyebrow=escape_text(theme['hero']['eyebrow']),
        hero_title=escape_text(theme['hero']['title']),
        hero_lead=escape_text(theme['hero']['lead']),
        featured_html=build_featured_html(latest),
        recent_heading=escape_text(theme['index']['recent_heading']),
        recent_html=build_recent_html(episodes),
        backnumber_heading=escape_text(theme['index']['backnumber_heading']),
        backnumber_html=build_backnumber_html(episodes),
        credits_heading=escape_text(theme['index']['credits_heading']),
        credits_voice=escape_text(theme['index']['credits_voice']),
    )
    index_path.write_text(html_text, encoding='utf-8')


if __name__ == '__main__':
    if len(sys.argv) > 2:
        raise SystemExit('Usage: ./scripts/update_index.py [YYYY-MM-DD]')
    update_index(sys.argv[1] if len(sys.argv) == 2 else None)
