#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import urllib.parse
from collections import OrderedDict
from pathlib import Path

from draft_fetch import extract_description, extract_site_name, extract_title, fetch_url
from schedule_utils import resolve_schedule

ROOT = Path(__file__).resolve().parent.parent

SKIP_EXTENSIONS = (
    '.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.pdf', '.mp4', '.mp3', '.zip'
)
SKIP_KEYWORDS = (
    '/video', '/videos', '/live', '/watch', '/tv', '/newsletter', '/subscribe', '/sign-in',
    '/login', '/account', '/privacy', '/terms', '/contact', '/about', '/advertising'
)


def extract_links(base_url: str, html_text: str) -> list[str]:
    hrefs = re.findall(r'href=["\']([^"\']+)["\']', html_text, flags=re.IGNORECASE)
    out: list[str] = []
    for href in hrefs:
        href = html.unescape(href.strip())
        if not href or href.startswith('#') or href.startswith('javascript:') or href.startswith('mailto:'):
            continue
        absolute = urllib.parse.urljoin(base_url, href)
        parsed = urllib.parse.urlparse(absolute)
        if parsed.scheme not in ('http', 'https'):
            continue
        if parsed.query:
            absolute = urllib.parse.urlunparse(parsed._replace(query='', fragment=''))
        else:
            absolute = urllib.parse.urlunparse(parsed._replace(fragment=''))
        out.append(absolute)
    return list(OrderedDict.fromkeys(out))


def is_candidate_article(url: str, seed_url: str, target_date: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    seed = urllib.parse.urlparse(seed_url)
    if parsed.netloc != seed.netloc:
        return False
    if parsed.path.endswith(SKIP_EXTENSIONS):
        return False
    lower = url.lower()
    if any(k in lower for k in SKIP_KEYWORDS):
        return False
    path = parsed.path.strip('/')
    if not path or path.count('/') < 1:
        return False
    if re.search(r'/tag/|/topics?/|/section/|/category/|/author/|/authors/', lower):
        return False
    yyyy, mm, dd = target_date.split('-')
    date_markers = [f'/{yyyy}/{mm}/{dd}/', f'/{yyyy}-{mm}-{dd}/', f'/{yyyy}{mm}{dd}/']
    if any(marker in parsed.path for marker in date_markers):
        return True
    if re.search(r'/20\d{2}/\d{2}/\d{2}/', parsed.path):
        return True
    slug_parts = [p for p in path.split('/') if p]
    return len(slug_parts) >= 2 and len(slug_parts[-1]) >= 12


def score_url(url: str, target_date: str) -> tuple[int, int]:
    parsed = urllib.parse.urlparse(url)
    yyyy, mm, dd = target_date.split('-')
    score = 0
    if f'/{yyyy}/{mm}/{dd}/' in parsed.path or f'/{yyyy}-{mm}-{dd}/' in parsed.path:
        score += 5
    if re.search(r'/20\d{2}/\d{2}/\d{2}/', parsed.path):
        score += 3
    score += min(parsed.path.count('/'), 4)
    return (-score, len(url))


def collect_from_source(seed_url: str, target_date: str, limit: int = 8) -> list[dict]:
    page_html = fetch_url(seed_url)
    links = extract_links(seed_url, page_html)
    candidates = [url for url in links if is_candidate_article(url, seed_url, target_date)]
    candidates = sorted(OrderedDict.fromkeys(candidates), key=lambda u: score_url(u, target_date))

    results: list[dict] = []
    for url in candidates[:limit]:
        try:
            article_html = fetch_url(url)
            title = extract_title(article_html)
            summary = extract_description(article_html)
            site_name = extract_site_name(article_html, url)
        except Exception:
            continue
        if not title or title == '記事タイトル未取得':
            continue
        results.append({
            'url': url,
            'title': title,
            'summary': summary,
            'site_name': site_name,
            'seed_url': seed_url,
        })
        if len(results) >= 3:
            break
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description='Collect three article candidates from configured source pages.')
    parser.add_argument('date', help='Episode date in YYYY-MM-DD format')
    parser.add_argument('--json', action='store_true', help='Print JSON instead of a human-readable list')
    args = parser.parse_args()

    schedule = resolve_schedule(args.date)
    all_results: list[dict] = []
    for seed_url in schedule.source_suggestions:
        try:
            all_results.extend(collect_from_source(seed_url, args.date))
        except Exception:
            continue

    unique: list[dict] = []
    seen_urls: set[str] = set()
    for item in all_results:
        if item['url'] in seen_urls:
            continue
        seen_urls.add(item['url'])
        unique.append(item)
        if len(unique) >= 3:
            break

    payload = {
        'date': args.date,
        'theme': schedule.theme,
        'coverage': schedule.coverage,
        'window': schedule.window,
        'items': unique,
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    print(f"date: {payload['date']}")
    print(f"theme: {payload['theme']}")
    print(f"coverage: {payload['coverage']}")
    print(f"window: {payload['window']}")
    print('')
    if not unique:
        print('No candidates found')
        raise SystemExit(1)
    for idx, item in enumerate(unique, start=1):
        print(f"{idx}. {item['title']}")
        print(f"   {item['url']}")
        if item.get('summary'):
            print(f"   {item['summary']}")
        print(f"   source: {item['site_name']}")
        print('')


if __name__ == '__main__':
    main()
