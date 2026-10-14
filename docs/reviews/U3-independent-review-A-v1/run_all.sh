#!/usr/bin/env bash
# Lane A independent review: reproduce every bounded check from a fresh private export.
# Usage: run_all.sh <rk-uarch-live-clone> <scratch-dir> <probe-dir>
# Writes only under <scratch-dir>; reads the live clone's Git objects and venv binaries.
set -u
LIVE=$1; SCRATCH=$2; PROBES=$3
TARGET=184d2c2b08c28a01673be143b086ef223ba6706a
EXPORT=$SCRATCH/export-fresh
V=$LIVE/.venv/bin
unset PYTHONPATH MYPYPATH

echo "## environment"
echo "date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "target: $TARGET tree: $(git -C "$LIVE" rev-parse "$TARGET^{tree}")"
echo "live HEAD: $(git -C "$LIVE" rev-parse HEAD) (not the review target)"
echo "uname: $(uname -sr)"
echo "venv python: $($V/python -V 2>&1); system python3: $(/usr/bin/python3 -V 2>&1)"
echo "ruff: $($V/ruff --version); mypy: $($V/mypy --version)"
echo "PYTHONPATH=[${PYTHONPATH-unset}] MYPYPATH=[${MYPYPATH-unset}]"

rm -rf "$EXPORT"; mkdir -p "$EXPORT"
git -C "$LIVE" archive "$TARGET" | tar -x -C "$EXPORT"
echo "export: fresh git archive of target"

echo; echo "## import origin (runtime imports resolve to the export, not the editable live clone)"
(cd "$SCRATCH" && $V/python -I -c "import sys; sys.path[:0]=['$EXPORT/src','$EXPORT/contract']; import rkuarch, uarch_contract; print(rkuarch.__file__); print(uarch_contract.__file__)")

echo; echo "## A's checks.md block (extracted verbatim, run from export root with python3 -I)"
/usr/bin/python3 -I -c "
import re, pathlib
body = pathlib.Path('$EXPORT/docs/reviews/U3-native-stage-design-v2/checks.md').read_text()
pathlib.Path('$SCRATCH/a_checks_block.py').write_text(re.search(r'\`\`\`python\n(.*?)\n\`\`\`', body, re.S).group(1) + '\n')"
sha256sum "$SCRATCH/a_checks_block.py" | cut -d' ' -f1
(cd "$EXPORT" && /usr/bin/python3 -I "$SCRATCH/a_checks_block.py"); echo "exit=$?"

for p in probe_contract probe_ledger; do
  echo; echo "## $p (venv python -I, export imports asserted)"
  (cd "$SCRATCH" && $V/python -I "$PROBES/$p.py" "$EXPORT"); echo "exit=$?"
done
for p in probe_arithmetic probe_volume; do
  echo; echo "## $p (stdlib only)"
  (cd "$SCRATCH" && /usr/bin/python3 -I "$PROBES/$p.py"); echo "exit=$?"
done

echo; echo "## CI-form static checks on the export (no install; ambient paths unset)"
(cd "$EXPORT" && $V/ruff check --no-cache . 2>&1 | tail -1); echo "ruff exit=${PIPESTATUS[0]}"
(cd "$EXPORT" && $V/mypy --cache-dir="$SCRATCH/mypy1" src contract/uarch_contract scripts 2>&1 | tail -1)
(cd "$EXPORT" && $V/mypy --cache-dir="$SCRATCH/mypy2" --no-explicit-package-bases contract/tests 2>&1 | tail -1)

echo; echo "## bounded doc-consistency test on the export"
(cd "$EXPORT" && $V/python -I -m pytest -q -p no:cacheprovider tests/unit/test_prompt_sync.py 2>&1 | tail -1)

echo; echo "## B patch identity (not applied; B's suite not rerun by Lane A)"
sha256sum "$EXPORT/docs/reviews/U3-B-artifact-dependency-audit-v1/repair.patch" | cut -d' ' -f1
