#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

warn() {
  echo "WARN: $*" >&2
}

[ -f index.html ] || fail "index.html not found"
[ -d episodes ] || fail "episodes directory not found"
[ -d days ] || fail "days directory not found"
[ -d assets/audio ] || fail "assets/audio directory not found"
[ -f assets/ogp.png ] || fail "assets/ogp.png not found"

if grep -R --line-number --exclude='_template.html' --exclude='_template.md' 'YYYY-MM-DD' episodes days index.html; then
  fail "Unreplaced template marker YYYY-MM-DD found"
fi

if grep -R --line-number --exclude='_template.html' --exclude='_template.md' '{[A-Za-z0-9_][A-Za-z0-9_]*}' days index.html; then
  fail "Unreplaced template placeholder found in rendered HTML"
fi

mapfile -t episode_sources < <(find episodes -maxdepth 1 -type f -name '*.md' ! -name '_template.md' | sort)
[ ${#episode_sources[@]} -gt 0 ] || fail "No episode sources found"

latest_date="$(basename "${episode_sources[-1]}")"
latest_date="${latest_date%.md}"
grep -q "href=\"days/$latest_date.html\"" index.html || fail "index.html does not point to latest episode $latest_date"

for source in "${episode_sources[@]}"; do
  base="$(basename "$source")"
  date="${base%.md}"
  [[ "$date" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] || fail "Unexpected episode source name: $base"

  [ -s "$source" ] || fail "Episode source is empty: $source"
  [ -f "days/$date.html" ] || fail "Missing rendered HTML for $date"
  [ -s "days/$date.html" ] || fail "Rendered HTML is empty for $date"
  [ -f "scripts_text/$date.txt" ] || fail "Missing rendered script text for $date"
  [ -s "scripts_text/$date.txt" ] || fail "Rendered script text is empty for $date"
  [ -f "assets/audio/sample-news-$date.wav" ] || fail "Missing audio file for $date"
  [ -s "assets/audio/sample-news-$date.wav" ] || fail "Audio file is empty for $date"
  [ -f "assets/ogp-$date.png" ] || fail "Missing OGP image for $date"
  [ -s "assets/ogp-$date.png" ] || fail "OGP image is empty for $date"

  python3 - "$source" <<'PY'
from pathlib import Path
import re
import sys
from scripts.episode_utils import detect_episode_theme, extract_section, parse_episode_full

path = Path(sys.argv[1])
text = path.read_text(encoding='utf-8')
try:
    explicit_theme = extract_section(text, 'Theme').strip().lower()
except SystemExit:
    raise SystemExit(f"Episode theme is missing: {path}")
if not explicit_theme:
    raise SystemExit(f"Episode theme must not be empty: {path}")
try:
    coverage = extract_section(text, 'Coverage').strip().lower()
except SystemExit:
    raise SystemExit(f"Episode coverage is missing: {path}")
if coverage not in {'daily', 'weekly'}:
    raise SystemExit(f"Episode coverage must be one of daily/weekly: {path} (got: {coverage})")
try:
    window = extract_section(text, 'Window').strip()
except SystemExit:
    raise SystemExit(f"Episode window is missing: {path}")
if not re.fullmatch(r'\d{4}-\d{2}-\d{2}\.\.\d{4}-\d{2}-\d{2}', window):
    raise SystemExit(f"Episode window must be YYYY-MM-DD..YYYY-MM-DD: {path} (got: {window})")
header, items = parse_episode_full(path, theme_name=detect_episode_theme(path))
if len(items) != 3:
    raise SystemExit(f"Episode must contain exactly 3 items: {path}")
if not header['title'].strip():
    raise SystemExit(f"Episode title is empty: {path}")
for idx, item in enumerate(items, start=1):
    if not item['Headline'].strip():
        raise SystemExit(f"Item {idx} headline is empty: {path}")
    if not item['Summary'].strip():
        raise SystemExit(f"Item {idx} summary is empty: {path}")
    if not item['SourceName'].strip() or not item['SourceURL'].strip():
        raise SystemExit(f"Item {idx} source is incomplete: {path}")
PY

  while IFS= read -r warning; do
    [ -n "$warning" ] && warn "$warning"
  done < <(python3 - "$source" <<'PY'
from pathlib import Path
import sys
from scripts.episode_utils import parse_episode_full

path = Path(sys.argv[1])
header, _items = parse_episode_full(path)
title = ' '.join(header['title'].split())
topics = [part.strip() for part in title.split('・') if part.strip()]
if len(title) > 28:
    print(f"{path.name}: title is {len(title)} chars; OGP may trim it")
if len(topics) >= 4:
    print(f"{path.name}: title has {len(topics)} topics; OGP may drop trailing topics")
for idx, topic in enumerate(topics, start=1):
    if len(topic) > 18:
        print(f"{path.name}: topic {idx} is {len(topic)} chars; OGP balance may degrade")
PY
)

  grep -q "href=\"days/$date.html\"" index.html || fail "index.html does not link to days/$date.html"
  grep -q "sample-news-$date\.wav" "days/$date.html" || fail "days/$date.html does not reference sample-news-$date.wav"
  grep -q "assets/ogp-$date\.png\|/assets/ogp-$date\.png" "days/$date.html" || fail "days/$date.html does not reference ogp-$date.png"
  grep -q '<meta property="og:type" content="article"' "days/$date.html" || fail "days/$date.html missing article og:type"
  grep -q '<audio class="audio" controls' "days/$date.html" || fail "days/$date.html missing audio player"
done

grep -q '<meta property="og:type" content="website"' index.html || fail "index.html missing website og:type"
grep -q 'sample-news-' index.html || fail "index.html does not reference any episode audio"

echo "Validation OK"
