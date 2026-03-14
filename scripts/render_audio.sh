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
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

python3 - "$SCRIPT_TEXT" "$TMP_DIR/chunks.txt" <<'PY'
from pathlib import Path
import sys

src = Path(sys.argv[1]).read_text(encoding='utf-8')
out = Path(sys.argv[2])
lines = [line.strip() for line in src.splitlines() if line.strip()]
chunks = []
current = ''
max_chars = 110
for line in lines:
    if len(line) > max_chars:
        if current:
            chunks.append(current)
            current = ''
        parts = []
        buf = ''
        for token in line.replace('。', '。\n').replace('、', '、\n').splitlines():
            token = token.strip()
            if not token:
                continue
            if len(buf) + len(token) <= max_chars:
                buf += token
            else:
                if buf:
                    parts.append(buf)
                buf = token
        if buf:
            parts.append(buf)
        chunks.extend(parts)
        continue
    if not current:
        current = line
    elif len(current) + 1 + len(line) <= max_chars:
        current += ' ' + line
    else:
        chunks.append(current)
        current = line
if current:
    chunks.append(current)
out.write_text('\n'.join(chunks) + '\n', encoding='utf-8')
PY

idx=0
while IFS= read -r chunk; do
  [ -n "$chunk" ] || continue
  idx=$((idx + 1))
  "$VOICEVOX_TTS_SCRIPT" "$SPEAKER" "$chunk" "$TMP_DIR/part-$(printf '%03d' "$idx").wav"
done < "$TMP_DIR/chunks.txt"

python3 - "$TMP_DIR" "$OUTPUT" <<'PY'
from pathlib import Path
import sys
import wave

parts = sorted(Path(sys.argv[1]).glob('part-*.wav'))
out_path = Path(sys.argv[2])
if not parts:
    raise SystemExit('No synthesized chunks were created')
with wave.open(str(parts[0]), 'rb') as first:
    params = first.getparams()
    frames = [first.readframes(first.getnframes())]
for part in parts[1:]:
    with wave.open(str(part), 'rb') as w:
        if w.getparams()[:3] != params[:3]:
            raise SystemExit(f'Incompatible wav params: {part}')
        frames.append(w.readframes(w.getnframes()))
with wave.open(str(out_path), 'wb') as out:
    out.setparams(params)
    for frame in frames:
        out.writeframes(frame)
PY

echo "Rendered: assets/audio/sample-news-$DATE.wav"
