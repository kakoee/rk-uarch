# How rk-uarch works

U2 implements a standalone stateless analytic estimate of one chip's LLM workload,
plus reproducible tables and provenance-aware reports. This description targets published
main commit `7fee0a8ed0c5d7bbb20b65c1cf68672470a5ac60`, tree
`deccb57a573717990762e60fb8819f0ae463ce20`. Publication and published-revision validation
have receipts; `u02-end` and sprint closure are still pending. The
[public workflow](u2-workflow.md) prepares explicit operators and mapping, executes the
analytic engine and packages results with reviewed source declarations. The
[accepted design](u2-design.md) defines its scope and limitations.

## From an NPU specification to an iteration estimate

Hardware values declare units and either a claim with its source or a stipulation with
its rationale. The accepted H1 and H2 inputs are proposed designs, not measured products.
Their original YAML proposal comments are preserved; [B1 acceptance](reviews/U2-B1-acceptance-record.md)
supplies the later approval. These are the current design examples, not executed golden
CI coverage. Validation checks declarations, not whether a chip achieves them
([hardware/source tests](../tests/unit/test_u2_b_badges.py)).

| Accepted design | Core grid | Declared compute/storage formats | Stipulations | Current analytic composite / badge |
| --- | --- | --- | --- | --- |
| H1 [npu-l4](../hw/designs/npu-l4.yaml) | 2 × 2 | BF16 | 59 | C0 / STUB |
| H2 [npu-m256](../hw/designs/npu-m256.yaml) | 16 × 16 | BF16, FP8 | 67 | C0 / STUB |

Run from the exact revision with its locked Python dependencies available. In the commands
below, `python` means that environment's interpreter; set `PYTHONDONTWRITEBYTECODE=1` and
`PYTHONPATH="$PWD/src:$PWD/contract"` when using a clean export. This command reproduces
the design inventory and the no-evidence badge summary; it does not issue model evidence:

```sh
python -B - <<'PY'
from pathlib import Path
import yaml
from uarch_contract.hardware import HardwareSpec, sourced_leaves
from uarch_contract.fidelity import FidelityDetail
from rkuarch.provenance.badge import badge_for
for name in ('npu-l4', 'npu-m256'):
    h = HardwareSpec.model_validate(yaml.safe_load(Path(f'hw/designs/{name}.yaml').read_text()))
    leaves = tuple(v for _, v in sourced_leaves(h))
    f = FidelityDetail(compute=0, noc=0, dram=0, sync='exact', layer_reuse=True)
    print(name, h.design_status, 'stipulations', sum(v.kind == 'stipulation' for v in leaves),
          'grid', h.cores.grid.rows.value, h.cores.grid.cols.value, 'formats', list(h.formats),
          'composite', f.conservative_composite(),
          'badge', badge_for(leaves, (), design_status=h.design_status).badge)
PY
```

TPU v5e and Blackhole p100a remain draft reference fixtures under
[hardware-review](../tests/fixtures/u2_b/hardware-review/), outside active hardware
references. Their unknowns and stand-ins do not authorize physical execution, performance
reporting or L3 use. No complete physical HardwareSpec or measured evidence is inferred
from these drafts. The [sourcing inventory](../hw/U2-sourcing-inventory.md) records the
restriction; its old v2 lifecycle paragraph is historical, superseded for currentness by
the v3 identities below.

Preparation resolves operator counts, tensor-parallel shard, KV reads and writes,
precision and selected-rank work. A row covers one chip's shard, one iteration and all
model layers, excluding inter-chip collectives. Decode generates one token per active
sequence; prefill processes its stated prompt count and length. KV reads use valid tokens,
while allocation uses page capacity. Fused attention does not spill its score matrix;
MoE is active-parameter dense-equivalent, with routing and communication omitted.
These conventions and H2 FP8 preparation are pinned by
[shape/count tests](../tests/unit/test_u2_a_shapes.py). Saved prepared input is authoritative:
replay does not silently rebuild mapping or reshard work
([prepared-input tests](../tests/unit/test_u2_a_prepared.py),
[unmodified public import test](../tests/integration/test_u2_a_stage2_cli.py)).

