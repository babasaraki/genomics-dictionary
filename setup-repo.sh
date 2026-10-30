#!/usr/bin/env bash
# Create the GitHub repository (or use one you just created) and publish the site.
#
#   ./setup-repo.sh YOUR-GITHUB-USERNAME [repository-name]
#
# What it does, in order:
#   1. sets base_url / repository_url in content/site.json to the address the site will live at
#   2. validates the corpus, rebuilds every page, runs the acceptance checks
#   3. initialises Git, commits, and pushes to GitHub
# It stops at the first failure and never pushes a site that did not validate.

set -euo pipefail

USERNAME="${1:-}"
REPO="${2:-genomics-dictionary}"

if [ -z "$USERNAME" ]; then
  echo "Usage: ./setup-repo.sh YOUR-GITHUB-USERNAME [repository-name]" >&2
  exit 2
fi

cd "$(dirname "$0")"

if [ ! -f content/site.json ]; then
  echo "Run this from inside the genomics-dictionary folder." >&2
  exit 2
fi

# A repository named USERNAME.github.io is served at the account root, not in a subpath.
if [ "$REPO" = "${USERNAME}.github.io" ]; then
  BASE="https://${USERNAME}.github.io"
else
  BASE="https://${USERNAME}.github.io/${REPO}"
fi
REMOTE="https://github.com/${USERNAME}/${REPO}.git"

echo "==> Site address:  ${BASE}"
echo "==> Repository:    ${REMOTE}"
echo

echo "==> 1/4  Writing the site address into content/site.json"
python3 - "$BASE" "https://github.com/${USERNAME}/${REPO}" <<'PY'
import json, sys
base, repo = sys.argv[1], sys.argv[2]
with open("content/site.json", encoding="utf-8") as fh:
    site = json.load(fh)
site["base_url"] = base
site["repository_url"] = repo
with open("content/site.json", "w", encoding="utf-8") as fh:
    json.dump(site, fh, indent=1, ensure_ascii=False)
    fh.write("\n")
print("    base_url     = %s" % base)
print("    repository_url = %s" % repo)
PY

echo
echo "==> 2/4  Validating the entry corpus"
python3 tools/validate.py

echo
echo "==> 3/4  Rebuilding the site and running the acceptance checks"
python3 tools/build.py
python3 tools/acceptance_check.py >/dev/null && echo "    acceptance checks passed"
rm -rf tools/__pycache__

echo
echo "==> 4/4  Publishing to GitHub"
if ! git config user.email >/dev/null 2>&1; then
  echo "    Git has no author identity on this machine. Set one first:" >&2
  echo "      git config --global user.name  \"Your Name\"" >&2
  echo "      git config --global user.email \"you@example.org\"" >&2
  exit 2
fi

if [ ! -d .git ]; then
  git init -b main
fi
git add -A
if git diff --cached --quiet; then
  echo "    Nothing new to commit."
else
  git commit -m "The Genomics Dictionary: static site with 200 draft entries"
fi

if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "$REMOTE"
else
  git remote add origin "$REMOTE"
fi

if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  gh repo view "${USERNAME}/${REPO}" >/dev/null 2>&1 || \
    gh repo create "${USERNAME}/${REPO}" --public --description "Open-access dictionary of genomics terminology" --source=. --remote=origin
fi

git branch -M main
git push -u origin main

cat <<EOF

Done. Two manual steps remain, both in the browser:

  1. https://github.com/${USERNAME}/${REPO}/settings/pages
     Build and deployment -> Source -> GitHub Actions   (takes effect immediately)

  2. https://github.com/${USERNAME}/${REPO}/actions
     Watch 'Deploy to GitHub Pages' finish, then open ${BASE}/

EOF
