#!/bin/sh
# F2 reproducer: does any test notice when the SHIPPED checker copy drifts from validation/?
# Usage: checker_drift.sh DISPOSABLE_DEV_TREE DEV_PYTHON RELEASE_BINARY
# Runs the proposal's own ordinary tests (baseline, then after one-line drift in the shipped
# copy only), first as in `make test-fast` (native marker excluded), then with ORDINARY_NATIVE.
set -u
# Never read or write bytecode: a same-size, same-second restore can otherwise leave a stale .pyc.
export PYTHONDONTWRITEBYTECODE=1
tree=$1; py=$2; bin=$3
target=$tree/src/rkuarch/verification/component/observations_v3.py
find "$tree/src" "$tree/contract" "$tree/tests" "$tree/validation" -name __pycache__ -type d -prune -exec rm -rf {} +
tests="tests/unit/test_ordinary_native.py tests/native/test_ordinary_process.py validation/component/test_f5_mechanism_duration.py validation/component/test_phase_laws.py"
run() { (cd "$tree" && env -u ORDINARY_NATIVE "$@" "$py" -m pytest -q -p no:cacheprovider $tests 2>&1 | tail -1); }
echo "baseline, test-fast markers:";       run env PYTEST_ADDOPTS='-m "not nightly and not silicon and not native"'
cp "$target" "$target.orig"
sed -i 's/("compute_overhead", 32)/("compute_overhead", 31)/' "$target"
grep -c '("compute_overhead", 31)' "$target" | sed 's/^/drifted lines in shipped copy: /'
echo "drifted, test-fast markers:";        run env PYTEST_ADDOPTS='-m "not nightly and not silicon and not native"'
echo "drifted, all markers, no binary:";   run env
echo "drifted, ORDINARY_NATIVE=release:";  run env ORDINARY_NATIVE="$bin"
mv "$target.orig" "$target"
find "$tree/src" -name __pycache__ -type d -prune -exec rm -rf {} +
echo "restored, ORDINARY_NATIVE=release:"; run env ORDINARY_NATIVE="$bin"
echo "restored:"; cmp "$target" "$tree/../recon/src/rkuarch/verification/component/observations_v3.py" && echo identical
