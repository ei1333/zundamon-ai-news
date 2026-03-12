#!/usr/bin/env python3
from __future__ import annotations

import html
import re
import sys

from episode_utils import ROOT, parse_episode_full


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
        category = html.escape(item['Category'])
        category_class = html.escape(item['CategoryClass'])
        item_html.append(
            f'''          <li>\n            <div class="episode-tags">\n              <span class="episode-tag {category_class}">{category}</span>\n            </div>\n            <h3>{headline}</h3>\n            <p>{summary_text}</p>\n            <p>出典: <a href="{source_url}">{source_name}</a></p>\n          </li>'''
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

    header, items = parse_episode_full(episode_path)

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