The [analytic engine](../src/rkuarch/engines/analytic/core.py) adds matrix and vector
compute times for each operator, compares that sum with its read-plus-write memory time,
and takes the larger. Per-operator mode sums those maxima. Aggregate U-C0 takes the
maximum of the summed compute times and summed memory times. The result verifier binds
U-C0 to that arithmetic and checks attribution conservation
([literal analytic tests](../tests/unit/test_u2_a_analytic.py),
[aggregate and per-op regressions](../tests/unit/test_u2_a_stage2_result.py)).

Composite **C0** describes model detail: compute, NoC and DRAM are at level zero, with
exact sync in the declared vector and shared SRAM absent in these designs. It does not
mean calibrated accuracy. Detailed queues, cache history, inter-chip communication,
compiler scheduling, energy and measured efficiency are unrepresented. The engine refuses
higher-detail requests; [fidelity rules](../contract/uarch_contract/fidelity.py) and the
[analytic refusal test](../tests/unit/test_u2_a_analytic.py) pin this boundary;
`test_zero_hardware_detail_is_c0` in the [contract tests](../contract/tests/test_u_p1.py)
pins the composite.

`capture` saves authenticated jobs/results. `companions draft` writes a STUB card and
UNREVIEWED recipes. `companions assemble` needs actual independent accepted reviews of
the exact final recipes and family registry; missing, rejected or mismatched subjects
refuse. Every supplied comparison attempt must survive intake, including failures.
Assembly cannot authenticate an attempt withheld from every supplied input; completeness
also needs external review. See the [assembly tests](../tests/unit/test_u2_b_companions.py),
particularly `test_external_review_is_required` and
`test_re_reviewed_subset_cannot_erase_supplied_capacity_failure`.

`table` binds hardware, prepared work, assumptions, results and report context into an
offline package. Keep its adjacent artifacts directory with it. Canonical identities and
condition ordering preserve repeat/replay bytes
([H1 condition-order regression](../tests/integration/test_u2_a_condition_order.py)); saved
capture replay can disable all producers
([offline capture test](../tests/unit/test_u2_a_companions.py)). U2 supports analytic execution
with `workers=1`, as scoped in the [public workflow](u2-workflow.md). There is no interpolation
or outside-grid extrapolation, and experimental errors have no samples
([table/replay tests](../tests/integration/test_u2_a_replay.py),
[public companion CLI tests](../tests/integration/test_u2_a_companions_cli.py)).

## What the report says about trust

Structural validity, content identity, source applicability and performance validation
are separate checks. Hashes identify content; an accepted declaration review supplies no
measurement. Full contributor closure includes actual, reference and adjustment inputs;
rehashing or re-reviewing a recipe cannot excuse missing original inputs
([reference contributor regressions](../tests/unit/test_u2_b_stage2_reference.py)).

Default HTML and Markdown show readable identities and `conditional · N stipulations`
while hiding unvalidated predictions. Explicit `--show-unvalidated-predictions` displays
eligible finite executed predictions with **STUB**, **error unknown** and their conditions.
It does not promote a badge. All numeric surfaces share the permission boundary
([display tests](../tests/unit/test_u2_b_display_permissions.py),
[stipulation/identity regressions](../tests/unit/test_u2_b_stage2_display.py),
[report surface tests](../tests/unit/test_u2_b_report_surfaces.py)).

[U0004](decisions/U0004-stipulated-values-and-the-estimated-ceiling.md) caps a proposed
design at estimated even if future eligible evidence exists. Current predictions remain
STUB: L0–L2 verification does not establish performance validation. Real measurement/history eligibility and nonempty energy verification remain
unsupported. This analytic model consumes no energy families: energy is **unverified**,
not zero. Unknown error bands stay null; deterministic output creates no confidence
interval. Positive card claims refuse at build, memory, disk and CLI boundaries
([model-card tests](../tests/unit/test_u2_b_stage2_cards.py)). Characterization's human
output labels counts and hides timing columns; raw JSON retains estimates
([characterization regression](../tests/unit/test_u2_b_stage2_characterize.py)).

