#!/bin/sh
# Hash every regular file in a tree, excluding bytecode caches.
cd "$1" && find . -type f -not -path '*/__pycache__/*' -not -path './.pytest_cache/*' -print0 | sort -z | xargs -0 sha256sum | sha256sum | cut -c1-64
