#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./scripts/render_audio.sh YYYY-MM-DD [speaker]

Examples:
  ./scripts/render_audio.sh 2026-03-13
  ./scripts/render_audio.sh 2026-03-13 zundamon
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
SCRIPT_TEXT="$REPO_ROOT/scripts_text/$DATE.txt"
OUTPUT="$REPO_ROOT/assets/audio/sample-news-$DATE.wav"
VOICEVOX_TTS_SCRIPT="${VOICEVOX_TTS_SCRIPT:-$HOME/.openclaw/workspace/voicevox_tts.sh}"

python3 "$REPO_ROOT/scripts/render_episode.py" "$DATE"

if [ ! -f "$SCRIPT_TEXT" ]; then
  echo "Script text not found: $SCRIPT_TEXT" >&2
  exit 1
fi

if [ ! -x "$VOICEVOX_TTS_SCRIPT" ]; then
  echo "VOICEVOX helper is not executable or not found: $VOICEVOX_TTS_SCRIPT" >&2
  exit 1
fi

mkdir -p "$REPO_ROOT/assets/audio"
TEXT="$(cat "$SCRIPT_TEXT")"

"$VOICEVOX_TTS_SCRIPT" "$SPEAKER" "$TEXT" "$OUTPUT"

echo "Rendered: assets/audio/sample-news-$DATE.wav"
