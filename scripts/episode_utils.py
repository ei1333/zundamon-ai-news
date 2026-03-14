#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def validate_theme_config(theme: dict, *, theme_name: str = 'ai') -> dict:
    required_top_level = ['site_name', 'site_url', 'hero', 'index', 'day', 'ogp', 'episode_template', 'draft', 'categories']
    for key in required_top_level:
        if key not in theme:
            raise SystemExit(f'Theme `{theme_name}` is missing required key: {key}')

    required_draft_keys = ['default_categories', 'intro', 'script_intro', 'script_closing', 'closing', 'title_fallback', 'category_rules']
    draft = theme.get('draft', {})
    for key in required_draft_keys:
        if key not in draft:
            raise SystemExit(f'Theme `{theme_name}` draft is missing required key: {key}')

    if not isinstance(draft.get('default_categories'), list):
        raise SystemExit(f'Theme `{theme_name}` draft.default_categories must be a list')
    if not isinstance(draft.get('category_rules'), list):
        raise SystemExit(f'Theme `{theme_name}` draft.category_rules must be a list')
    if 'tag_rules' in draft and not isinstance(draft.get('tag_rules'), list):
        raise SystemExit(f'Theme `{theme_name}` draft.tag_rules must be a list when present')

    return theme


@lru_cache(maxsize=None)
def load_theme(theme_name: str = 'ai') -> dict:
    normalized_theme = {'default': 'ai'}.get(theme_name, theme_name)
    candidates = [ROOT / 'config' / 'themes' / f'{normalized_theme}.json']
    if normalized_theme == 'ai':
        candidates.extend([
            ROOT / 'config' / 'themes' / 'default.json',
            ROOT / 'config' / 'theme.json',
        ])

    for path in candidates:
        if path.exists():
            return validate_theme_config(json.loads(path.read_text(encoding='utf-8')), theme_name=normalized_theme)

    searched = ', '.join(str(path) for path in candidates)
    raise SystemExit(f'Theme config not found. Searched: {searched}')


@lru_cache(maxsize=None)
def category_mapping(theme_name: str = 'ai') -> dict[str, tuple[str, str]]:
    theme = load_theme(theme_name)
    mapping: dict[str, tuple[str, str]] = {}
    for key, value in theme.get('categories', {}).items():
        label = value.get('label', key)
        css_class = value.get('class', 'category-general')
        mapping[key.strip().lower()] = (label, css_class)
        for alias in value.get('aliases', []):
            mapping[str(alias).strip().lower()] = (label, css_class)
    return mapping


@lru_cache(maxsize=None)
def default_categories(theme_name: str = 'ai') -> dict[int, tuple[str, str]]:
    theme = load_theme(theme_name)
    labels = theme.get('draft', {}).get('default_categories', [])
    mapping = category_mapping(theme_name)
    resolved: dict[int, tuple[str, str]] = {}
    for idx, label in enumerate(labels, start=1):
        resolved[idx] = mapping.get(str(label).strip().lower(), (label, 'category-general'))
    return resolved


def extract_section(text: str, heading: str) -> str:
    pattern = rf'^## {re.escape(heading)}\n(.*?)(?=^## |\Z)'
    match = re.search(pattern, text, flags=re.MULTILINE | re.DOTALL)
    if not match:
        raise SystemExit(f'Missing section: {heading}')
    return match.group(1).strip()



def extract_subsection(text: str, heading: str, required: bool = True) -> str:
    pattern = rf'^### {re.escape(heading)}\n(.*?)(?=^### |\Z)'
    match = re.search(pattern, text, flags=re.MULTILINE | re.DOTALL)
    if not match:
        if required:
            raise SystemExit(f'Missing subsection: {heading}')
        return ''
    return match.group(1).strip()



