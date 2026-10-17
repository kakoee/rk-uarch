#!/bin/sh
set -eu
printf '%s\0' "$@" > /receipts/${C2_RUN_TAG}.linker.$$.argv
/usr/bin/env -0 > /receipts/${C2_RUN_TAG}.linker.$$.env
exec /usr/bin/cc "$@"
