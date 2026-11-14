#!/usr/bin/env bash
# Scan files for content that must never be committed to this public-ready repo.
#
# Built-in rule: absolute home paths containing a username (use ~ instead).
# Extra rules: one extended regex per line in .privacy-patterns.local
# (gitignored; for private names that can't be written into a public repo).
# Blank lines and lines starting with # in that file are ignored.
#
# Usage:
#   scripts/check-privacy.sh            # scan all tracked files
#   scripts/check-privacy.sh FILE...    # scan only the given files (pre-commit)
# Exit code 0 when clean, 1 when anything matches.
set -uo pipefail

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$repo_root" || exit 1

# Character classes keep these patterns from matching this script itself.
patterns=('/[U]sers/[A-Za-z0-9._-]+/' '/[h]ome/[A-Za-z0-9._-]+/')

local_patterns="${PLOTPOINT_PRIVACY_PATTERNS:-.privacy-patterns.local}"
if [ -f "$local_patterns" ]; then
  while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in ''|'#'*) continue ;; esac
    patterns+=("$line")
  done < "$local_patterns"
fi

files=()
if [ "$#" -gt 0 ]; then
  files=("$@")
else
  while IFS= read -r f; do files+=("$f"); done < <(git ls-files)
fi

status=0
for f in "${files[@]}"; do
  [ -f "$f" ] || continue
  case "$f" in LICENSE|.privacy-patterns.local) continue ;; esac
  for p in "${patterns[@]}"; do
    if grep -nIE -- "$p" "$f" >/dev/null 2>&1; then
      grep -nIE -- "$p" "$f" | sed "s|^|PRIVACY $f:|"
      status=1
    fi
  done
done

if [ "$status" -ne 0 ]; then
  echo "Privacy check failed: remove the matches above (use ~ for home paths)." >&2
fi
exit "$status"
