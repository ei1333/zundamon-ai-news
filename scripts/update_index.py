#!/usr/bin/env python3
from __future__ import annotations

import argparse

from index_models import IndexEpisodeSummary, IndexThemeFilter, IndexViewModel
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


def list_episodes(*, site_theme_name: str = 'ai') -> list[IndexEpisodeSummary]:
    paths = sorted((ROOT / 'episodes').glob('*.md'), key=lambda p: p.stem, reverse=True)
    return [parse_episode_summary(path, theme_name=site_theme_name) for path in paths if path.name != '_template.md']



def build_featured_html(episode: IndexEpisodeSummary) -> str:
    return load_template('index_featured.html').format(
        date=escape_text(episode.date),
        date_attr=escape_attr(episode.date),
        title=escape_text(episode.title),
        theme_label=escape_text(episode.theme_label),
        theme_name_attr=escape_attr(episode.theme_name),
        tags_html=build_tag_spans(
            episode.items, indent='            ', category_key='category_label', class_key='category_class'
        ),
        headlines_html=build_headline_items(
            episode.items, indent='            ', headline_key='headline'
        ),
    )



def build_recent_html(episodes: list[IndexEpisodeSummary]) -> str:
    cards = []
    template = load_template('index_recent_card.html')
    for episode in episodes[1:4]:
        cards.append(
            template.format(
                date=escape_text(episode.date),
                date_attr=escape_attr(episode.date),
                title=escape_text(episode.title),
                summary=escape_text(episode.summary),
                theme_label=escape_text(episode.theme_label),
                theme_name_attr=escape_attr(episode.theme_name),
                tags_html=build_tag_spans(
                    episode.items, indent='              ', category_key='category_label', class_key='category_class'
                ),
                headlines_html=build_headline_items(
                    episode.items, indent='              ', headline_key='headline'
                ),
            ).rstrip()
        )
    return '\n'.join(cards)



def build_backnumber_html(episodes: list[IndexEpisodeSummary]) -> str:
    template = load_template('index_backnumber_item.html')
    return ''.join(
        template.format(
            date=escape_text(episode.date),
            date_attr=escape_attr(episode.date),
            title=escape_text(episode.title),
            theme_label=escape_text(episode.theme_label),
            theme_name_attr=escape_attr(episode.theme_name),
        )
        for episode in episodes
    ).rstrip()



def build_theme_filters_html(filters: list[IndexThemeFilter]) -> str:
    return '\n'.join(
        f'          <button class="theme-filter-button" type="button" data-theme-filter="{escape_attr(item.theme_name)}" aria-pressed="false">{escape_text(item.label)}</button>'
        for item in filters
    )


def build_index_view_model(target_date: str | None = None, *, site_theme_name: str = 'ai') -> IndexViewModel:
    theme = load_theme(site_theme_name)
    episodes = list_episodes(site_theme_name=site_theme_name)
    if not episodes:
        raise SystemExit('No episodes found')

    featured = episodes[0]
    if target_date is not None:
        matched = [episode for episode in episodes if episode.date == target_date]
        if not matched:
            raise SystemExit(f'Episode not found for date: {target_date}')
        featured = matched[0]

    available = {episode.theme_name for episode in episodes}
    ordered = [('all', 'すべて'), ('ai', 'AI'), ('shogi', '将棋'), ('vocaloid', 'ボーカロイド')]
    filters = [IndexThemeFilter(theme_name=name, label=label) for name, label in ordered if name == 'all' or name in available]

    return IndexViewModel(
        site_theme_name=site_theme_name,
        hero_eyebrow=str(theme['hero']['eyebrow']),
        hero_title=str(theme['hero']['title']),
        hero_lead=str(theme['hero']['lead']),
        recent_heading=str(theme['index']['recent_heading']),
        backnumber_heading=str(theme['index']['backnumber_heading']),
        credits_heading=str(theme['index']['credits_heading']),
        credits_voice=str(theme['index']['credits_voice']),
        featured_episode=featured,
        recent_episodes=episodes[1:4],
        all_episodes=episodes,
        theme_filters=filters,
    )



def update_index(target_date: str | None = None, *, site_theme_name: str = 'ai') -> None:
    view = build_index_view_model(target_date, site_theme_name=site_theme_name)
    theme = load_theme(view.site_theme_name)

    index_path = ROOT / 'index.html'
    html_text = load_template('index.html').format(
        head_html=build_head_html(
            title=theme['site_name'],
            description=view.hero_lead,
            url=theme['site_url'],
            stylesheet_href='assets/style.css',
            og_type='website',
            theme_name=view.site_theme_name,
        ),
        hero_eyebrow=escape_text(view.hero_eyebrow),
        hero_title=escape_text(view.hero_title),
        hero_lead=escape_text(view.hero_lead),
        featured_html=build_featured_html(view.featured_episode),
        theme_filters_html=build_theme_filters_html(view.theme_filters),
        recent_heading=escape_text(view.recent_heading),
        recent_html=build_recent_html(view.all_episodes),
        backnumber_heading=escape_text(view.backnumber_heading),
        backnumber_html=build_backnumber_html(view.all_episodes),
        credits_heading=escape_text(view.credits_heading),
        credits_voice=escape_text(view.credits_voice),
    )
    index_path.write_text(html_text, encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Rebuild index.html from episodes.')
    parser.add_argument('date', nargs='?', help='Optional featured episode date YYYY-MM-DD')
    parser.add_argument('--site-theme', '--theme', dest='site_theme', default='ai', help='Site-level theme for index branding and OGP. Episode cards still use each episode\'s own ## Theme.')
    args = parser.parse_args()
    update_index(args.date, site_theme_name=args.site_theme)
