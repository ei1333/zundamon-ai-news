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
EPISODE_TEMPLATE="$REPO_ROOT/episodes/_template.md"
EPISODE_TARGET="$REPO_ROOT/episodes/$DATE.md"

if [ ! -f "$EPISODE_TEMPLATE" ]; then
  echo "Episode template not found: $EPISODE_TEMPLATE" >&2
  exit 1
fi

if [ -e "$EPISODE_TARGET" ]; then
  echo "Target already exists: $EPISODE_TARGET" >&2
  exit 1
fi

mkdir -p "$REPO_ROOT/episodes"
cp "$EPISODE_TEMPLATE" "$EPISODE_TARGET"
sed -i "s/YYYY-MM-DD/$DATE/g" "$EPISODE_TARGET"
sed -i "s/title: 新しいAIニュース回/title: $TITLE/g" "$EPISODE_TARGET"

python3 "$REPO_ROOT/scripts/render_episode.py" "$DATE"
python3 "$REPO_ROOT/scripts/update_index.py" "$DATE"

mkdir -p "$REPO_ROOT/assets/audio"

cat <<EOF
Created:
- episodes/$DATE.md
- days/$DATE.html
- scripts_text/$DATE.txt

Next steps:
1. Edit episodes/$DATE.md
2. Re-render: ./scripts/render_episode.py $DATE
3. Render audio: ./scripts/render_audio.sh $DATE
4. Review index.html
5. git add . && git commit && git push origin main
EOF
