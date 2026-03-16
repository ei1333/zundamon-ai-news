#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

TARGET_DATE="${1:-$(date -u -d '+1 day' +%F)}"
shift $(( $# > 0 ? 1 : 0 )) || true

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'EOF'
Usage:
  ./scripts/cron_prepare_episode.sh [YYYY-MM-DD] [URL1 URL2 URL3]

Behavior:
  - If no date is passed, defaults to tomorrow in UTC.
  - If 3 URLs are passed, prepares draft + prompt files.
  - If no URLs are passed, prints the resolved schedule and source suggestions.

Examples:
  ./scripts/cron_prepare_episode.sh
  ./scripts/cron_prepare_episode.sh 2026-03-17
  ./scripts/cron_prepare_episode.sh 2026-03-17 \
    https://example.com/a \
    https://example.com/b \
    https://example.com/c
EOF
  exit 0
fi

mapfile -t SCHEDULE_LINES < <(python3 "$REPO_ROOT/scripts/show_schedule.py" "$TARGET_DATE")
printf '%s\n' "${SCHEDULE_LINES[@]}"

echo
if [[ $# -eq 0 ]]; then
  echo "No article URLs passed; schedule only."
  echo "Pass exactly 3 article URLs to prepare draft + prompt files."
  exit 0
fi

if [[ $# -ne 3 ]]; then
  echo "ERROR: pass either zero URLs or exactly three URLs" >&2
  exit 1
fi

exec "$REPO_ROOT/scripts/prepare_llm_episode.sh" "$TARGET_DATE" "$1" "$2" "$3"
