#!/usr/bin/env python3
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def extract_section(text: str, heading: str) -> str:
    pattern = rf'^## {re.escape(heading)}\n(.*?)(?=^## |\Z)'
    match = re.search(pattern, text, flags=re.MULTILINE | re.DOTALL)
    if not match:
        raise SystemExit(f"Missing section: {heading}")
    return match.group(1).strip()


def extract_subsection(text: str, heading: str) -> str:
    pattern = rf'^### {re.escape(heading)}\n(.*?)(?=^### |\Z)'
    match = re.search(pattern, text, flags=re.MULTILINE | re.DOTALL)
    if not match:
        raise SystemExit(f"Missing subsection: {heading}")
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


def parse_episode(path: Path):
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
        item = {
            'Headline': extract_subsection(item_block, 'Headline'),
            'Summary': extract_subsection(item_block, 'Summary'),
            'Script': extract_subsection(item_block, 'Script'),
        }
        item.update(parse_source_block(extract_subsection(item_block, 'Source')))
        items.append(item)

    return header, items


def render_html(date: str, header: dict, items: list[dict]) -> str:
    title = html.escape(header['title'])
    summary = html.escape(header['summary'])
    intro = html.escape(header['intro'])
    closing = html.escape(header['closing'])
    audio_file = html.escape(f'sample-news-{date}.wav')

    item_html = []
    for item in items:
        headline = html.escape(item['Headline'])
        summary_text = html.escape(item['Summary'])
        source_name = html.escape(item['SourceName'])
        source_url = html.escape(item['SourceURL'], quote=True)
        item_html.append(
            f'''          <li>\n            <h3>{headline}</h3>\n            <p>{summary_text}</p>\n            <p>出典: <a href="{source_url}">{source_name}</a></p>\n          </li>'''
        )

    items_joined = '\n'.join(item_html)
    return f'''<!DOCTYPE html>
<html lang="ja">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{date} | ずんだもん1分AIニュース</title>
    <link rel="stylesheet" href="../assets/style.css" />
  </head>
  <body>
    <main class="container">
      <a class="back-link" href="../index.html">← トップページへ戻る</a>

      <article class="article">
        <p class="eyebrow">Daily Episode</p>
        <h1>{date} のAIニュース</h1>
        <p class="meta">{intro}</p>

        <h2>音声</h2>
        <audio class="audio" controls>
          <source src="../assets/audio/{audio_file}" type="audio/wav" />
          お使いのブラウザは audio 要素に対応していません。
        </audio>

        <h2>ニュース要約</h2>
        <p>{summary}</p>
        <ol class="news-list">
{items_joined}
        </ol>

        <p class="note">{closing}</p>
      </article>
    </main>
  </body>
</html>
'''


def render_script(header: dict, items: list[dict]) -> str:
    lines = [header['script_intro'], '']
    for item in items:
        lines.append(item['Script'])
        lines.append('')
    lines.append(header['script_closing'])
    return '\n'.join(lines).strip() + '\n'


def main():
    if len(sys.argv) != 2:
        raise SystemExit('Usage: ./scripts/render_episode.py YYYY-MM-DD')

    date = sys.argv[1]
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', date):
        raise SystemExit('Expected YYYY-MM-DD')

    episode_path = ROOT / 'episodes' / f'{date}.md'
    if not episode_path.exists():
        raise SystemExit(f'Episode source not found: {episode_path}')

    header, items = parse_episode(episode_path)

    days_dir = ROOT / 'days'
    scripts_dir = ROOT / 'scripts_text'
    days_dir.mkdir(exist_ok=True)
    scripts_dir.mkdir(exist_ok=True)

    (days_dir / f'{date}.html').write_text(render_html(date, header, items), encoding='utf-8')
    (scripts_dir / f'{date}.txt').write_text(render_script(header, items), encoding='utf-8')

    print(f'Rendered: days/{date}.html')
    print(f'Rendered: scripts_text/{date}.txt')


if __name__ == '__main__':
    main()
