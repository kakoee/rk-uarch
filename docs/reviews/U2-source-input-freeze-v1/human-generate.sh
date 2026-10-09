#!/usr/bin/env bash
# PROPOSAL: Javid runs only AFTER explicit acceptance of U2-source-input-freeze-v1.
# Agents must not execute this file. No adoption, staging, commit, push or tag.
set -euo pipefail
cd /home/jjaff/AI-infra-simulation/rk-uarch-u2-integration
U2_REVIEW_ROOT=/home/jjaff/AI-infra-simulation/rk-uarch-u2-integration/docs/reviews/U2-source-input-freeze-v1
U2_RUN_ROOT=/home/jjaff/AI-infra-simulation/rk-uarch-u2-integration/docs/reviews/U2-real-generation-v1
U2_CANDIDATE="$U2_RUN_ROOT/candidate"
U2_PYTHON=/home/jjaff/AI-infra-simulation/rk-uarch/.venv/bin/python
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:contract:src
export UV_PROJECT_ENVIRONMENT=/tmp/rk-sim-u1-jjaffari-1e5706e
unset PARAMS
# Fail on any drift before creating the dedicated evidence directory.
"$U2_PYTHON" -B "$U2_REVIEW_ROOT/preflight.py"
test ! -e "$U2_RUN_ROOT"
test ! -L "$U2_RUN_ROOT"
mkdir "$U2_RUN_ROOT"
"$U2_PYTHON" -B "$U2_REVIEW_ROOT/preflight.py" > "$U2_RUN_ROOT/preflight.json"
git rev-parse HEAD > "$U2_RUN_ROOT/local-HEAD.txt"
git branch --show-current > "$U2_RUN_ROOT/local-branch.txt"
# Same exact command in two fresh processes: missing destination, then byte verification.
U2_COMMAND=("$U2_PYTHON" -B -m scripts.vendor_rk
  --sha 1e5706e0ebfcc67c1a7333079a35b75f693e9963
  --rk /home/jjaff/AI-infra-simulation/rk-sim-u1-pin
  --inputs "$U2_REVIEW_ROOT/inputs"
  --input-manifest-sha256 81df43c063396c89bd3333f43957c71efc7087cfa65b2a401177f2227fca8898
  --output-root "$U2_CANDIDATE")
UARCH_HUMAN=1 "${U2_COMMAND[@]}" 2>&1 | tee "$U2_RUN_ROOT/created.log"
rg '^created:' "$U2_RUN_ROOT/created.log"
"$U2_PYTHON" -B "$U2_REVIEW_ROOT/preflight.py" > "$U2_RUN_ROOT/preflight-between.json"
UARCH_HUMAN=1 "${U2_COMMAND[@]}" 2>&1 | tee "$U2_RUN_ROOT/verified-identical.log"
rg '^verified-identical:' "$U2_RUN_ROOT/verified-identical.log"
"$U2_PYTHON" -B "$U2_REVIEW_ROOT/preflight.py" > "$U2_RUN_ROOT/preflight-after.json"
"$U2_PYTHON" -B -m scripts.vendor_rk --check --output-root "$U2_CANDIDATE" > "$U2_RUN_ROOT/strict-check.txt" 2>&1
"$U2_PYTHON" -B -m tests.u2_refresh inspect "$U2_CANDIDATE" > "$U2_RUN_ROOT/raw-inspection.json"
"$U2_PYTHON" -B -m scripts.u2_inputs compare   contract/vendor/rk-sim@1e5706e0ebfcc67c1a7333079a35b75f693e9963   "$U2_CANDIDATE" > "$U2_RUN_ROOT/semantic-diff.json"
sha256sum "$U2_CANDIDATE/MANIFEST.json" | tee "$U2_RUN_ROOT/candidate-manifest-sha256.txt"
printf '%s\n' 'STOP: return both generation logs and the candidate manifest digest for coordinator audit. Adoption is separate.'