def parse_source_block(text: str) -> dict[str, str]:
    markdown_link = re.search(r'\[([^\]]+)\]\((https?://[^\)]+)\)', text)
    if markdown_link:
        return {
            'SourceName': markdown_link.group(1).strip(),
            'SourceURL': markdown_link.group(2).strip(),
        }

    name_match = re.search(r'^- Name:\s*(.+)$', text, flags=re.MULTILINE)
    url_match = re.search(r'^- URL:\s*(.+)$', text, flags=re.MULTILINE)
    if name_match and url_match:
        return {
            'SourceName': name_match.group(1).strip(),
            'SourceURL': url_match.group(1).strip(),
        }

    raise SystemExit('Source section must contain [Name](URL) or - Name: / - URL:')



def auto_script(headline: str, summary: str, idx: int) -> str:
    summary = re.sub(r'\s+', ' ', summary).strip()
    return f'{idx}本目なのだ。{headline}なのだ。{summary}'



def normalize_category(label: str, idx: int | None = None, *, theme_name: str = 'ai') -> tuple[str, str]:
    normalized = label.strip().lower()
    mapping = category_mapping(theme_name)
    if normalized in mapping:
        return mapping[normalized]

    if not label.strip() and idx is not None:
        return default_categories(theme_name).get(idx, ('AI', 'category-general'))

    return (label.strip() or 'AI', 'category-general')


def parse_tags_block(text: str, *, idx: int | None = None, theme_name: str = 'ai') -> list[dict[str, str]]:
    raw = text.strip()
    if not raw:
        label, css_class = normalize_category('', idx, theme_name=theme_name)
        return [{'label': label, 'class': css_class}]

    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    if len(lines) == 1:
        candidates = [part.strip() for part in re.split(r'[、,]', lines[0]) if part.strip()]
    else:
        candidates = [re.sub(r'^[-*]\s*', '', line).strip() for line in lines]
        candidates = [tag for tag in candidates if tag]

    tags = []
    seen = set()
    for candidate in candidates:
        label, css_class = normalize_category(candidate, None, theme_name=theme_name)
        key = (label, css_class)
        if key in seen:
            continue
        seen.add(key)
        tags.append({'label': label, 'class': css_class})

    if tags:
        return tags

    label, css_class = normalize_category('', idx, theme_name=theme_name)
    return [{'label': label, 'class': css_class}]


def parse_iso_date(value: str) -> datetime:
    return datetime.strptime(value, '%Y-%m-%d')


def default_window_for(date: str, coverage: str) -> str:
    if coverage == 'weekly':
        end = parse_iso_date(date)
        start = end - timedelta(days=6)
        return f'{start:%Y-%m-%d}..{end:%Y-%m-%d}'
    return f'{date}..{date}'


def parse_episode_metadata(path: Path) -> dict[str, str]:
    text = path.read_text(encoding='utf-8')
    explicit_theme = extract_section(text, 'Theme') if re.search(r'^## Theme\n', text, flags=re.MULTILINE) else ''
    theme = explicit_theme.strip().lower()
    if not theme:
        lowered = text.lower()
        shogi_keywords = [
            '将棋', '叡王', '王将', '王位', '王座', '名人', '棋王', '棋聖', '竜王',
            '女流', '順位戦', '挑戦者決定', '棋士', '八段', '九段'
        ]
        theme = 'shogi' if any(keyword.lower() in lowered for keyword in shogi_keywords) else 'ai'

    coverage = extract_section(text, 'Coverage').strip().lower() if re.search(r'^## Coverage\n', text, flags=re.MULTILINE) else 'daily'
    window = extract_section(text, 'Window').strip() if re.search(r'^## Window\n', text, flags=re.MULTILINE) else default_window_for(path.stem, coverage)
    return {
        'theme': theme,
        'coverage': coverage,
        'window': window,
    }


@lru_cache(maxsize=None)
def detect_episode_theme(path: Path) -> str:
    return parse_episode_metadata(path)['theme']



