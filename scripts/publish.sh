#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

PUBLIC_BRANCH="gh-pages"

cd "$REPO_ROOT"

git fetch origin "$PUBLIC_BRANCH"

git worktree add "$TMP_DIR/site" "$PUBLIC_BRANCH"

find "$TMP_DIR/site" -mindepth 1 -maxdepth 1 \
  ! -name '.git' \
  -exec rm -rf {} +

cp -R "$REPO_ROOT/index.html" "$TMP_DIR/site/index.html"
cp -R "$REPO_ROOT/assets" "$TMP_DIR/site/assets"
cp -R "$REPO_ROOT/days" "$TMP_DIR/site/days"
rm -f "$TMP_DIR/site/days/_template.html"

cd "$TMP_DIR/site"
git add -A

if git diff --cached --quiet; then
  echo "No changes to publish"
  exit 0
fi

git commit -m "Publish site from main"
git push origin "$PUBLIC_BRANCH"

echo "Published to $PUBLIC_BRANCH"
