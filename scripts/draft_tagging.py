#!/usr/bin/env python3
from __future__ import annotations


def infer_category(title: str, description: str, fallback: str, category_rules: list[tuple[str, list[str]]]) -> str:
    haystack = f'{title} {description}'.lower()
    for category, keywords in category_rules:
        if any(keyword in haystack for keyword in keywords):
            return category
    return fallback


def infer_tags(title: str, description: str, primary_tag: str, tag_rules: list[tuple[str, list[str]]]) -> list[str]:
    haystack = f'{title} {description}'.lower()
    tags: list[str] = []
    seen: set[str] = set()

    def add(tag: str) -> None:
        tag = tag.strip()
        if not tag or tag in seen:
            return
        seen.add(tag)
        tags.append(tag)

    add(primary_tag)
    for tag, keywords in tag_rules:
        if any(keyword in haystack for keyword in keywords):
            add(tag)
    return tags


def pick_episode_title(items: list[object], draft_theme: dict[str, object]) -> str:
    keywords = []
    seen = set()
    for item in items[:3]:
        category = str(getattr(item, 'category', ''))
        if category and category not in seen:
            keywords.append(category)
            seen.add(category)
            continue

        headline = str(getattr(item, 'headline', ''))
        if headline and headline not in seen:
            keywords.append(headline)
            seen.add(headline)

    title = '・'.join(keywords[:3]).strip()
    return title or str(draft_theme.get('title_fallback', '新しいAIニュース回'))
