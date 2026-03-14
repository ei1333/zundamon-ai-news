#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./scripts/build_episode.sh YYYY-MM-DD [speaker]

Examples:
  ./scripts/build_episode.sh 2026-03-13
  ./scripts/build_episode.sh 2026-03-13 zundamon
EOF
}

if [ $# -lt 1 ] || [ $# -gt 2 ]; then
  usage
  exit 1
fi

DATE="$1"
SPEAKER="${2:-zundamon}"

if ! [[ "$DATE" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
  echo "Invalid date format: $DATE" >&2
  echo "Expected YYYY-MM-DD" >&2
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

if [ $# -eq 1 ]; then
  SCHEDULE_JSON="$(python3 scripts/show_schedule.py --json "$DATE")"
  SCHEDULE_SPEAKER="$(printf '%s' "$SCHEDULE_JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("speaker", "zundamon"))')"
  SCHEDULE_SITE_THEME="$(printf '%s' "$SCHEDULE_JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("site_theme", "ai"))')"
  SPEAKER="$SCHEDULE_SPEAKER"
  echo "==> Using schedule for $DATE"
  echo "$SCHEDULE_JSON"
else
  SCHEDULE_SITE_THEME="ai"
fi

echo "==> Rendering episode outputs for $DATE"
python3 scripts/render_episode.py "$DATE"

echo "==> Updating index (site theme: $SCHEDULE_SITE_THEME)"
python3 scripts/update_index.py --site-theme "$SCHEDULE_SITE_THEME"

echo "==> Rendering audio ($SPEAKER)"
./scripts/render_audio.sh "$DATE" "$SPEAKER"

echo "==> Validating site"
./scripts/validate.sh

echo "==> Done"
echo "Built episode: $DATE"
