#!/usr/bin/env bash
# Fork koreainvestment/open-trading-api to the authenticated user, add remote "fork", push main.
# Requires: GH_TOKEN or GITHUB_TOKEN (classic PAT: repo scope) OR logged-in `gh` (gh auth token).
set -euo pipefail

UPSTREAM_OWNER="koreainvestment"
UPSTREAM_REPO="open-trading-api"
REMOTE_NAME="${FORK_REMOTE_NAME:-fork}"
BRANCH="${PUSH_BRANCH:-main}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  echo "Using GitHub CLI (logged in)."
  gh repo fork "${UPSTREAM_OWNER}/${UPSTREAM_REPO}" --remote=true --remote-name="$REMOTE_NAME" 2>/dev/null || true
  if ! git remote get-url "$REMOTE_NAME" >/dev/null 2>&1; then
    LOGIN="$(gh api user --jq .login)"
    git remote add "$REMOTE_NAME" "https://github.com/${LOGIN}/${UPSTREAM_REPO}.git"
  fi
  echo "Pushing ${BRANCH} to ${REMOTE_NAME} ..."
  git push -u "$REMOTE_NAME" "$BRANCH"
  echo "Done."
  exit 0
fi

TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
if [[ -z "$TOKEN" ]]; then
  echo "No GitHub auth. Do one of:" >&2
  echo "  gh auth login   # then re-run this script" >&2
  echo "  export GH_TOKEN=ghp_...   # classic PAT with 'repo', then re-run" >&2
  exit 1
fi

USER_JSON="$(curl -sS -H "Authorization: Bearer ${TOKEN}" -H "Accept: application/vnd.github+json" "https://api.github.com/user")"
LOGIN="$(python3 -c "import json,sys; print(json.load(sys.stdin).get('login',''))" <<<"$USER_JSON")"
if [[ -z "$LOGIN" ]]; then
  echo "Could not read GitHub login from /user (check token)." >&2
  echo "$USER_JSON" >&2
  exit 1
fi

FORK_URL="https://github.com/${LOGIN}/${UPSTREAM_REPO}.git"
echo "Authenticated as: ${LOGIN}"

if ! curl -sS -o /dev/null -w "%{http_code}" -H "Authorization: Bearer ${TOKEN}" "https://api.github.com/repos/${LOGIN}/${UPSTREAM_REPO}" | grep -q '^200$'; then
  echo "Creating fork ${LOGIN}/${UPSTREAM_REPO} ..."
  curl -sS -X POST \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Accept: application/vnd.github+json" \
    "https://api.github.com/repos/${UPSTREAM_OWNER}/${UPSTREAM_REPO}/forks" >/dev/null
  echo "Waiting for fork to be available..."
  for _ in $(seq 1 60); do
    code="$(curl -sS -o /dev/null -w "%{http_code}" -H "Authorization: Bearer ${TOKEN}" "https://api.github.com/repos/${LOGIN}/${UPSTREAM_REPO}")"
    if [[ "$code" == "200" ]]; then break; fi
    sleep 2
  done
fi

if git remote get-url "$REMOTE_NAME" >/dev/null 2>&1; then
  git remote set-url "$REMOTE_NAME" "$FORK_URL"
else
  git remote add "$REMOTE_NAME" "$FORK_URL"
fi

echo "Pushing ${BRANCH} to ${REMOTE_NAME} (${FORK_URL}) ..."
git push -u "$REMOTE_NAME" "$BRANCH"
echo "Done."
