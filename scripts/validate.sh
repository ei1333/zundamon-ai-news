#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

[ -f index.html ] || fail "index.html not found"
[ -d episodes ] || fail "episodes directory not found"
[ -d days ] || fail "days directory not found"
[ -d assets/audio ] || fail "assets/audio directory not found"
[ -f assets/ogp.png ] || fail "assets/ogp.png not found"

if grep -R --line-number --exclude='_template.html' --exclude='_template.md' 'YYYY-MM-DD' episodes days index.html; then
  fail "Unreplaced template marker YYYY-MM-DD found"
fi

mapfile -t episode_sources < <(find episodes -maxdepth 1 -type f -name '*.md' ! -name '_template.md' | sort)
[ ${#episode_sources[@]} -gt 0 ] || fail "No episode sources found"

for source in "${episode_sources[@]}"; do
  base="$(basename "$source")"
  date="${base%.md}"
  [[ "$date" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] || fail "Unexpected episode source name: $base"

  [ -f "days/$date.html" ] || fail "Missing rendered HTML for $date"
  [ -f "scripts_text/$date.txt" ] || fail "Missing rendered script text for $date"
  [ -f "assets/audio/sample-news-$date.wav" ] || fail "Missing audio file for $date"
  [ -f "assets/ogp-$date.png" ] || fail "Missing OGP image for $date"

  grep -q "href=\"days/$date.html\"" index.html || fail "index.html does not link to days/$date.html"
  grep -q "sample-news-$date\.wav" "days/$date.html" || fail "days/$date.html does not reference sample-news-$date.wav"
  grep -q "assets/ogp-$date\.png\|/assets/ogp-$date\.png" "days/$date.html" || fail "days/$date.html does not reference ogp-$date.png"
done

echo "Validation OK"
