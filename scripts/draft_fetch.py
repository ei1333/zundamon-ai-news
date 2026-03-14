#!/usr/bin/env python3
from __future__ import annotations

import html
import re
import urllib.parse
import urllib.request

USER_AGENT = 'zundamon-ai-news/0.1 (+https://ei1333.github.io/zundamon-ai-news/)'


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
    text = text.strip(' 　')

    sentences = re.split(r'(?<=[.!?。！？])\s+', text)
    sentences = [s.strip(' "“”') for s in sentences if s.strip()]
    if sentences:
        text = ' '.join(sentences[:2])
    if len(text) > 140:
        text = text[:139].rstrip(' 、。,.!！?？') + '…'
    return text or '要約未取得。元記事を確認して補ってください。'


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


def finalize_headline(title: str, theme_name: str, *, description: str = '') -> str:
    _ = theme_name, description
    return normalize_headline_style(title)