def parse_episode_full(path: Path, *, theme_name: str = 'ai') -> tuple[dict[str, str], list[dict[str, str]]]:
    text = path.read_text(encoding='utf-8').strip()
    first_line = text.splitlines()[0].strip() if text.splitlines() else ''
    if not first_line.startswith('# '):
        raise SystemExit('Episode file must start with a # title')

    metadata = parse_episode_metadata(path)
    header = {
        'title': first_line[2:].strip(),
        'theme': metadata['theme'],
        'coverage': metadata['coverage'],
        'window': metadata['window'],
        'summary': extract_section(text, 'Summary'),
        'intro': extract_section(text, 'Intro'),
        'script_intro': extract_section(text, 'Script Intro'),
        'script_closing': extract_section(text, 'Script Closing'),
        'closing': extract_section(text, 'Closing'),
    }

    items: list[dict[str, str]] = []
    for idx in range(1, 4):
        item_block = extract_section(text, f'Item {idx}')
        headline = extract_subsection(item_block, 'Headline')
        summary = extract_subsection(item_block, 'Summary')
        tags_text = extract_subsection(item_block, 'Tags', required=False)
        category = extract_subsection(item_block, 'Category', required=False)
        if tags_text:
            tags = parse_tags_block(tags_text, idx=idx, theme_name=theme_name)
        else:
            category_label, category_class = normalize_category(category, idx, theme_name=theme_name)
            tags = [{'label': category_label, 'class': category_class}]
        script = extract_subsection(item_block, 'Script', required=False)
        item = {
            'Headline': headline,
            'Summary': summary,
            'Category': tags[0]['label'],
            'CategoryClass': tags[0]['class'],
            'Tags': tags,
            'Script': script or auto_script(headline, summary, idx),
        }
        item.update(parse_source_block(extract_subsection(item_block, 'Source')))
        items.append(item)

    return header, items



def load_template(name: str) -> str:
    path = ROOT / 'scripts' / 'templates' / name
    if not path.exists():
        raise SystemExit(f'Template not found: {path}')
    return path.read_text(encoding='utf-8')



def escape_text(value: str) -> str:
    return html.escape(str(value))



def escape_attr(value: str) -> str:
    return html.escape(str(value), quote=True)



def build_head_html(*, title: str, description: str, url: str, stylesheet_href: str, og_type: str, og_image_url: str | None = None, theme_name: str = 'ai') -> str:
    theme = load_theme(theme_name)
    title_text = escape_text(title)
    desc_attr = escape_attr(description)
    url_attr = escape_attr(url)
    stylesheet_attr = escape_attr(stylesheet_href)
    og_type_attr = escape_attr(og_type)
    resolved_og_image_url = escape_attr(og_image_url or theme.get('og_image_url', f"{theme.get('site_url', '').rstrip('/')}/assets/ogp.png"))
    site_name = escape_attr(theme.get('site_name', 'Site'))
    site_image_alt = escape_attr(theme.get('ogp', {}).get('site_image_alt', f"{theme.get('site_name', 'Site')}のOGP画像"))
    return '\n'.join([
        '    <meta charset="UTF-8" />',
        '    <meta name="viewport" content="width=device-width, initial-scale=1.0" />',
        f'    <title>{title_text}</title>',
        f'    <meta name="description" content="{desc_attr}" />',
        f'    <meta property="og:type" content="{og_type_attr}" />',
        f'    <meta property="og:title" content="{title_text}" />',
        f'    <meta property="og:description" content="{desc_attr}" />',
        f'    <meta property="og:url" content="{url_attr}" />',
        f'    <meta property="og:site_name" content="{site_name}" />',
        f'    <meta property="og:image" content="{resolved_og_image_url}" />',
        f'    <meta property="og:image:alt" content="{site_image_alt}" />',
        '    <meta name="twitter:card" content="summary_large_image" />',
        f'    <meta name="twitter:title" content="{title_text}" />',
        f'    <meta name="twitter:description" content="{desc_attr}" />',
        f'    <meta name="twitter:image" content="{resolved_og_image_url}" />',
        f'    <link rel="stylesheet" href="{stylesheet_attr}" />',
    ])



