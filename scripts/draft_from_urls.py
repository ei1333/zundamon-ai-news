#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import re
import socket
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from episode_utils import default_window_for, load_theme
from schedule_utils import resolve_rule

ROOT = Path(__file__).resolve().parent.parent

USER_AGENT = 'zundamon-ai-news/0.1 (+https://ei1333.github.io/zundamon-ai-news/)'


def fetch_url(url: str) -> str:
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req, timeout=20) as resp:
        charset = resp.headers.get_content_charset() or 'utf-8'
        data = resp.read()
    return data.decode(charset, errors='replace')



def fallback_from_url(url: str, fallback_category: str, reason: str, draft_theme: dict[str, object], *, theme_name: str = 'ai') -> dict[str, str]:
    parsed = urllib.parse.urlparse(url)
    slug = parsed.path.rstrip('/').split('/')[-1] or parsed.netloc
    slug = urllib.parse.unquote(slug)
    slug = re.sub(r'[-_]+', ' ', slug)
    slug = re.sub(r'\b\d{4}\b', ' ', slug)
    slug = re.sub(r'\s+', ' ', slug).strip(' /')
    headline = finalize_headline(clean_title(slug.title()), theme_name, description='') if slug else '記事タイトル未取得'
    site_name = parsed.netloc.removeprefix('www.') or 'source'
    return {
        'headline': headline,
        'summary': str(draft_theme.get('fallback_summary', 'URL からの自動取得に失敗したため、元記事を開いて要約を補ってください。({reason})')).format(reason=reason),
        'source_name': site_name,
        'url': url,
        'category': fallback_category,
    }



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



def normalize_headline_style(title: str) -> str:
    title = title.strip()
    title = title.replace('‘', '“').replace('’', '”')
    title = re.sub(r'\bAI\b', 'AI', title)
    title = re.sub(r'\bOFC\b', 'OFC', title)
    title = re.sub(r'\bHB\s*(\d+)\b', r'HB \1', title)
    title = re.sub(r'\s+', ' ', title)
    title = title.strip(' .-–—|｜:：')
    return title



def clean_title(title: str) -> str:
    title = html.unescape(title)
    title = re.sub(r'\s+', ' ', title).strip()
    title = title.strip('"“”‘’「」『』')

    title = re.sub(r'[｜|](将棋ニュース|棋戦トピックス|日本将棋連盟)\s*$', '', title)
    title = re.sub(r'\s*[｜|]\s*(将棋ニュース|棋戦トピックス|日本将棋連盟)\s*$', '', title)
    title = re.sub(r'[｜|](将棋ニュース|棋戦トピックス)[｜|]日本将棋連盟\s*$', '', title)
    title = re.sub(r'\s*[｜|]\s*(将棋ニュース|棋戦トピックス)\s*[｜|]\s*日本将棋連盟\s*$', '', title)
    title = re.sub(r'[｜|]日本将棋連盟\s*$', '', title)
    title = re.sub(r'\s*[｜|]\s*日本将棋連盟\s*$', '', title)
    title = re.sub(r'^日本将棋連盟\s*[｜|]\s*', '', title)

    separators = [r' \| ', r' ｜ ', r' - ', r' — ', r' – ', r' :: ', r' : ', r'：']
    parts = [title]
    for sep in separators:
        next_parts: list[str] = []
        for part in parts:
            split_parts = [p.strip() for p in re.split(sep, part) if p.strip()]
            next_parts.extend(split_parts or [part])
        parts = next_parts

    noise_patterns = [
        r'^home$',
        r'^news$',
        r'^press release$',
        r'^press$',
        r'^blog$',
        r'^article$',
        r'^official site$',
        r'^transparency coalition$',
        r'^legislation for transparency in ai now\.?$',
        r'^日本将棋連盟$',
        r'^将棋ニュース$',
        r'^棋戦トピックス$',
    ]

    filtered = []
    for part in parts:
        normalized = re.sub(r'[^a-z0-9ぁ-んァ-ヶ一-龠 ]+', '', part.lower()).strip()
        if any(re.fullmatch(pattern, normalized) for pattern in noise_patterns):
            continue
        filtered.append(part)

    if filtered:
        title = max(filtered, key=len).strip()

    title = re.sub(r'\s+[\-|｜:：]+\s*$', '', title).strip()
    title = normalize_headline_style(title)
    return title or '記事タイトル未取得'



