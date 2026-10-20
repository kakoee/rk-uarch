#!/bin/sh
# Was the ordinary consume->check_v3 wiring tested before the cleanup (v1)?
# Usage: v1_wiring_baseline.sh V1_TREE WORK DEV_PYTHON V1_BINARY
# Disables only the check_v3 call in v1 rkuarch/engines/native/ordinary.py (disposable copy) and
# runs every v1 test module that imports rkuarch.engines.native.ordinary, with the v1 binary.
set -u
v1=$1; work=$2; py=$3; bin=$4
export PYTHONDONTWRITEBYTECODE=1
unset PYTHONPATH
rm -rf "$work/wiring"; cp -a "$v1" "$work/wiring"
f="$work/wiring/src/rkuarch/engines/native/ordinary.py"
[ "$(grep -c '^    check_v3($' "$f")" = 1 ] || { echo "anchor missing"; exit 2; }
sed -i 's/^    check_v3($/    (lambda *_: None)(/' "$f"
cd "$work/wiring" && ORDINARY_NATIVE="$bin" "$py" -m pytest -q -p no:cacheprovider -rf \
  tests/unit/test_ordinary_native.py tests/native/test_ordinary_process.py 2>&1 | tail -2
