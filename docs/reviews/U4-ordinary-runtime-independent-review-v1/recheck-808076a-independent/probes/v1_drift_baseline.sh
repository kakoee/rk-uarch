#!/bin/sh
# Was the compute-overhead drift gap pre-existing in v1, or created by the v2 cleanup?
# Usage: v1_drift_baseline.sh V1_TREE WORK DEV_PYTHON FILES_TXT
# Runs the v1 default tests that statically reach validation.component.observations_v3
# (the v1 copy used by those tests), first unmodified, then with ("compute_overhead", 32)->31
# in that copy only. Bytecode disabled; disposable copies; failure sets are compared.
set -u
v1=$1; work=$2; py=$3; files=$(cat "$4")
export PYTHONDONTWRITEBYTECODE=1
unset PYTHONPATH ORDINARY_NATIVE
for mode in baseline drift; do
  rm -rf "$work/$mode"; cp -a "$v1" "$work/$mode"
  if [ "$mode" = drift ]; then
    f="$work/$mode/validation/component/observations_v3.py"
    [ "$(grep -c '("compute_overhead", 32)' "$f")" = 1 ] || { echo "drift anchor missing"; exit 2; }
    sed -i 's/("compute_overhead", 32)/("compute_overhead", 31)/' "$f"
  fi
  (cd "$work/$mode" && "$py" -m pytest -q -p no:cacheprovider -rf \
     -m "not nightly and not silicon and not native" $files > "$work/$mode.log" 2>&1)
  echo "$mode: exit=$? $(tail -1 "$work/$mode.log")"
  grep '^FAILED' "$work/$mode.log" | sed 's/ - .*//' | sort > "$work/$mode.failed"
done
echo "failures only under drift:"; comm -13 "$work/baseline.failed" "$work/drift.failed"
echo "(end)"