## A reproducible analytic row

This is an explicitly opted-in **STUB prediction, error unknown, energy unverified**,
conditional on H1's **59 stipulations**. Scope: Llama-3.1-8B, BF16 compute/KV, tp=1,
steady stateless analytic `per_op`, nominal frequency, one chip, all layers, no collectives.
It is computed work, not a physical duration measurement.

| Phase | Batch | Context per sequence | Duration (s), STUB / unknown error | U-C0 (s), STUB / unknown error |
| --- | --- | --- | --- | --- |
| decode | 1 | 128 | 0.015038327296 | 0.015038327296 |

The containing table hash is
`sha256:d55dfc66a0d33aff209a82353eba7e5316db20eb8cb51d56c9d6ab75124ba6be`.
The canonical content hash of this complete row is
`sha256:e2f0c393c09b90c0a3ff7761d7b2e6b529a493b4830032a8562138d860843467`
(a computed row digest, not an additional schema field).

The adjacent command reproduces that row and the eight-point public demonstration from
published inputs, with outputs in a new temporary directory. It replays the committed
prepare/capture/draft commands and reconstructs the exact administrative singleton registry.
All input byte hashes must match the [capture receipt](reviews/U2-public-demo-v1/capture-receipt.json)
before the preserved driver consumes the [actual independent AI reviews](reviews/U2-public-demo-v1/external-review/review.md).
The driver checks review-file hashes, accepted/independent decisions and exact
`review_subject_hash` bindings before assembly. This session issues no new approvals.
Any changed subject requires a new independent review; do not bypass the assertions.
The singleton establishes no relationship to measured hardware.

The [historical driver](reviews/U2-public-demo-v1/completion/run-demo.py.txt) originally
requires ignored local inputs and an old source-tree export; invoking it unchanged is
not a fresh-clone recipe. This command replaces only its path/export setup and freshly
reconstructs those inputs. It retains its review, report, repeat and producer-trap checks.
Two fresh runs and saved replay reproduce 61 files and 36,707,563 bytes per run.
Default reports hide all 1,992 declared prediction paths; explicit opt-in shows them with
STUB/error labels. These are metric paths across eight points, not workload configurations.
Its empty comparison intake is valid only for this standalone demonstration, not the matrix.

