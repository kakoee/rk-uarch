#!/usr/bin/env bash
# Human-only continuation of the accepted freeze: first created run already preserved.
set -euo pipefail
cd /home/jjaff/AI-infra-simulation/rk-uarch-u2-integration
U2_REVIEW_ROOT=/home/jjaff/AI-infra-simulation/rk-uarch-u2-integration/docs/reviews/U2-source-input-freeze-v1
U2_RUN_ROOT=/home/jjaff/AI-infra-simulation/rk-uarch-u2-integration/docs/reviews/U2-real-generation-v1
U2_CANDIDATE="$U2_RUN_ROOT/candidate"
U2_PYTHON=/home/jjaff/AI-infra-simulation/rk-uarch/.venv/bin/python
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:contract:src
export UV_PROJECT_ENVIRONMENT=/tmp/rk-sim-u1-jjaffari-1e5706e
unset PARAMS
# Preserve the first run and refuse to overwrite any later-step evidence.
"$U2_PYTHON" -B - <<'CHECK'
from pathlib import Path
import hashlib
r=Path('/home/jjaff/AI-infra-simulation/rk-uarch-u2-integration/docs/reviews/U2-real-generation-v1')
assert hashlib.sha256((r/'created.log').read_bytes()).hexdigest()=='4600af4f6276705ef1f199d4324bcae10064a8a75e71b6eaccace770e062220b'
assert hashlib.sha256((r/'candidate/MANIFEST.json').read_bytes()).hexdigest()=='2d15afd7dd80124f70d387bc7cde4addda29162cd49370d40da7b99830709b44'
for name in ['preflight-between.json','verified-identical.log','preflight-after.json','strict-check.txt','raw-inspection.json','semantic-diff.json','candidate-manifest-sha256.txt']:
 assert not (r/name).exists() and not (r/name).is_symlink(), f'Existing evidence; stop for reconciliation: {name}'
CHECK
"$U2_PYTHON" -B "$U2_REVIEW_ROOT/preflight.py" > "$U2_RUN_ROOT/preflight-between.json"
# EXACT generator command/inputs from the first run, in a new process.
U2_COMMAND=("$U2_PYTHON" -B -m scripts.vendor_rk
  --sha 1e5706e0ebfcc67c1a7333079a35b75f693e9963
  --rk /home/jjaff/AI-infra-simulation/rk-sim-u1-pin
  --inputs "$U2_REVIEW_ROOT/inputs"
  --input-manifest-sha256 81df43c063396c89bd3333f43957c71efc7087cfa65b2a401177f2227fca8898
  --output-root "$U2_CANDIDATE")
UARCH_HUMAN=1 "${U2_COMMAND[@]}" 2>&1 | tee "$U2_RUN_ROOT/verified-identical.log"
"$U2_PYTHON" -B - <<'CHECK'
from pathlib import Path
r=Path('/home/jjaff/AI-infra-simulation/rk-uarch-u2-integration/docs/reviews/U2-real-generation-v1')
expected=f'verified-identical: 48 files at {r / "candidate"}'
assert expected in (r/'verified-identical.log').read_text().splitlines(), 'Second run did not report verified-identical'
CHECK
"$U2_PYTHON" -B "$U2_REVIEW_ROOT/preflight.py" > "$U2_RUN_ROOT/preflight-after.json"
"$U2_PYTHON" -B -m scripts.vendor_rk --check --output-root "$U2_CANDIDATE" > "$U2_RUN_ROOT/strict-check.txt" 2>&1
"$U2_PYTHON" -B -m tests.u2_refresh inspect "$U2_CANDIDATE" > "$U2_RUN_ROOT/raw-inspection.json"
"$U2_PYTHON" -B -m scripts.u2_inputs compare contract/vendor/rk-sim@1e5706e0ebfcc67c1a7333079a35b75f693e9963 "$U2_CANDIDATE" > "$U2_RUN_ROOT/semantic-diff.json"
"$U2_PYTHON" -B - <<'CHECK'
from pathlib import Path
import hashlib
r=Path('/home/jjaff/AI-infra-simulation/rk-uarch-u2-integration/docs/reviews/U2-real-generation-v1')
p=r/'candidate/MANIFEST.json'
text=f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p}\n'
with (r/'candidate-manifest-sha256.txt').open('x') as f:f.write(text)
print(text,end='')
CHECK
printf '%s\n' 'STOP: return the final output for coordinator audit. Candidate adoption remains separate.'
