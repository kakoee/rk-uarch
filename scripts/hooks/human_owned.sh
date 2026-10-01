#!/usr/bin/env bash
# Human-owned paths (build-spec §6.3). A human committing sets UARCH_HUMAN=1.
owned=$(git diff --cached --name-only | grep -E '^(contract/|tests/golden/expected/|CLAUDE\.md|docs/decisions/)')
if [ -n "$owned" ] && [ "${UARCH_HUMAN:-0}" != "1" ]; then
  echo "human-owned path(s) staged; if you are a human, commit with UARCH_HUMAN=1:"
  echo "$owned"
  exit 1
fi
exit 0
