#!/usr/bin/env bash
# Lane A U-REVIEW Stage 3: reproduce author checks, bounded random revert/restore, and
# reviewer-independent sufficiency probe, all on private git-archive exports.
# Usage: run_stage3.sh <live-clone> <empty-scratch-dir> <probe-dir>
set -u
LIVE=$1; SCRATCH=$2; PROBES=$3
TARGET=a7f4acb12d4bd4adf29668a9707440738aa44f09
STAGE1=184d2c2b08c28a01673be143b086ef223ba6706a
V=$LIVE/.venv/bin
unset PYTHONPATH MYPYPATH
T=$SCRATCH/target; O=$SCRATCH/stage1; R=$SCRATCH/revert
py() { (cd "$1" && shift && "$V/python" -I -B "$@"); }

echo "## environment"
echo "utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)  uname: $(uname -sr)"
echo "target: $TARGET tree: $(git -C "$LIVE" rev-parse "$TARGET^{tree}")"
echo "stage1: $STAGE1 tree: $(git -C "$LIVE" rev-parse "$STAGE1^{tree}")"
echo "live HEAD: $(git -C "$LIVE" rev-parse HEAD)"
echo "venv: $($V/python -V 2>&1); PYTHONPATH=[${PYTHONPATH-unset}] MYPYPATH=[${MYPYPATH-unset}]"
echo "non-doc paths changed $STAGE1..$TARGET: $(git -C "$LIVE" diff --name-only "$STAGE1" "$TARGET" -- . ':(exclude)docs' | wc -l)"
for d in "$T" "$O"; do rm -rf "$d"; mkdir -p "$d"; done
git -C "$LIVE" archive "$TARGET" | tar -x -C "$T"
git -C "$LIVE" archive "$STAGE1" | tar -x -C "$O"

echo; echo "## import origin in target export"
py "$T" -c "import sys; sys.path[:0]=['contract','src']; import uarch_contract, rkuarch; print(uarch_contract.__file__); print(rkuarch.__file__)"

echo; echo "## extract author blocks verbatim from target"
"$V/python" -I -c "
import re, pathlib
t = pathlib.Path('$T/docs/reviews')
for src, dst in (('U3-A-stage2-proposal-checks.md', 'a_stage2_block.py'), ('U3-native-stage-design-v2/checks.md', 'a_package_checker.py')):
    body = (t / src).read_text()
    pathlib.Path('$SCRATCH', dst).write_text(re.search(r'\`\`\`python\n(.*?)\n\`\`\`', body, re.S).group(1) + '\n')"
sha256sum "$SCRATCH/a_stage2_block.py" "$SCRATCH/a_package_checker.py" | sed "s|$SCRATCH/||"

echo; echo "## author f1-f10 on target (expect 10 PASS + shared PASS)"
py "$T" "$SCRATCH/a_stage2_block.py"; echo "exit=$?"
echo; echo "## author f1-f10 on Stage 1 export (expect 10 FAIL; whole-old run, NOT the random revert)"
py "$O" "$SCRATCH/a_stage2_block.py"; echo "exit=$?"
echo; echo "## author package checker on target"
(cd "$T" && /usr/bin/python3 -I "$SCRATCH/a_package_checker.py"); echo "exit=$?"

echo; echo "## reviewer independent sufficiency probe: target (expect all PASS), Stage 1 (expect all FAIL)"
py "$SCRATCH" "$PROBES/stage3_independent.py" "$T"; echo "exit=$?"
py "$SCRATCH" "$PROBES/stage3_independent.py" "$O" | tail -1; echo "exit=$?"

echo; echo "## random selection (drawn before this run)"
cat "$PROBES/random_selection.txt"

echo; echo "## bounded revert of A-F9 only (full A-F9 scope)"
rm -rf "$R"; cp -a "$T" "$R"
/usr/bin/python3 -I "$PROBES/revert_af9.py" "$R" full
echo "--- exact reverted scope (diff target -> revert copy):"
diff -ru "$T/docs" "$R/docs" | sed "s|$SCRATCH/||g"
echo "--- author f1-f10 on revert copy (expect only A-F9 FAIL)"
py "$R" "$SCRATCH/a_stage2_block.py"; echo "exit=$?"
echo "--- which f9 assertion fails"
/usr/bin/python3 -I "$PROBES/f9_reason.py" "$R"
echo "--- independent probe on revert copy (expect only A-F9 FAIL)"
py "$SCRATCH" "$PROBES/stage3_independent.py" "$R"; echo "exit=$?"

for part in delivery u0011; do
  echo; echo "## partial A-F9 revert: $part only (each half must be caught)"
  rm -rf "$R"; cp -a "$T" "$R"
  /usr/bin/python3 -I "$PROBES/revert_af9.py" "$R" "$part"
  py "$R" "$SCRATCH/a_stage2_block.py" | grep -E "^A-F9|failures"
  /usr/bin/python3 -I "$PROBES/f9_reason.py" "$R"
done

echo; echo "## restore (fresh copy of target) and rerun"
rm -rf "$R"; cp -a "$T" "$R"
diff -r "$T" "$R" && echo "restored copy identical to target export"
py "$R" "$SCRATCH/a_stage2_block.py"; echo "exit=$?"
/usr/bin/python3 -I "$PROBES/f9_reason.py" "$R"

echo; echo "## bounded doc-consistency pytest on target (explicit config/root)"
(cd "$T" && "$V/python" -I -B -m pytest -q -p no:cacheprovider -c pyproject.toml --rootdir . tests/unit/test_prompt_sync.py 2>&1 | tail -1)

echo; echo "## preservation hashes (live, read-only)"
sha256sum "$LIVE/docs/reviews/U3-lane-A-review.md" "$LIVE"/docs/reviews/U3-independent-review-A-v1/* | sed "s|$LIVE/||"
