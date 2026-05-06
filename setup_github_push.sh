#!/usr/bin/env bash
set -euo pipefail

DEFAULT_REPO_URL="https://github.com/eyepoint2218/javis.git"
REPO_URL="${1:-$DEFAULT_REPO_URL}"
CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
BRANCH="${2:-$CURRENT_BRANCH}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: run this script inside a git repository"
  exit 1
fi

if ! git rev-parse --verify HEAD >/dev/null 2>&1; then
  echo "Error: there is no commit yet. Run:"
  echo "  git add . && git commit -m 'init: first commit'"
  exit 1
fi

if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "$REPO_URL"
else
  git remote add origin "$REPO_URL"
fi

echo "Remote origin set to: $(git remote get-url origin)"
echo "Pushing branch '$BRANCH'..."
git push -u origin "$BRANCH"

echo "Done."
echo "If Pages is enabled, open: https://eyepoint2218.github.io/javis/"
