#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

[ -f index.html ] || fail "index.html not found"
[ -d days ] || fail "days directory not found"
[ -d assets/audio ] || fail "assets/audio directory not found"

if grep -R --line-number --exclude='_template.html' 'YYYY-MM-DD' days index.html; then
  fail "Unreplaced template marker YYYY-MM-DD found"
fi

mapfile -t day_pages < <(find days -maxdepth 1 -type f -name '*.html' ! -name '_template.html' | sort)
[ ${#day_pages[@]} -gt 0 ] || fail "No day pages found"

for page in "${day_pages[@]}"; do
  base="$(basename "$page")"
  date="${base%.html}"
  [[ "$date" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] || fail "Unexpected day page name: $base"

  grep -q "href=\"days/$base\"" index.html || fail "index.html does not link to days/$base"
  grep -q "sample-news-$date\.wav" "$page" || fail "$page does not reference sample-news-$date.wav"
  [ -f "assets/audio/sample-news-$date.wav" ] || fail "Missing audio file for $date"
done

echo "Validation OK"
