#!/usr/bin/env python3
from __future__ import annotations

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CATEGORY_MAPPING = {
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

DEFAULT_CATEGORIES = {
    1: ('透明性', 'category-transparency'),
    2: ('研究', 'category-research'),
    3: ('インフラ', 'category-infra'),
}


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



def normalize_category(label: str, idx: int | None = None) -> tuple[str, str]:
    normalized = label.strip().lower()
    if normalized in CATEGORY_MAPPING:
        return CATEGORY_MAPPING[normalized]

    if not label.strip() and idx is not None:
        return DEFAULT_CATEGORIES.get(idx, ('AI', 'category-general'))

    return (label.strip() or 'AI', 'category-general')



def parse_episode_full(path: Path) -> tuple[dict[str, str], list[dict[str, str]]]:
    text = path.read_text(encoding='utf-8').strip()
    first_line = text.splitlines()[0].strip() if text.splitlines() else ''
    if not first_line.startswith('# '):
        raise SystemExit('Episode file must start with a # title')

    header = {
        'title': first_line[2:].strip(),
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
        category = extract_subsection(item_block, 'Category', required=False)
        category_label, category_class = normalize_category(category, idx)
        script = extract_subsection(item_block, 'Script', required=False)
        item = {
            'Headline': headline,
            'Summary': summary,
            'Category': category_label,
            'CategoryClass': category_class,
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



def build_head_html(*, title: str, description: str, url: str, stylesheet_href: str, og_type: str) -> str:
    title_text = escape_text(title)
    desc_attr = escape_attr(description)
    url_attr = escape_attr(url)
    stylesheet_attr = escape_attr(stylesheet_href)
    og_type_attr = escape_attr(og_type)
    og_image_url = escape_attr('https://ei1333.github.io/zundamon-ai-news/assets/ogp.svg')
    return '\n'.join([
        '    <meta charset="UTF-8" />',
        '    <meta name="viewport" content="width=device-width, initial-scale=1.0" />',
        f'    <title>{title_text}</title>',
        f'    <meta name="description" content="{desc_attr}" />',
        f'    <meta property="og:type" content="{og_type_attr}" />',
        f'    <meta property="og:title" content="{title_text}" />',
        f'    <meta property="og:description" content="{desc_attr}" />',
        f'    <meta property="og:url" content="{url_attr}" />',
        '    <meta property="og:site_name" content="ずんだもん1分AIニュース" />',
        f'    <meta property="og:image" content="{og_image_url}" />',
        '    <meta property="og:image:alt" content="ずんだもん1分AIニュースのOGP画像" />',
        '    <meta name="twitter:card" content="summary_large_image" />',
        f'    <meta name="twitter:title" content="{title_text}" />',
        f'    <meta name="twitter:description" content="{desc_attr}" />',
        f'    <meta name="twitter:image" content="{og_image_url}" />',
        f'    <link rel="stylesheet" href="{stylesheet_attr}" />',
    ])



def build_tag_spans(items: list[dict[str, object]], *, indent: str, category_key: str, class_key: str) -> str:
    template = load_template('partial_tag.html')
    return ''.join(
        template.format(
            indent=indent,
            category_class=escape_attr(item[class_key]),
            category_label=escape_text(item[category_key]),
        )
        for item in items
    ).rstrip()



def build_headline_items(items: list[dict[str, object]], *, indent: str, headline_key: str) -> str:
    template = load_template('partial_headline_item.html')
    return ''.join(
        template.format(
            indent=indent,
            headline=escape_text(item[headline_key]),
        )
        for item in items
    ).rstrip()



def parse_episode_summary(path: Path) -> dict[str, object]:
    header, items = parse_episode_full(path)
    return {
        'date': path.stem,
        'title': header['title'],
        'summary': header['summary'],
        'items': [
            {
                'headline': item['Headline'],
                'category_label': item['Category'],
                'category_class': item['CategoryClass'],
            }
            for item in items
        ],
    }
