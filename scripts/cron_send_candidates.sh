#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OPENCLAW_BIN="${OPENCLAW_BIN:-$(command -v openclaw || true)}"
: "${OPENCLAW_BIN:?openclaw not found; set OPENCLAW_BIN or ensure openclaw is on PATH}"
cd "$REPO_ROOT"

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'EOF'
Usage:
  ./scripts/cron_send_candidates.sh [YYYY-MM-DD] channel:<CHANNEL_ID> <USER_ID>

Examples:
  ./scripts/cron_send_candidates.sh 2026-03-17 channel:1234567890 9876543210
  ./scripts/cron_send_candidates.sh "$(date -u -d '+1 day' +%F)" channel:1234567890 9876543210
EOF
  exit 0
fi

TARGET_DATE="${1:-$(date -u -d '+1 day' +%F)}"
TARGET_CHANNEL="${2:?target channel required (e.g. channel:1234567890)}"
MENTION_USER="${3:?mention user id required}"

JSON_OUT="$(python3 "$REPO_ROOT/scripts/collect_candidate_urls.py" "$TARGET_DATE" --json)"
JSON_PATH="$(mktemp)"
printf '%s\n' "$JSON_OUT" > "$JSON_PATH"

MESSAGE_TEXT="$(python3 - "$JSON_PATH" "$MENTION_USER" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
mention_user = sys.argv[2]
items = payload.get('items', [])
if not items:
    print(f"<@{mention_user}> わっふー！ {payload['date']} の {payload['theme']} 候補を拾えなかっためう… source 候補の確認を頼みたいめうっ☆")
    raise SystemExit(0)

lines = [
    f"<@{mention_user}> わっふー！ {payload['date']} の **{payload['theme']}** 候補を3本集めためうっ！！",
    f"coverage: {payload['coverage']} / window: {payload['window']}",
    '',
]
for idx, item in enumerate(items[:3], start=1):
    lines.append(f"{idx}. {item['title']}")
    lines.append(f"<{item['url']}>")
    if item.get('summary'):
        lines.append(f"- {item['summary']}")
    lines.append('')
lines.append('この3本でよければ **「はい」** って返してほしいめうっ☆')
print('\n'.join(lines))
PY
)"

"$OPENCLAW_BIN" agent \
  --message "$MESSAGE_TEXT" \
  --deliver \
  --reply-channel discord \
  --reply-to "$TARGET_CHANNEL"

rm -f "$JSON_PATH"