```sh
python -B - <<'PY'
# Run from a clean export/clone of 7fee0a8 with the locked dependencies available.
import hashlib, json, os, subprocess, sys, tempfile
from pathlib import Path
repo = Path.cwd()
r = repo / 'docs/reviews/U2-public-demo-v1'
work = Path(tempfile.mkdtemp(prefix='u2-doc-demo-'))
d = work / 'inputs'
d.mkdir()
e = work / 'receipts'
e.mkdir()
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
os.environ['PYTHONPATH'] = f'{repo}/src:{repo}/contract'
os.environ.pop('MYPYPATH', None)
sys.path[:0] = [str(repo / 'src'), str(repo / 'contract')]
import rkuarch.cli, uarch_contract
assert Path(rkuarch.cli.__file__).is_relative_to(repo)
assert Path(uarch_contract.__file__).is_relative_to(repo)
old_root = '/home/jjaff/AI-infra-simulation/rk-uarch-u2-integration'
commands = []
for row in json.loads((r / 'commands.json').read_text()):
    argv = [sys.executable] + [a.replace(old_root + '/tables/U2-public-demo-v1', str(d))
        .replace(old_root + '/docs/reviews/U2-public-demo-v1', str(r))
        for a in row['argv'][1:]]
    p = subprocess.run(argv, capture_output=True, text=True)
    commands.append({'argv': argv, 'exit_code': p.returncode, 'output': p.stdout + p.stderr})
    (e / 'fresh-input-commands.json').write_text(json.dumps(commands, indent=2) + '\n')
    assert p.returncode == 0, commands[-1]
# Reconstruct the exact reviewed administrative singleton, not a new family claim.
registry = {'entries': [{'family': 'u2-h1-npu-l4-only',
    'hardware_spec_hash': 'sha256:3b7186f3e69d38723ec40f9a074b941934644ac57cc6f61d64865429caac07d9'}],
    'format': 'uarch-family-registry/1',
    'registry_hash': 'sha256:c8e33266930c4548767c25c66586e20e7a062fbb2cc25545624fd5e5a01aec7b',
    'review_hash': 'sha256:' + '0' * 64, 'version': 'u2-public-demo-v1-singleton-proposal'}
(d / 'draft/registry.json').write_text(json.dumps(registry, sort_keys=True, separators=(',', ':')) + '\n')
actual = {p.relative_to(d).as_posix(): {'sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
    'bytes': p.stat().st_size} for p in d.rglob('*') if p.is_file()}
assert actual == json.loads((r / 'capture-receipt.json').read_text())['files'], 'Changed subjects: do not reuse reviews'
# Retarget only the historical driver's path/export setup; retain its review hash,
# subject, byte-equality, display-permission and disabled-producer assertions.
source = (r / 'completion/run-demo.py.txt').read_text()
start = source.index('I = Path(')
end = source.index('from uarch_contract.evidence import ReviewRecord')
setup = f'''I = Path({str(repo)!r})
R = I / 'docs/reviews/U2-public-demo-v1'
E = Path({str(e)!r})
D = Path({str(d)!r})
O = Path({str(work / 'outputs')!r})
T = '7fee0a8ed0c5d7bbb20b65c1cf68672470a5ac60'
S = I
PY = Path({sys.executable!r})
assert not O.exists()
O.mkdir()
sys.path[:0] = [str(S / 'src'), str(S / 'contract')]
'''
driver = work / 'run-demo.py'
driver.write_text(source[:start] + setup + source[end:])
subprocess.run([sys.executable, '-B', str(driver)], check=True)
from rkuarch.table.artifacts import load_verified_report_inputs
from uarch_contract.hashing import content_hash
v = load_verified_report_inputs(work / 'outputs/fresh-a/table/table.json')
row = v.table.rows[0]
print('ROW', json.dumps(row.model_dump(mode='json'), sort_keys=True))
print('ROW_CONTENT_HASH', content_hash(row))
print('OUTPUT_ROOT', work)
PY
```

The printed `OUTPUT_ROOT` contains local generated files, not committed repository files.
Fresh input generation, assembly and reporting are pinned by the
[CLI workflow regressions](../tests/integration/test_u2_a_companions_cli.py); the actual
reviews above apply only to these byte-identical subjects. The broader matrix uses
explicitly synthetic administrative packaging reviews, which do not become independent
approvals through a passing software test.

## Why rk-sim also estimates runtime

rk-uarch estimates the resolved physical operator graph on one chip. rk-sim has a separate
coarse aggregate iteration-cost model. Pinned outputs of that model provide compatibility
evidence; production rk-uarch neither imports rk-sim nor tunes physical work to its conventions.
Accepted [U0003 direction S](decisions/U0003-one-chip-one-set-of-facts.md) separates physical
correctness/replay and discrepancy recording from isolated test-only nominal compatibility
([nominal tests](../contract/tests/test_u2_nominal_candidate.py),
[physical discrepancy test](../contract/tests/test_u2_physical_discrepancies.py)).

The completed published-revision run records **1,008 nominal compatibility cases** separately
from **96 executed physical discrepancies, 48 capacity failures and 864 not-run cases**.
The nominal gate is `compatibility_pass`; physical duration accuracy is `not_assessed`.
Four existing upstream precision-refusal observations per track are retained, not newly
generated. This provides no independent physical full-workload duration or silicon validation.
The receipt-reading command in the next section reproduces these counts without rerunning
the matrix.

## Published state and remaining limits

