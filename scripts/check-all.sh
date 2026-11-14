#!/usr/bin/env bash
# Run every quality gate. CI runs this same script, so local and CI can't drift.
# Requires: .venv with requirements-dev.txt installed, node_modules (npm install),
# and the `claude` CLI on PATH for plugin validation.
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo_root"

py=".venv/bin"
[ -x "$py/python" ] || py="$(dirname "$(command -v python3)")"

step() { printf '\n== %s\n' "$1"; }

step "markdownlint"
npx --no-install markdownlint-cli2

step "ruff check"
"$py/ruff" check .

step "ruff format --check"
"$py/ruff" format --check .

step "shellcheck"
"$py/shellcheck" scripts/*.sh .githooks/pre-commit

step "pytest"
"$py/python" -m pytest -q

step "frontmatter"
"$py/python" scripts/check_frontmatter.py

step "privacy"
scripts/check-privacy.sh

step "claude plugin validate"
claude plugin validate .

printf '\nAll gates passed.\n'
