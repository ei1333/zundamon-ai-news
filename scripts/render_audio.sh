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
SCRIPT_PARTS="$REPO_ROOT/scripts_text/$DATE.parts.json"
OUTPUT="$REPO_ROOT/assets/audio/sample-news-$DATE.wav"
VOICEVOX_TTS_SCRIPT="${VOICEVOX_TTS_SCRIPT:-$HOME/.openclaw/workspace/voicevox_tts.sh}"

python3 "$REPO_ROOT/scripts/render_episode.py" "$DATE"

if [ ! -f "$SCRIPT_TEXT" ]; then
  echo "Script text not found: $SCRIPT_TEXT" >&2
  exit 1
fi
if [ ! -f "$SCRIPT_PARTS" ]; then
  echo "Script parts not found: $SCRIPT_PARTS" >&2
  exit 1
fi

if [ ! -x "$VOICEVOX_TTS_SCRIPT" ]; then
  echo "VOICEVOX helper is not executable or not found: $VOICEVOX_TTS_SCRIPT" >&2
  exit 1
fi

mkdir -p "$REPO_ROOT/assets/audio"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

python3 - "$SCRIPT_PARTS" "$TMP_DIR" <<'PY'
from pathlib import Path
import json
import sys

parts = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
out_dir = Path(sys.argv[2])
out_dir.mkdir(parents=True, exist_ok=True)
manifest = []
max_chars = 110
warnings = []
seq = 0
for part in parts:
    part_id = part['id']
    text = ' '.join(part['text'].split())
    if len(text) > max_chars:
        warnings.append(f"WARN: {part_id} is {len(text)} chars; chunking within the part")
    buf = ''
    chunk_index = 0
    tokens = text.replace('。', '。\n').replace('、', '、\n').splitlines()
    for token in tokens:
        token = token.strip()
        if not token:
            continue
        if len(buf) + len(token) <= max_chars:
            buf += token
        else:
            if buf:
                seq += 1
                chunk_index += 1
                manifest.append({'seq': seq, 'part_id': part_id, 'chunk_index': chunk_index, 'text': buf})
            buf = token
    if buf:
        seq += 1
        chunk_index += 1
        manifest.append({'seq': seq, 'part_id': part_id, 'chunk_index': chunk_index, 'text': buf})
(Path(out_dir) / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
(Path(out_dir) / 'warnings.log').write_text('\n'.join(warnings) + ('\n' if warnings else ''), encoding='utf-8')
PY

if [ -s "$TMP_DIR/warnings.log" ]; then
  cat "$TMP_DIR/warnings.log" >&2
fi

while read -r seq part_id chunk_index text_b64; do
  chunk_text="$(python3 - <<'PY' "$text_b64"
import base64, sys
print(base64.b64decode(sys.argv[1]).decode('utf-8'))
PY
)"
  out_file="$TMP_DIR/${part_id}-$(printf '%02d' "$chunk_index").wav"
  "$VOICEVOX_TTS_SCRIPT" "$SPEAKER" "$chunk_text" "$out_file"
done < <(python3 - <<'PY' "$TMP_DIR/manifest.json"
from pathlib import Path
import base64
import json
import sys
for item in json.loads(Path(sys.argv[1]).read_text(encoding='utf-8')):
    encoded = base64.b64encode(item['text'].encode('utf-8')).decode('ascii')
    print(item['seq'], item['part_id'], item['chunk_index'], encoded)
PY
)

python3 - "$TMP_DIR" "$OUTPUT" <<'PY'
from pathlib import Path
import json
import sys
import wave

base = Path(sys.argv[1])
out_path = Path(sys.argv[2])
manifest = json.loads((base / 'manifest.json').read_text(encoding='utf-8'))
parts = [base / f"{item['part_id']}-{item['chunk_index']:02d}.wav" for item in manifest]
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