Current adopted **v3** manifest:
`20eee19b0e864ad07a7b122da7544e385116fdd50d279e1fac1bfbbf03a697ad`.
Frozen input manifest:
`08d0e905cc50943d286b9c6dbcfb2cf844c969dda28b9446162d12734870871c`.
Strict current verification passes on the published commit. The earlier v2 support failures
in the [A](reviews/U2-lane-A-review.md) and [B](reviews/U2-lane-B-review.md) reports describe
their reviewed trees; their original verdicts and evidence remain unchanged. Both final
software-response acceptances were scoped to tree
`53f9f21b7cc3f84c0cbdb5f3f1e74e6e4aeca522`, not a new review of this publication commit.

```sh
python -B scripts/vendor_rk.py --check
python -B - <<'PY'
from pathlib import Path
from hashlib import sha256
root = next(Path('contract/vendor').glob('rk-sim@*'))
for rel in ('MANIFEST.json', 'u2-inputs/SHA256SUMS'):
    print(rel, sha256((root / rel).read_bytes()).hexdigest())
PY
```

Coordinator-owned **local receipts**, not files committed at this revision, are under
`/home/jjaff/AI-infra-simulation/rk-uarch-u2-integration/docs/reviews/`:
`U2-main-publication-v1/execution.json` and `U2-published-validation-v1/`.
The latter's `configuration.json` identifies the actual GitHub cold clone, new environment
and cache, reused base interpreter, and temporary generated outputs. Its final verification
reports completed U0021 checks on the exact published commit: **1,394 tests passed, no
failures/errors/skips**, strict current support, report/replay, explicit synthetic-assignment
H2 characterization and the pinned upstream loader round trip (no oracle execution).
The historical B64 ledger is preserved; its later disposition overlay does not convert
all earlier pending cases into passes.

The following reads those receipts; it does not rerun their suite or matrix and requires
access to that local coordinator directory. A published clone alone does not contain these
post-publication receipts. Preserve or publish them separately when reconciling this page.
A missing, running or pending receipt is not a pass.

```sh
python -B - <<'PY'
import json
from pathlib import Path
from xml.etree import ElementTree as ET
base = Path('/home/jjaff/AI-infra-simulation/rk-uarch-u2-integration/docs/reviews')
p = base / 'U2-published-validation-v1'
print('publication', json.loads((base / 'U2-main-publication-v1/execution.json').read_text())['status'])
for name in ('configuration', 'final-verification', 'characterize', 'pinned-loader-result'):
    print(name, json.loads((p / (name + '.json')).read_text()))
print('JUnit', [s.attrib for s in ET.parse(p / 'full-suite.xml').iter('testsuite')])
print('checks', [(c['check'], c['exit_code']) for c in json.loads((p / 'checks.json').read_text())])
r = json.loads((p / 'runtime-progress.json').read_text())
print('runtime', r['status'], r['actual_execution'])
ci = json.loads((p / 'ci-final.json').read_text())
print('CI', ci['headSha'], ci['status'], ci['conclusion'])
for line in (p / 'hosted-ci.log').read_text().splitlines():
    if 'passed in ' in line or ('nothing yet:' in line and 'echo ' not in line):
        print(line)
print('public demo', json.loads((p / 'public-demo/result.json').read_text()))
print('case dispositions', json.loads((p / 'case-dispositions.json').read_text()))
PY
```

Same-commit [hosted CI](https://github.com/kakoee/rk-uarch/actions/runs/38101625804)
is recorded successful. Executed checks include Python lint, both strict type commands,
import checks and tests; strict snapshot verification, contract tests and schema freshness;
and licence tests. **Golden, determinism, native, perf, prediction-ordering and the patch
step were conditional no-ops**, not coverage. Actual U2 repeat/replay evidence came from
the cold clone. The [workflow](../.github/workflows/ci.yml) defines these distinctions.

[U0021](decisions/U0021-u2-cold-clone-validation-exception.md) permits this U2 correctness
validation on ElfinKidsLaptop Ubuntu/WSL2 plus hosted Ubuntu CI on the same published commit.
It does not approve simulator-performance benchmarking on WSL2 or waive U3's Linux
self-hosted runner and later hardware-validation requirements. The execution plan's older
STATUS remains a coordinator reconciliation item. Publication receipts do not authorize a
tag, sprint closure, badge promotion, hardware accuracy claim or deletion of historical evidence.
