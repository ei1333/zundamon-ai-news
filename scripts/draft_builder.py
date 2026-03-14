#!/usr/bin/env python3
from __future__ import annotations

from episode_utils import default_window_for
from draft_fetch import clean_title, finalize_headline
from draft_models import DraftItem
import re
import urllib.parse


def fallback_from_url(url: str, fallback_category: str, reason: str, draft_theme: dict[str, object], *, theme_name: str = 'ai') -> DraftItem:
    parsed = urllib.parse.urlparse(url)
    slug = parsed.path.rstrip('/').split('/')[-1] or parsed.netloc
    slug = urllib.parse.unquote(slug)
    slug = re.sub(r'[-_]+', ' ', slug)
    slug = re.sub(r'\b\d{4}\b', ' ', slug)
    slug = re.sub(r'\s+', ' ', slug).strip(' /')
    headline = finalize_headline(clean_title(slug.title()), theme_name, description='') if slug else '記事タイトル未取得'
    site_name = parsed.netloc.removeprefix('www.') or 'source'
    return DraftItem(
        headline=headline,
        summary=str(draft_theme.get('fallback_summary', 'URL からの自動取得に失敗したため、元記事を開いて要約を補ってください。({reason})')).format(reason=reason),
        source_name=site_name,
        url=url,
        category=fallback_category,
        tags=[fallback_category],
    )


def build_episode_text(date: str, items: list[DraftItem], draft_theme: dict[str, object], *, theme_name: str = 'ai', coverage: str = 'weekly', window: str | None = None, title: str | None = None, pick_title=None) -> str:
    resolved_title = title or (pick_title(items, draft_theme) if pick_title else str(draft_theme.get('title_fallback', '新しいAIニュース回')))
    resolved_window = window or default_window_for(date, coverage)
    summary = f'{resolved_window} の公開情報から、' + '、'.join(str(item.headline) for item in items[:3]) + 'の3本を掲載しています。'
    lines = [
        f'# {resolved_title}',
        '',
        '## Theme',
        theme_name,
        '',
        '## Coverage',
        coverage,
        '',
        '## Window',
        resolved_window,
        '',
        '## Summary',
        summary,
        '',
        '## Intro',
        str(draft_theme.get('intro', '{date} 時点の公開情報をもとに構成した下書きです。内容を確認して整えてください。')).format(date=date),
        '',
        '## Script Intro',
        str(draft_theme.get('script_intro', 'ずんだもん1分AIニュース、{date}版なのだ。')).format(date=date),
        '',
    ]
    for idx, item in enumerate(items, start=1):
        lines += [
            f'## Item {idx}',
            '### Headline',
            str(item.headline),
            '',
            '### Summary',
            str(item.summary),
            '',
            '### Tags',
            *[str(tag) for tag in item.tags],
            '',
            '### Source',
            f'[{item.source_name}]({item.url})',
            '',
            '### Script',
            '',
            '',
        ]
    lines += [
        '## Script Closing',
        str(draft_theme.get('script_closing', '以上、今日のAIニュースまとめなのだ。気になる話題は出典も見てみるのだ。')),
        '',
        '## Closing',
        str(draft_theme.get('closing', '※ この記事は公開情報をもとにした短い要約です。詳細は各出典をご確認ください。')),
        '',
    ]
    return '\n'.join(lines)