def build_tag_spans(items: list[dict[str, object]], *, indent: str, category_key: str, class_key: str) -> str:
    template = load_template('partial_tag.html')
    spans: list[str] = []
    for item in items:
        tags = item.get('Tags')
        if isinstance(tags, list) and tags:
            for tag in tags:
                spans.append(
                    template.format(
                        indent=indent,
                        tag_class=escape_attr(tag.get('class', 'category-general')),
                        tag_label=escape_text(tag.get('label', '')),
                    )
                )
        else:
            spans.append(
                template.format(
                    indent=indent,
                    tag_class=escape_attr(item[class_key]),
                    tag_label=escape_text(item[category_key]),
                )
            )
    return ''.join(spans).rstrip()



def build_headline_items(items: list[dict[str, object]], *, indent: str, headline_key: str) -> str:
    template = load_template('partial_headline_item.html')
    return ''.join(
        template.format(
            indent=indent,
            headline=escape_text(item[headline_key]),
        )
        for item in items
    ).rstrip()



def parse_episode_summary(path: Path, *, theme_name: str = 'ai') -> dict[str, object]:
    episode_theme_name = detect_episode_theme(path)
    header, items = parse_episode_full(path, theme_name=episode_theme_name)
    theme = load_theme(episode_theme_name)
    return {
        'date': path.stem,
        'title': header['title'],
        'summary': header['summary'],
        'coverage': header['coverage'],
        'window': header['window'],
        'theme_name': episode_theme_name,
        'theme_label': theme.get('theme_label', theme.get('site_name', '')),
        'items': [
            {
                'headline': item['Headline'],
                'category_label': item['Category'],
                'category_class': item['CategoryClass'],
            }
            for item in items
        ],
    }



def build_episode_template_text(date: str, *, title: str | None = None, theme_name: str = 'ai', coverage: str = 'weekly', window: str | None = None) -> str:
    theme = load_theme(theme_name)
    template = theme.get('episode_template', {})
    resolved_title = title or template.get('default_title', '新しいニュース回')
    category_labels = theme.get('draft', {}).get('default_categories', ['トピック1', 'トピック2', 'トピック3'])
    category_labels = (category_labels + ['トピック1', 'トピック2', 'トピック3'])[:3]
    resolved_window = window or default_window_for(date, coverage)

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
        template.get('summary', 'YYYY-MM-DD の回です。').replace('YYYY-MM-DD', date),
        '',
        '## Intro',
        template.get('intro', 'YYYY-MM-DD 時点の公開情報をもとに構成した回です。').replace('YYYY-MM-DD', date),
        '',
        '## Script Intro',
        template.get('script_intro', 'YYYY-MM-DD版なのだ。').replace('YYYY-MM-DD', date),
        '',
    ]

    item_summary_defaults = [
        'ここに要約を書く。2〜3文で短く、何が起きたかと意味が伝わるようにまとめる。',
        'ここに要約を書く。異なる角度の話題を混ぜると収まりが良い。',
        'ここに要約を書く。1分音声に合わせるなら、3本で全体250〜350字程度が目安。',
    ]

    for idx in range(1, 4):
        lines += [
            f'## Item {idx}',
            '### Headline',
            f'ニュース見出し{idx}',
            '',
            '### Summary',
            item_summary_defaults[idx - 1],
            '',
            '### Tags',
            category_labels[idx - 1],
            '',
            '### Source',
            f'[Source {idx}](https://example.com/source-{idx})',
            '',
            '### Script',
            '',
            '',
            '',
        ]

    lines += [
        '## Script Closing',
        template.get('script_closing', '今日のひとことなのだ。ここに締めのひとことを入れるのだ。'),
        '',
        '## Closing',
        template.get('closing', '※ 詳細は各出典をご確認ください。'),
        '',
    ]
    return '\n'.join(lines)
