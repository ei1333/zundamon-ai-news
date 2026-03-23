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

Behavior:
  - Sends a Discord reminder only.
  - Does NOT auto-collect article candidates.
  - Human/manual candidate gathering happens after this notification.

Examples:
  ./scripts/cron_send_candidates.sh 2026-03-17 channel:1234567890 9876543210
  ./scripts/cron_send_candidates.sh "$(date -u -d '+1 day' +%F)" channel:1234567890 9876543210
EOF
  exit 0
fi

TARGET_DATE="${1:-$(date -u -d '+1 day' +%F)}"
TARGET_CHANNEL="${2:?target channel required (e.g. channel:1234567890)}"
MENTION_USER="${3:?mention user id required}"

DISCORD_TARGET="$TARGET_CHANNEL"
if [[ "$DISCORD_TARGET" == channel:* ]]; then
  DISCORD_TARGET="${DISCORD_TARGET#channel:}"
fi

MESSAGE_TEXT="$(python3 - "$TARGET_DATE" "$MENTION_USER" <<'PY'
import sys
from schedule_utils import resolve_schedule

payload = resolve_schedule(sys.argv[1]).to_dict()
mention_user = sys.argv[2]

lines = [
    f"<@{mention_user}> わっふー！ {payload['date']} の **{payload['theme']}** 回、候補選定の時間めうっ！！",
    f"coverage: {payload['coverage']} / window: {payload['window']}",
    '',
    '今回は **自動候補収集はしない** めうっ☆',
    '候補はめうが集め直して3本を選定してから、Discord に投げるめう〜っ♪',
    'その後、お主の **「はい」** が出たら push まで進めるめうっ！',
]
print('\n'.join(lines))
PY
)"

"$OPENCLAW_BIN" message send \
  --channel discord \
  --target "$DISCORD_TARGET" \
  --message "$MESSAGE_TEXT"
