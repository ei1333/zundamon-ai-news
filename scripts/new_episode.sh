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
TEMPLATE="$REPO_ROOT/days/_template.html"
TARGET="$REPO_ROOT/days/$DATE.html"
AUDIO_FILE="sample-news-$DATE.wav"

if [ ! -f "$TEMPLATE" ]; then
  echo "Template not found: $TEMPLATE" >&2
  exit 1
fi

if [ -e "$TARGET" ]; then
  echo "Target already exists: $TARGET" >&2
  exit 1
fi

cp "$TEMPLATE" "$TARGET"
sed -i "s/YYYY-MM-DD/$DATE/g" "$TARGET"

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

latest_old = '<p>2026-03-12 の試作回です。</p>'
latest_new = f'<p>{date} の回です。</p>'
button_old = '<p><a class="button" href="days/2026-03-12.html">サンプル回を見る</a></p>'
button_new = f'<p><a class="button" href="days/{date}.html">最新回を見る</a></p>'
marker = '        <ul>\n'
entry = f'          <li><a href="days/{date}.html">{date} | {title}</a></li>\n'

if latest_old in text:
    text = text.replace(latest_old, latest_new, 1)
if button_old in text:
    text = text.replace(button_old, button_new, 1)

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

Next steps:
1. Edit days/$DATE.html
2. Generate audio: assets/audio/$AUDIO_FILE
3. Review index.html
4. git add . && git commit && git push origin main
5. ./scripts/publish.sh
EOF
