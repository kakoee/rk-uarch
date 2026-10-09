#!/usr/bin/env bash
# Javid runs only after explicit U2-source-input-freeze-v2 acceptance.
# Agents must not execute this script. No adoption, commit, push or closure.
set -euo pipefail
cd /home/jjaff/AI-infra-simulation/rk-uarch-u2-integration
U2_REVIEW_ROOT="$PWD/docs/reviews/U2-source-input-freeze-v2"
U2_RUN_ROOT="$PWD/docs/reviews/U2-real-generation-v2"
U2_CANDIDATE="$U2_RUN_ROOT/candidate"
U2_PYTHON=/home/jjaff/AI-infra-simulation/rk-uarch/.venv/bin/python
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:contract:src
export UV_PROJECT_ENVIRONMENT=/tmp/rk-sim-u1-jjaffari-1e5706e
unset PARAMS
"$U2_PYTHON" -B "$U2_REVIEW_ROOT/preflight.py" --require-acceptance
test ! -e "$U2_RUN_ROOT"
test ! -L "$U2_RUN_ROOT"
mkdir "$U2_RUN_ROOT"
"$U2_PYTHON" -B "$U2_REVIEW_ROOT/preflight.py" --require-acceptance > "$U2_RUN_ROOT/preflight.json"
git rev-parse HEAD > "$U2_RUN_ROOT/local-HEAD.txt"
git branch --show-current > "$U2_RUN_ROOT/local-branch.txt"
U2_COMMAND=("$U2_PYTHON" -B -m scripts.vendor_rk
  --sha 1e5706e0ebfcc67c1a7333079a35b75f693e9963
  --rk /home/jjaff/AI-infra-simulation/rk-sim-u1-pin
  --inputs "$U2_REVIEW_ROOT/inputs"
  --input-manifest-sha256 9a30b29029a32339dfc6062e138cebc23f7f1474044b414068dd9c8113c1dca0
  --output-root "$U2_CANDIDATE")
UARCH_HUMAN=1 "${U2_COMMAND[@]}" 2>&1 | tee "$U2_RUN_ROOT/created.log"
"$U2_PYTHON" -B - "$U2_RUN_ROOT" created <<'CHECK'
import sys
from pathlib import Path
r=Path(sys.argv[1]); status=sys.argv[2]
assert f'{status}: 48 files at {r / "candidate"}' in (r/(status+'.log')).read_text().splitlines()
CHECK
"$U2_PYTHON" -B "$U2_REVIEW_ROOT/preflight.py" --require-acceptance > "$U2_RUN_ROOT/preflight-between.json"
UARCH_HUMAN=1 "${U2_COMMAND[@]}" 2>&1 | tee "$U2_RUN_ROOT/verified-identical.log"
"$U2_PYTHON" -B - "$U2_RUN_ROOT" verified-identical <<'CHECK'
import sys
from pathlib import Path
r=Path(sys.argv[1]); status=sys.argv[2]
assert f'{status}: 48 files at {r / "candidate"}' in (r/(status+'.log')).read_text().splitlines()
CHECK
"$U2_PYTHON" -B "$U2_REVIEW_ROOT/preflight.py" --require-acceptance > "$U2_RUN_ROOT/preflight-after.json"
"$U2_PYTHON" -B -m scripts.vendor_rk --check --output-root "$U2_CANDIDATE" > "$U2_RUN_ROOT/strict-check.txt" 2>&1
"$U2_PYTHON" -B -m tests.u2_refresh inspect "$U2_CANDIDATE" > "$U2_RUN_ROOT/raw-inspection.json"
"$U2_PYTHON" -B -m scripts.u2_inputs compare contract/vendor/rk-sim@1e5706e0ebfcc67c1a7333079a35b75f693e9963 "$U2_CANDIDATE" > "$U2_RUN_ROOT/semantic-diff.json"
"$U2_PYTHON" -B - "$U2_RUN_ROOT" <<'CHECK'
import hashlib,sys
from pathlib import Path
r=Path(sys.argv[1]); p=r/'candidate/MANIFEST.json'
line=f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p}\n'
with (r/'candidate-manifest-sha256.txt').open('x') as f:f.write(line)
print(line,end='')
CHECK
printf '%s\n' 'STOP: return both generation logs and the candidate manifest digest for coordinator audit. Candidate adoption remains separate.'
