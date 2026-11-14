#!/usr/bin/env bash
# Zip one skill for upload to Claude.ai (Settings > Capabilities > Skills).
# The zip's root is the skill folder, as Claude.ai expects.
#
# Usage: scripts/package-skill.sh SKILL_NAME [OUT_DIR]
#   SKILL_NAME  folder name under plugins/*/skills/ (e.g. visualize)
#   OUT_DIR     where to write SKILL_NAME.zip (default: dist/)
set -euo pipefail

name="${1:?usage: scripts/package-skill.sh SKILL_NAME [OUT_DIR]}"
repo_root="$(cd "$(dirname "$0")/.." && pwd)"
out_dir="${2:-$repo_root/dist}"

matches=()
while IFS= read -r d; do matches+=("$d"); done < <(
  find "$repo_root/plugins" -mindepth 3 -maxdepth 3 -type d -path "*/skills/$name"
)

if [ "${#matches[@]}" -ne 1 ]; then
  echo "expected exactly one skill folder named '$name', found ${#matches[@]}" >&2
  exit 1
fi

skill_dir="${matches[0]}"
mkdir -p "$out_dir"
out_dir="$(cd "$out_dir" && pwd)"
rm -f "$out_dir/$name.zip"
(cd "$(dirname "$skill_dir")" && zip -rq "$out_dir/$name.zip" "$name" -x '*/.DS_Store' '*/__pycache__/*' '*.pyc')
echo "Wrote $out_dir/$name.zip"