def normalize_summary(text: str) -> str:
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'^(share this:|read more:|continue reading:?|for immediate release:?)+', '', text, flags=re.IGNORECASE).strip()
    text = re.sub(r'\b(photo|image) courtesy of [^.]+\.?', '', text, flags=re.IGNORECASE).strip()
    text = re.sub(r'\bclick here to[^.]+\.?', '', text, flags=re.IGNORECASE).strip()
    text = text.strip(' 　')

    sentences = re.split(r'(?<=[.!?。！？])\s+', text)
    sentences = [s.strip(' "“”') for s in sentences if s.strip()]
    if sentences:
        text = ' '.join(sentences[:2])
    if len(text) > 140:
        text = text[:139].rstrip(' 、。,.!！?？') + '…'
    return text or '要約未取得。元記事を確認して補ってください。'



def finalize_headline(title: str, theme_name: str, *, description: str = '') -> str:
    # Keep this step intentionally conservative: collect a clean source title,
    # and let downstream generation/LLM steps rewrite it into a spoken headline.
    _ = theme_name, description
    return normalize_headline_style(title)



def infer_category(title: str, description: str, fallback: str, category_rules: list[tuple[str, list[str]]]) -> str:
    haystack = f'{title} {description}'.lower()
    for category, keywords in category_rules:
        if any(keyword in haystack for keyword in keywords):
            return category
    return fallback



def pick_episode_title(items: list[dict[str, str]], draft_theme: dict[str, object]) -> str:
    keywords = []
    seen = set()
    for item in items[:3]:
        category = item['category']
        if category and category not in seen:
            keywords.append(category)
            seen.add(category)
            continue

        headline = item['headline']
        if headline and headline not in seen:
            keywords.append(headline)
            seen.add(headline)

    title = '・'.join(keywords[:3]).strip()
    return title or str(draft_theme.get('title_fallback', '新しいAIニュース回'))



def build_episode_text(date: str, items: list[dict[str, str]], draft_theme: dict[str, object], *, theme_name: str = 'ai', coverage: str = 'weekly', window: str | None = None, title: str | None = None) -> str:
    resolved_title = title or pick_episode_title(items, draft_theme)
    resolved_window = window or default_window_for(date, coverage)
    summary = f'{resolved_window} の公開情報から、' + '、'.join(item['headline'] for item in items[:3]) + 'の3本を掲載しています。'
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
        str(draft_theme.get('script_closing', '以上、今日のAIニュースまとめなのだ。気になる話題は出典も見てみるのだ。')),
        '',
        '## Closing',
        str(draft_theme.get('closing', '※ この記事は公開情報をもとにした短い要約です。詳細は各出典をご確認ください。')),
        '',
    ]
    return '\n'.join(lines)



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Create an episode draft from article URLs.')
    parser.add_argument('date', help='Episode date in YYYY-MM-DD format')
    parser.add_argument('urls', nargs=3, help='Three source article URLs')
    parser.add_argument('--title', help='Override episode title')
    parser.add_argument('--theme', help='Theme name from config/themes/<name>.json. If omitted, resolves from schedule.')
    parser.add_argument('--coverage', choices=['daily', 'weekly'], help='Coverage window type for this draft. If omitted, resolves from schedule.')
    parser.add_argument('--window', help='Explicit window like YYYY-MM-DD..YYYY-MM-DD. Defaults from coverage/date or schedule.')
    parser.add_argument('--stdout', action='store_true', help='Print the draft instead of writing episodes/YYYY-MM-DD.md')
    return parser.parse_args()



def main() -> None:
    args = parse_args()
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', args.date):
        raise SystemExit('Expected YYYY-MM-DD')

    _, schedule_rule = resolve_rule(args.date)
    theme_name = args.theme or schedule_rule.get('theme', 'ai')
    coverage = args.coverage or schedule_rule.get('coverage', 'weekly')
    window = args.window or schedule_rule.get('window') or default_window_for(args.date, coverage)

    theme = load_theme(theme_name)
    draft_theme = theme.get('draft', {})
    default_categories = list(draft_theme.get('default_categories', ['透明性', '研究', 'インフラ']))
    category_rules = [
        (str(rule['label']), list(rule.get('keywords', [])))
        for rule in draft_theme.get('category_rules', [])
    ]

    items: list[dict[str, str]] = []
    for idx, url in enumerate(args.urls, start=1):
        fallback_category = default_categories[idx - 1]
        try:
            html_text = fetch_url(url)
            raw_title = extract_title(html_text)
            description = extract_description(html_text)
            title = finalize_headline(raw_title, args.theme, description=description)
            site_name = extract_site_name(html_text, url)
            items.append(
                {
                    'headline': title,
                    'summary': description,
                    'source_name': site_name,
                    'url': url,
                    'category': infer_category(title, description, fallback_category, category_rules),
                }
            )
        except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
            items.append(fallback_from_url(url, fallback_category, str(exc), draft_theme, theme_name=theme_name))

    draft = build_episode_text(args.date, items, draft_theme, theme_name=theme_name, coverage=coverage, window=window, title=args.title)

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
