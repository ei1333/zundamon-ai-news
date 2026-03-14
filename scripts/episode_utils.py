#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path

from episode_models import EpisodeDocument, EpisodeHeader, EpisodeItem, EpisodeTag
from index_models import IndexDisplayTag, IndexEpisodeSummary, IndexEpisodeTagSummary

ROOT = Path(__file__).resolve().parent.parent


def validate_theme_config(theme: dict, *, theme_name: str = 'ai') -> dict:
    required_top_level = ['site_name', 'site_url', 'hero', 'index', 'day', 'ogp', 'episode_template', 'draft', 'categories']
    for key in required_top_level:
        if key not in theme:
            raise SystemExit(f'Theme `{theme_name}` is missing required key: {key}')

    for key in ['hero', 'index', 'day', 'ogp', 'episode_template', 'draft', 'categories']:
        if not isinstance(theme.get(key), dict):
            raise SystemExit(f'Theme `{theme_name}` key `{key}` must be an object')

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

    for idx, rule in enumerate(draft.get('category_rules', []), start=1):
        if not isinstance(rule, dict) or 'label' not in rule or 'keywords' not in rule:
            raise SystemExit(f'Theme `{theme_name}` draft.category_rules[{idx}] must contain label and keywords')
        if not isinstance(rule.get('keywords'), list):
            raise SystemExit(f'Theme `{theme_name}` draft.category_rules[{idx}].keywords must be a list')

    for idx, rule in enumerate(draft.get('tag_rules', []), start=1):
        if not isinstance(rule, dict) or 'label' not in rule or 'keywords' not in rule:
            raise SystemExit(f'Theme `{theme_name}` draft.tag_rules[{idx}] must contain label and keywords')
        if not isinstance(rule.get('keywords'), list):
            raise SystemExit(f'Theme `{theme_name}` draft.tag_rules[{idx}].keywords must be a list')

    for name, meta in theme.get('categories', {}).items():
        if not isinstance(meta, dict):
            raise SystemExit(f'Theme `{theme_name}` categories.{name} must be an object')
        if 'label' not in meta or 'class' not in meta:
            raise SystemExit(f'Theme `{theme_name}` categories.{name} must contain label and class')

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



def parse_source_block(text: str) -> tuple[str, str]:
    markdown_link = re.search(r'\[([^\]]+)\]\((https?://[^\)]+)\)', text)
    if markdown_link:
        return markdown_link.group(1).strip(), markdown_link.group(2).strip()

    name_match = re.search(r'^- Name:\s*(.+)$', text, flags=re.MULTILINE)
    url_match = re.search(r'^- URL:\s*(.+)$', text, flags=re.MULTILINE)
    if name_match and url_match:
        return name_match.group(1).strip(), url_match.group(1).strip()

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


def parse_tags_block(text: str, *, idx: int | None = None, theme_name: str = 'ai') -> list[EpisodeTag]:
    raw = text.strip()
    if not raw:
        label, css_class = normalize_category('', idx, theme_name=theme_name)
        return [EpisodeTag(label=label, css_class=css_class)]

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
        tags.append(EpisodeTag(label=label, css_class=css_class))

    if tags:
        return tags

    label, css_class = normalize_category('', idx, theme_name=theme_name)
    return [EpisodeTag(label=label, css_class=css_class)]


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



def parse_episode_full(path: Path, *, theme_name: str = 'ai') -> EpisodeDocument:
    text = path.read_text(encoding='utf-8').strip()
    first_line = text.splitlines()[0].strip() if text.splitlines() else ''
    if not first_line.startswith('# '):
        raise SystemExit('Episode file must start with a # title')

    metadata = parse_episode_metadata(path)
    header = EpisodeHeader(
        title=first_line[2:].strip(),
        theme=metadata['theme'],
        coverage=metadata['coverage'],
        window=metadata['window'],
        summary=extract_section(text, 'Summary'),
        intro=extract_section(text, 'Intro'),
        script_intro=extract_section(text, 'Script Intro'),
        script_closing=extract_section(text, 'Script Closing'),
        closing=extract_section(text, 'Closing'),
    )

    items: list[EpisodeItem] = []
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
            tags = [EpisodeTag(label=category_label, css_class=category_class)]
        script = extract_subsection(item_block, 'Script', required=False)
        source_name, source_url = parse_source_block(extract_subsection(item_block, 'Source'))
        items.append(EpisodeItem(
            headline=headline,
            summary=summary,
            source_name=source_name,
            source_url=source_url,
            category=tags[0].label,
            category_class=tags[0].css_class,
            tags=tags,
            script=script or auto_script(headline, summary, idx),
        ))

    return EpisodeDocument(header=header, items=items)



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



def build_tag_spans(items: list[object], *, indent: str, category_key: str, class_key: str) -> str:
    template = load_template('partial_tag.html')
    spans: list[str] = []
    for item in items:
        tags = getattr(item, 'tags', None)
        if tags is None and isinstance(item, dict):
            tags = item.get('Tags') or item.get('tags')
        if isinstance(tags, list) and tags:
            for tag in tags:
                if isinstance(tag, dict):
                    tag_class = tag.get('css_class') or tag.get('class', 'category-general')
                    tag_label = tag.get('label', '')
                else:
                    tag_class = getattr(tag, 'css_class', 'category-general')
                    tag_label = getattr(tag, 'label', '')
                spans.append(
                    template.format(
                        indent=indent,
                        tag_class=escape_attr(tag_class),
                        tag_label=escape_text(tag_label),
                    )
                )
        else:
            if isinstance(item, dict):
                tag_class = item[class_key]
                tag_label = item[category_key]
            else:
                tag_class = getattr(item, class_key)
                tag_label = getattr(item, category_key)
            spans.append(
                template.format(
                    indent=indent,
                    tag_class=escape_attr(tag_class),
                    tag_label=escape_text(tag_label),
                )
            )
    return ''.join(spans).rstrip()



def build_headline_items(items: list[object], *, indent: str, headline_key: str) -> str:
    template = load_template('partial_headline_item.html')
    rendered: list[str] = []
    for item in items:
        headline = item[headline_key] if isinstance(item, dict) else getattr(item, headline_key)
        rendered.append(template.format(indent=indent, headline=escape_text(headline)))
    return ''.join(rendered).rstrip()



def dedupe_index_tags(items: list[IndexEpisodeTagSummary]) -> list[IndexDisplayTag]:
    deduped: list[IndexDisplayTag] = []
    seen: set[tuple[str, str]] = set()
    for item in items:
        for tag in item.tags:
            key = (str(tag.get('label', '')), str(tag.get('css_class', '')))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(IndexDisplayTag(label=key[0], css_class=key[1]))
    return deduped


def parse_episode_summary(path: Path, *, theme_name: str = 'ai') -> IndexEpisodeSummary:
    episode_theme_name = detect_episode_theme(path)
    document = parse_episode_full(path, theme_name=episode_theme_name)
    theme = load_theme(episode_theme_name)
    items = [
        IndexEpisodeTagSummary(
            headline=item.headline,
            category_label=item.category,
            category_class=item.category_class,
            tags=[{'label': tag.label, 'css_class': tag.css_class} for tag in item.tags],
        )
        for item in document.items
    ]
    return IndexEpisodeSummary(
        date=path.stem,
        title=document.header.title,
        summary=document.header.summary,
        coverage=document.header.coverage,
        window=document.header.window,
        theme_name=episode_theme_name,
        theme_label=str(theme.get('theme_label', theme.get('site_name', ''))),
        items=items,
        display_tags=dedupe_index_tags(items),
    )



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
