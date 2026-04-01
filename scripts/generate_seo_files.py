#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from episode_utils import ROOT, load_theme


def lastmod_for(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).strftime('%Y-%m-%d')


def build_sitemap(theme_name: str = 'ai') -> str:
    theme = load_theme(theme_name)
    site_url = theme.get('site_url', 'https://example.com/').rstrip('/')

    entries: list[tuple[str, str]] = [
        (f'{site_url}/', lastmod_for(ROOT / 'index.html')),
        (f'{site_url}/about.html', lastmod_for(ROOT / 'about.html')),
    ]

    for path in sorted((ROOT / 'days').glob('*.html')):
        if path.name == '_template.html':
            continue
        entries.append((f'{site_url}/days/{path.name}', lastmod_for(path)))

    body = '\n'.join(
        '  <url>\n'
        f'    <loc>{loc}</loc>\n'
        f'    <lastmod>{lastmod}</lastmod>\n'
        '  </url>'
        for loc, lastmod in entries
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f'{body}\n'
        '</urlset>\n'
    )


def build_robots(theme_name: str = 'ai') -> str:
    theme = load_theme(theme_name)
    site_url = theme.get('site_url', 'https://example.com/').rstrip('/')
    return (
        'User-agent: *\n'
        'Allow: /\n\n'
        f'Sitemap: {site_url}/sitemap.xml\n'
    )


def main() -> None:
    (ROOT / 'sitemap.xml').write_text(build_sitemap(), encoding='utf-8')
    (ROOT / 'robots.txt').write_text(build_robots(), encoding='utf-8')
    print('Rendered: sitemap.xml')
    print('Rendered: robots.txt')


if __name__ == '__main__':
    main()
