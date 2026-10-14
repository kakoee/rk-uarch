#!/bin/sh
# Snapshot "<mtime_ns> <sha256> <path>" for every regular file except bytecode caches.
cd "$1" && find . -type f -not -path '*/__pycache__/*' -not -path './.pytest_cache/*' -not -path './.ruff_cache/*' -printf '%T@ %p\n' | sort -k2 | while read -r t p; do printf '%s %s %s\n' "$t" "$(sha256sum "$p" | cut -c1-64)" "$p"; done
