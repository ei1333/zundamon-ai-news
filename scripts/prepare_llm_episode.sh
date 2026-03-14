#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./scripts/prepare_llm_episode.sh [--theme THEME] YYYY-MM-DD [URL1 URL2 URL3]

Examples:
  ./scripts/prepare_llm_episode.sh 2026-03-13 \
    "https://example.com/a" \
    "https://example.com/b" \
    "https://example.com/c"

  ./scripts/prepare_llm_episode.sh --theme shogi 2026-03-13 \
    "https://www.shogi.or.jp/match_news/2026/03/260312_t_result_01.html" \
    "https://www.shogi.or.jp/news/2026/03/260308_n_result_01.html" \
    "https://www.shogi.or.jp/match_news/2026/03/260313_t_01.html"
EOF
}

THEME=""
if [ "${1:-}" = "--theme" ]; then
  if [ $# -lt 2 ]; then
    usage
    exit 1
  fi
  THEME="$2"
  shift 2
fi

if [ $# -ne 1 ] && [ $# -ne 4 ]; then
  usage
  exit 1
fi

DATE="$1"
URL1="${2:-}"
URL2="${3:-}"
URL3="${4:-}"

if ! [[ "$DATE" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
  echo "Invalid date format: $DATE" >&2
  echo "Expected YYYY-MM-DD" >&2
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

SCHEDULE_JSON="$(python3 scripts/show_schedule.py --json "$DATE")"
if [ -z "$THEME" ]; then
  THEME="$(printf '%s' "$SCHEDULE_JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("theme", "ai"))')"
fi

if [ -z "$URL1" ] || [ -z "$URL2" ] || [ -z "$URL3" ]; then
  echo "Schedule for $DATE:" >&2
  echo "$SCHEDULE_JSON" >&2
  echo >&2
  echo "Source suggestions:" >&2
  printf '%s' "$SCHEDULE_JSON" | python3 -c 'import json,sys; data=json.load(sys.stdin); [print(f"- {u}") for u in data.get("source_suggestions", [])]' >&2
  echo >&2
  echo "Pass 3 article URLs to continue." >&2
  exit 1
fi

mkdir -p drafts prompts/generated episodes

DRAFT_OUT="drafts/$DATE.$THEME.draft.md"
PROMPT_OUT="prompts/generated/$DATE.$THEME.prompt.txt"
EPISODE_OUT="episodes/$DATE.md"

if [ -e "$EPISODE_OUT" ]; then
  echo "Episode already exists: $EPISODE_OUT" >&2
  exit 1
fi

echo "==> Building draft: $DRAFT_OUT"
python3 scripts/draft_from_urls.py --theme "$THEME" --stdout "$DATE" \
  "$URL1" "$URL2" "$URL3" > "$DRAFT_OUT"

echo "==> Building LLM prompt: $PROMPT_OUT"
python3 scripts/build_rewrite_prompt.py "$DATE" --theme "$THEME" --draft-file "$DRAFT_OUT" > "$PROMPT_OUT"

echo "==> Prepared files"
echo "- Draft:  $DRAFT_OUT"
echo "- Prompt: $PROMPT_OUT"
echo
echo "Next steps:"
echo "1. Send $PROMPT_OUT to your LLM"
echo "2. Save the returned Markdown to $EPISODE_OUT"
echo "3. Run: ./scripts/build_episode.sh $DATE"
