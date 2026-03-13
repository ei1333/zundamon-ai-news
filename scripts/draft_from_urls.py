#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

USER_AGENT = 'zundamon-ai-news/0.1 (+https://ei1333.github.io/zundamon-ai-news/)'
DEFAULT_CATEGORIES = ['透明性', '研究', 'インフラ']

CATEGORY_RULES = [
    ('透明性', ['policy', 'regulation', 'law', 'govern', 'transparency', 'disclosure', 'copyright', 'safety', 'trust']),
    ('研究', ['research', 'study', 'paper', 'model', 'benchmark', 'science', 'university', 'lab']),
    ('インフラ', ['chip', 'gpu', 'datacenter', 'data center', 'cloud', 'semiconductor', 'infra', 'infrastructure', 'network', 'server']),
]


def fetch_url(url: str) -> str:
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req, timeout=20) as resp:
        charset = resp.headers.get_content_charset() or 'utf-8'
        data = resp.read()
    return data.decode(charset, errors='replace')



def strip_tags(text: str) -> str:
    text = re.sub(r'<script\b[^>]*>.*?</script>', ' ', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<style\b[^>]*>.*?</style>', ' ', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()



def find_meta(html_text: str, attr_name: str, attr_value: str) -> str | None:
    patterns = [
        rf'<meta[^>]+{attr_name}=["\']{re.escape(attr_value)}["\'][^>]+content=["\']([^"\']+)["\']',
        rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+{attr_name}=["\']{re.escape(attr_value)}["\']',
    ]
    for pattern in patterns:
        m = re.search(pattern, html_text, flags=re.IGNORECASE)
        if m:
            return html.unescape(m.group(1)).strip()
    return None



def extract_title(html_text: str) -> str:
    for candidate in [
        find_meta(html_text, 'property', 'og:title'),
        find_meta(html_text, 'name', 'twitter:title'),
    ]:
        if candidate:
            return clean_title(candidate)
    m = re.search(r'<title[^>]*>(.*?)</title>', html_text, flags=re.IGNORECASE | re.DOTALL)
    if m:
        return clean_title(strip_tags(m.group(1)))
    return '記事タイトル未取得'



def extract_description(html_text: str) -> str:
    for candidate in [
        find_meta(html_text, 'property', 'og:description'),
        find_meta(html_text, 'name', 'description'),
        find_meta(html_text, 'name', 'twitter:description'),
    ]:
        if candidate:
            return normalize_summary(candidate)

    body_text = strip_tags(html_text)
    body_text = re.sub(r'\s+', ' ', body_text)
    return normalize_summary(body_text[:240])



def extract_site_name(html_text: str, url: str) -> str:
    for candidate in [
        find_meta(html_text, 'property', 'og:site_name'),
        find_meta(html_text, 'name', 'application-name'),
    ]:
        if candidate:
            return candidate
    netloc = urllib.parse.urlparse(url).netloc
    return netloc.removeprefix('www.')



def clean_title(title: str) -> str:
    title = re.sub(r'\s+', ' ', title).strip()
    parts = re.split(r'\s+[\-|｜:：]\s+', title)
    if parts:
        title = max(parts, key=len).strip()
    return title



def normalize_summary(text: str) -> str:
    text = re.sub(r'\s+', ' ', html.unescape(text)).strip()
    text = text.strip(' 　')
    if len(text) > 140:
        text = text[:139].rstrip(' 、。,.!！?？') + '…'
    return text or '要約未取得。元記事を確認して補ってください。'



def infer_category(title: str, description: str, fallback: str) -> str:
    haystack = f'{title} {description}'.lower()
    for category, keywords in CATEGORY_RULES:
        if any(keyword in haystack for keyword in keywords):
            return category
    return fallback



def build_episode_text(date: str, items: list[dict[str, str]], title: str | None = None) -> str:
    resolved_title = title or '・'.join(item['headline'] for item in items[:3])
    summary = f'{date} の回では、' + '、'.join(item['headline'] for item in items[:3]) + 'の3本を掲載しています。'
    lines = [
        f'# {resolved_title}',
        '',
        '## Summary',
        summary,
        '',
        '## Intro',
        f'{date} 時点の公開情報をもとに構成した下書きです。内容を確認して整えてください。',
        '',
        '## Script Intro',
        f'ずんだもん1分AIニュース、{date}版なのだ。',
        '',
    ]
    for idx, item in enumerate(items, start=1):
        lines += [
            f'## Item {idx}',
            '### Headline',
            item['headline'],
            '',
            '### Summary',
            item['summary'],
            '',
            '### Category',
            item['category'],
            '',
            '### Source',
            f'[{item["source_name"]}]({item["url"]})',
            '',
            '### Script',
            '',
            '',
        ]
    lines += [
        '## Script Closing',
        '以上、今日のAIニュースまとめなのだ。気になる話題は出典も見てみるのだ。',
        '',
        '## Closing',
        '※ この記事は公開情報をもとにした短い要約です。詳細は各出典をご確認ください。',
        '',
    ]
    return '\n'.join(lines)



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Create an episode draft from article URLs.')
    parser.add_argument('date', help='Episode date in YYYY-MM-DD format')
    parser.add_argument('urls', nargs=3, help='Three source article URLs')
    parser.add_argument('--title', help='Override episode title')
    parser.add_argument('--stdout', action='store_true', help='Print the draft instead of writing episodes/YYYY-MM-DD.md')
    return parser.parse_args()



def main() -> None:
    args = parse_args()
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', args.date):
        raise SystemExit('Expected YYYY-MM-DD')

    items: list[dict[str, str]] = []
    for idx, url in enumerate(args.urls, start=1):
        try:
            html_text = fetch_url(url)
        except urllib.error.URLError as exc:
            raise SystemExit(f'Failed to fetch {url}: {exc}') from exc

        title = extract_title(html_text)
        description = extract_description(html_text)
        site_name = extract_site_name(html_text, url)
        items.append(
            {
                'headline': title,
                'summary': description,
                'source_name': site_name,
                'url': url,
                'category': infer_category(title, description, DEFAULT_CATEGORIES[idx - 1]),
            }
        )

    draft = build_episode_text(args.date, items, title=args.title)

    if args.stdout:
        print(draft)
        return

    out_path = ROOT / 'episodes' / f'{args.date}.md'
    if out_path.exists():
        raise SystemExit(f'Target already exists: {out_path}')
    out_path.write_text(draft, encoding='utf-8')

    print(f'Created: episodes/{args.date}.md')
    print('Review the generated summaries and categories before rendering.')
    print(json.dumps(items, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
