#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP_DIR="$(mktemp -d)"
WORKTREE_DIR="$TMP_DIR/site"
cleanup() {
  git -C "$REPO_ROOT" worktree remove --force "$WORKTREE_DIR" 2>/dev/null || true
  git -C "$REPO_ROOT" worktree prune 2>/dev/null || true
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

PUBLIC_BRANCH="gh-pages"

cd "$REPO_ROOT"

git fetch origin "$PUBLIC_BRANCH"

git worktree add "$WORKTREE_DIR" "$PUBLIC_BRANCH"

find "$WORKTREE_DIR" -mindepth 1 -maxdepth 1 \
  ! -name '.git' \
  -exec rm -rf {} +

cp -R "$REPO_ROOT/index.html" "$WORKTREE_DIR/index.html"
cp -R "$REPO_ROOT/assets" "$WORKTREE_DIR/assets"
cp -R "$REPO_ROOT/days" "$WORKTREE_DIR/days"
rm -f "$WORKTREE_DIR/days/_template.html"

cd "$WORKTREE_DIR"
git add -A

if git diff --cached --quiet; then
  echo "No changes to publish"
  exit 0
fi

git commit -m "Publish site from main"
git push origin "$PUBLIC_BRANCH"

echo "Published to $PUBLIC_BRANCH"
