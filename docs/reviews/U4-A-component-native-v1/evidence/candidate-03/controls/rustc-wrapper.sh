#!/bin/sh
set -eu
printf '%s\0' "$@" > /receipts/${C2_RUN_TAG}.rustc.$$.argv
/usr/bin/env -0 > /receipts/${C2_RUN_TAG}.rustc.$$.env
exec "$@"
