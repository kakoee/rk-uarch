#!/usr/bin/env bash
# A committed prediction is frozen (build-spec §2.7). New predictions are new files.
changed=$(git diff --cached --name-only --diff-filter=MDR | grep -E '^validation/L3_silicon/.*/predictions/')
if [ -n "$changed" ]; then
  echo "committed predictions are frozen; add a new file in a new commit instead:"
  echo "$changed"
  exit 1
fi
exit 0
