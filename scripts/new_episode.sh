#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./scripts/new_episode.sh YYYY-MM-DD [title]

Examples:
  ./scripts/new_episode.sh 2026-03-13
  ./scripts/new_episode.sh 2026-03-13 "AI規制・研究・半導体"
EOF
}

if [ $# -lt 1 ] || [ $# -gt 2 ]; then
  usage
  exit 1
fi

DATE="$1"
TITLE="${2:-新しいAIニュース回}"

if ! [[ "$DATE" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
  echo "Invalid date format: $DATE" >&2
  echo "Expected YYYY-MM-DD" >&2
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HTML_TEMPLATE="$REPO_ROOT/days/_template.html"
HTML_TARGET="$REPO_ROOT/days/$DATE.html"
SCRIPT_TEMPLATE="$REPO_ROOT/scripts_text/_template.txt"
SCRIPT_TARGET="$REPO_ROOT/scripts_text/$DATE.txt"
AUDIO_FILE="sample-news-$DATE.wav"

if [ ! -f "$HTML_TEMPLATE" ]; then
  echo "HTML template not found: $HTML_TEMPLATE" >&2
  exit 1
fi

if [ ! -f "$SCRIPT_TEMPLATE" ]; then
  echo "Script template not found: $SCRIPT_TEMPLATE" >&2
  exit 1
fi

if [ -e "$HTML_TARGET" ]; then
  echo "Target already exists: $HTML_TARGET" >&2
  exit 1
fi

if [ -e "$SCRIPT_TARGET" ]; then
  echo "Target already exists: $SCRIPT_TARGET" >&2
  exit 1
fi

cp "$HTML_TEMPLATE" "$HTML_TARGET"
sed -i "s/YYYY-MM-DD/$DATE/g" "$HTML_TARGET"

mkdir -p "$REPO_ROOT/scripts_text"
cp "$SCRIPT_TEMPLATE" "$SCRIPT_TARGET"
sed -i "s/YYYY-MM-DD/$DATE/g" "$SCRIPT_TARGET"

INDEX="$REPO_ROOT/index.html"
BACKUP="$INDEX.bak"
cp "$INDEX" "$BACKUP"

python3 - <<'PY' "$INDEX" "$DATE" "$TITLE"
from pathlib import Path
import sys

index_path = Path(sys.argv[1])
date = sys.argv[2]
title = sys.argv[3]
text = index_path.read_text()

latest_pattern = '<section class="card">\n        <h2>最新サンプル</h2>'
latest_start = text.find(latest_pattern)
if latest_start == -1:
    raise SystemExit('Could not find latest sample section in index.html')

latest_end = text.find('</section>', latest_start)
if latest_end == -1:
    raise SystemExit('Could not find end of latest sample section in index.html')
latest_end += len('</section>')

latest_block = f'''<section class="card">\n        <h2>最新サンプル</h2>\n        <p>{date} の回です。</p>\n        <p><a class="button" href="days/{date}.html">最新回を見る</a></p>\n      </section>'''
text = text[:latest_start] + latest_block + text[latest_end:]

marker = '        <ul>\n'
entry = f'          <li><a href="days/{date}.html">{date} | {title}</a></li>\n'

if entry not in text:
    pos = text.find(marker)
    if pos == -1:
        raise SystemExit('Could not find backnumber list in index.html')
    pos += len(marker)
    text = text[:pos] + entry + text[pos:]

index_path.write_text(text)
PY

rm -f "$BACKUP"
mkdir -p "$REPO_ROOT/assets/audio"

cat <<EOF
Created:
- days/$DATE.html
- scripts_text/$DATE.txt

Next steps:
1. Edit days/$DATE.html
2. Edit scripts_text/$DATE.txt
3. Render audio: ./scripts/render_audio.sh $DATE
4. Review index.html
5. git add . && git commit && git push origin main
EOF
