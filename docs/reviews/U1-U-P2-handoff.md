# U1 · U-P2 · Lane B — tooling proposal and integration handoff

> **Current publication status — Lane B integration note, 2026-10-06.**
> Both independent lane Stage 3 reviews are ACCEPTED; see [Lane A](U1-lane-A-review.md)
> and [Lane B](U1-lane-B-review.md). A-F12's guard and full-coverage regressions are
> implemented and accepted in the combined proposal; B-F8 is integrated. The replacement
> snapshot has passed real human double-generation and strict validation. Earlier pending
> integration/generation statements below are historical and superseded, not rewritten.
> U0001/U0002 remain proposed; the strict stub-source exception still needs whole-ADR
> acceptance. Snapshot adoption/publication, hosted CI, Linux-box cold-clone validation
> and G1/U1 remain pending. Embedding accounting and B-F16 retain their U2 scope.
> Use [the final publication handoff](U1-publication-handoff.md) for exact files and gates.

> **Stage 2 supersedes the earlier readiness and generation/adoption instructions below.**
> See [the Stage 2 response](U1-lane-B-response.md) and the final section of this handoff.
> Both existing snapshots are historically intact but incompatible with the revised
> generator: its full fingerprint changed and required oracle-environment metadata is
> absent. Neither is eligible for adoption under the newly approved strict policy.
> U0002 remains proposed. A's revised carrier is integrated and tested; review and
> the embedding-accounting decision remains pending. A-F12
> interim projection refusal is approved and implemented; see the latest section below. Accepted U0019 governs preparation ownership.

Prepared for **Javid (@jjaffari), acting owner and human approver for both U1 lanes**,
2026-10-04. All changes are local and uncommitted. Reza's approval is not claimed.
Javid has now run the documented vendor operation twice successfully; he reported that
its second run confirmed byte-identical output. The generated snapshot is present locally
and remains uncommitted. The agent inspected it read-only and did not regenerate or edit
vendor files. A final candidate has also been generated and verified, but not adopted;
see the 2026-10-06 lifecycle and adoption section below. U0002 remains **proposed**.
U1 and G1 are not complete.

## Workspace and baseline

- Worktree: `/home/jjaff/AI-infra-simulation/rk-uarch-u1-b`, branch `u1/parity`.
- The supplied initial cwd was the separate `rk-uarch` worktree on `main`; it was
  inspected, not edited. Lane B was clean before implementation.
- Actual Lane B HEAD: `af3b1bc3df3171d196394a58f62202ad50845dfa`, one documentation-only
  commit after requested baseline `fa16aeb`. `fa16aeb` is an ancestor. The additional
  commit records Javid's pin update; it was preserved rather than reset or hidden.
- Read-only upstream: `../rk-sim-u1-pin`, clean at
  `1e5706e0ebfcc67c1a7333079a35b75f693e9963`. No rk-sim files were edited.
- Required context read: CLAUDE, execution-plan STATUS/U1/G1, how-it-works, U0 handoff,
  implementation template, U-P2 and required context, U-P1; pinned schema sources,
  compute implementation, component adapter/loader, and Makefile. U0001 was absent
  when work began, as the execution plan permits.
- Sandbox execution was unavailable because of the `/mnt/wslg/distro` mount error.
  Commands ran with explicit escalation; writes stayed in Lane B or test temp paths.

## Deliverables

- `scripts/vendor_rk.py` and only Lane B's `vendor-rk` Makefile target.
- Acceptance tests and reusable test-only parity/path-loading helpers in `contract/tests/`.
- Three source-attributed JSON sidecars in `contract/fixtures/model_shapes/`.
- Proposed [ADR U0002](../decisions/U0002-the-vendored-snapshot-and-parity-discipline.md).
- Contract CI requiring committed snapshot evidence, strict integration checks, and
  Lane A's existing read-only schema-freshness interface.
- Import boundaries, generated-source lint/type exclusions, test import configuration.
- Javid-approved wording reconciled across build-spec and the U-P1/U-P2 prompt copies.

No production contract models, schemas, toy table, `make gen` implementation, or U0001
were replaced or modified by Lane B. Javid generated the snapshot under
`contract/vendor/`; the agent has not edited or regenerated its files.

## Acceptance checklist and evidence

| Acceptance item | Result now | Evidence / remaining requirement |
|---|---|---|
| Tests written first | Done | Initial tooling/harness tests failed collection on missing modules; loader tests failed before its implementation; approved precision/map/environment/deviation regressions failed before fixes. |
| Tamper names stale file | Pass, synthetic test | A byte change in temporary schema.json fails naming schema.json. Missing/extra files, symlinks and path traversal also fail. |
| Clean exact pin and U0001 mismatch refusal | Pass, tooling tests | Wrong HEAD, dirty checkout and mismatched eventual U0001 rejected. Missing U0001 remains allowed during preparation. |
| SourcedValue claim round trip and stipulation refusal | Pass in isolated A+B integration | Both tests pass with A models and the existing snapshot. Blank stub sources are a separately tested **proposed exception**, not exact validator parity. |
| ModelSpec / PrecisionFormat identity; exact Channel mapping | Pass in isolated A+B integration | Both tests pass with A models, toy table and the actual vendored classes. |
| Parity harness self-test and ×1.1 mutant | Pass, synthetic self-test | Failure includes fixture id, actual and expected values; null, nonfinite, signed-deviation and unknown-fixture guards pass. This is **not workload parity**. |
| Real fixture echo/mutant tests | Pass, coordinator-reported harness self-test | Runs against the human-generated oracle fixtures. This verifies the harness, **not real workload parity**. |
| Full oracle bridge matrix | Pass, synthetic dispatch self-test | Fake APIs return sentinel numbers across 864 required cases, plus 288 for a custom PARAMS file. Verifies returned numbers are preserved and both negative exception paths are demanded. |
| Actual iteration_cost counts and durations | Generated by Javid | Human operation executed the actual pinned rk-sim methods. Read-only inspection verified 864 records and their explicit count/duration scopes; agent did not rerun the oracle. |
| Placeholder UnsupportedPrecision from rk-sim | Generated; evidence verified | Both actual BF16 and FP8 refusal records are present. The validator passes; the coordinator reported the snapshot refusal test passed. No duration was synthesized for these refusals. |
| ModelShape sidecars pass A check_parity | Pass in isolated A+B integration | All three sourced sidecars pass A's actual checker in the integration copy; B's branch itself still lacks A's models. |
| Two real make vendor-rk runs byte-identical | Complete, Javid-reported | Javid ran the documented command twice; the second run confirmed byte-identical output. Agent has not regenerated the snapshot. |
| Full fixture matrix, tp, params, durations, six decode points | Pass on generated artifacts | Agent reran read-only manifest/matrix verification: 864 records, all required groups and decode points. Coordinator reported the snapshot matrix/provenance test passed. |
| Production import boundaries | Pass | import-linter: 2 contracts kept, 0 broken. `rk`, `contract` and vendor namespace are forbidden to production roots. |
| CI uses only committed snapshot | Wired; integration checks pass locally | No upstream checkout or credentials in CI. Snapshot remains uncommitted. Strict suite passes with no skips in the isolated integration copy; this is not a remote CI run. |
| Schema freshness | Pass in isolated A+B integration | A's `uarch_contract.generate --check` passes, sharing the implementation used by A's freshness test and `make gen-check`. |

Historical validation before human generation (retained to distinguish preparation evidence):

```text
uv run pytest -q -rs                30 passed, 8 skipped
uv run mypy src contract           no issues in 36 source files
uv run mypy scripts                no issues in 2 source files
uv run ruff check .                all checks passed
uv run lint-imports                2 kept, 0 broken
uv run python scripts/vendor_rk.py --check
    expected failure: missing .../rk-sim@<pin>/MANIFEST.json;
    human vendor operation required
```

Those eight skips described the pre-generation state, not the current state.
`test_prompt_sync.py` was included and passed. No native files changed, so native
tests do not apply.

### Evidence after human generation

- **Javid-reported:** the documented vendor operation succeeded twice, and its
  second run confirmed byte-identical output. This completes the human generation
  and real regeneration-determinism acceptance items.
- **Coordinator-reported independent test run:** **33 passed, 5 skipped**. The three
  newly passing tests check snapshot matrix/provenance, fixture echo/mutant harness
  behavior, and recorded placeholder refusals. The five remaining skips require
  Lane A: claim round trip, stipulation refusal, ModelSpec/PrecisionFormat identity,
  exact Row-to-Channel mapping, and ModelShape check_parity. No skip is a pass.
- **Agent read-only follow-up:** `uv run python -B scripts/vendor_rk.py --check`
  passes. Inspection found **19 files, all mode 0444**, **864 records** (432 decode,
  432 prefill), three models, tp={1,8}, and 144 records in each of the six
  component/precision groups. Both placeholder refusal records are present, and
  every decode memory_write_bytes is null.
- Vendored source modules, generated schema bundle and both component YAMLs are
  byte-identical to the pinned checkout. All three snapshot sidecars match the
  proposed source-attributed sidecars. These are file-identity checks, not A's
  semantic ModelShape checks.
- Inspected `MANIFEST.json` SHA256:
  `4caea65f3c217bbb2030409833be6c67c15561552f8d9c9e179ac3ff82883284`.
  The pinned rk-sim checkout was independently rechecked and remains clean at
  `1e5706e0ebfcc67c1a7333079a35b75f693e9963`.

At that stage the agent deferred strict round-trip and ModelShape checks pending
integration. The later isolated A+B results below supersede that pending status.
Passing oracle-fixture echo tests remains a **harness self-test, not real workload
parity**. Human generation or green tests do not accept the ADR or complete G1.

## Human command record and inspected outputs

The documented commands below are retained as the reproducibility record of the
operation Javid reported completing. They are **not a request to regenerate now**
and were not executed by the agent. The rk-sim checkout must remain clean at the
exact pin.

Provision rk-sim's locked dependencies in an external environment; the vendor tool
will refuse an absent environment rather than create one inside rk-sim:

```bash
cd /home/jjaff/AI-infra-simulation/rk-uarch-u1-b
UV_PROJECT_ENVIRONMENT=/tmp/rk-sim-u1-jjaffari-1e5706e \
  uv sync --locked --project ../rk-sim-u1-pin
```

The documented human operation, run twice unchanged by Javid:

```bash
UARCH_HUMAN=1 UV_PROJECT_ENVIRONMENT=/tmp/rk-sim-u1-jjaffari-1e5706e \
  make vendor-rk SHA=1e5706e0ebfcc67c1a7333079a35b75f693e9963 RK=../rk-sim-u1-pin
UARCH_HUMAN=1 UV_PROJECT_ENVIRONMENT=/tmp/rk-sim-u1-jjaffari-1e5706e \
  make vendor-rk SHA=1e5706e0ebfcc67c1a7333079a35b75f693e9963 RK=../rk-sim-u1-pin
```

Optional additional inputs: append `PARAMS='/absolute/first.yaml /absolute/second.yaml'`
to both commands. For paths containing spaces, quote each path inside PARAMS, e.g.
`PARAMS='"/absolute/my chip.yaml"'`. Basenames must be unique unless bytes are identical;
a collision with different bytes is rejected. Extra components add 288 records each.

Inspected generated destination:
`contract/vendor/rk-sim@1e5706e0ebfcc67c1a7333079a35b75f693e9963/`.
Observed **19 files**, all mode 0444:

- `schema.json`: unchanged `web/src/schema.json` from the pinned checkout.
- `rk/provenance.py`, and `rk/schema/{fidelity,channels,execution,workloads,agentic,hashing,traces,versions}.py`.
- `components/asic_placeholder.yaml`, `components/nvidia_h100_sxm.yaml`, unchanged.
- `model_shapes/{llama-3.1-8b,llama-3.1-70b,mixtral-8x7b}.json`, retaining sources.
- `parity/fixtures.json`: **864 records**, each with compute/KV precision, tp,
  query, replica counts, component filename/digest, and actual rk-sim duration.
- `parity/refusals.json`: **two** actual placeholder UnsupportedPrecision records,
  for BF16/BF16 and FP8/FP8; no invented duration.
- `GENERATOR.json`: pin, source fingerprints and scope labels; no timestamp.
- `MANIFEST.json`: pin and SHA256 digest of every other file.

The documented success message is `vendored 19 files to ...; rerun is byte-checked`.
Javid reported successful completion of both runs and the second run's byte comparison.
That second operation recomputed the oracle and checked it against the first;
the agent's current inspection did not regenerate either output. The synthetic
rerun test is separate evidence.

The following checks are the integration recipe. They have now passed in the
isolated copy described below; apply the fix to the coordinator's combined tree
before using the same checks there:

```bash
uv run python scripts/vendor_rk.py --check
uv run pytest -q -rs contract/tests --require-vendor
uv run python -m uarch_contract.generate --check
uv run pytest -q
uv run mypy src contract
uv run ruff check .
uv run lint-imports
git -C ../rk-sim-u1-pin status --short
```

The strict suite and schema command require integrated Lane A. Expected upstream
status output is empty. If generated output differs or any check fails, stop and
report it; do not hand-edit snapshot files or widen tolerances. These verification
commands perform no commit, merge, push or tag. The separately approved human
adoption/publication process is described in the lifecycle section below.

## Decisions for Javid and Lane A coordination

Already approved by Javid in this session:

1. Preserve Row.counts keys and use the exact name-only four-entry Channel mapping.
2. Use the two common precision configurations, add H100 BF16/BF16 and FP8/FP8, and
   assert the placeholder's actual unsupported-precision exception.

U0002 records those instructions and remains a complete uncommitted implementation
proposal for Javid's review. Additional reviewable implementation choices are the
unchanged-source dependency closure, explicit replica-to-rank harness projection,
signed per-fixture/channel deviations, immutable rerun behavior, and sourced model
fixtures with rounded nominal parameter counts. No claim is made that Javid accepted
those remaining choices merely by approving the two questions.

**Exact text for Lane A to record in U0001** (B has not edited A's ADR):

> Javid (@jjaffari), acting human approver for both U1 lanes, approved preserving
> Row.counts fields matrix_ops, vector_ops, memory_read_bytes and memory_write_bytes.
> Their diagnostic Channel mapping is exactly matrix_ops → matrix_ops,
> vector_ops → vector_ops, memory_read_bytes → memory_read, and
> memory_write_bytes → memory_write. This is only a naming translation: no scaling,
> tp division or null-to-zero conversion. Every field must have exactly one mapping;
> destinations must be unique and valid vendored Channel literals. Unknown fields
> fail. U0002 references this decision. No later rk-sim integration is implemented in U1.

Lane A's draft was inspected read-only once available. Its schema API is
`python -m uarch_contract.generate --check`; B's CI now calls that exact interface.
A's Makefile `gen`/`gen-check` additions must be preserved when combining B's
`vendor-rk` target. A's table API uses `Counts`, `UarchCostTable`, and typed decode/
prefill rows; B validates the toy table through UarchCostTable before examining counts.
No cross-session message delivery or A acknowledgement is claimed; this shared
handoff and the updated U-P1 text are the coordination artifacts.

## Integration fix and validation

The coordinator combined A+B in `/tmp/u1-integration-yhia1lfl` and reported:
strict contract **97 passed, 1 failed, no skips**; full **101 passed, 1 failed**.
The failure was B's `test_eventual_u0001_uses_same_pin`: the checker incorrectly
classified A's rk-uarch baseline/history hashes as upstream pins.

Read A's actual U0001 in `../rk-uarch-u1-a` without modifying it. The fix recognizes
its dedicated reference line: `**Reference:** rk-sim` followed by a full SHA in
Markdown code quotes. An existing ADR must have exactly one such reference, with
one unambiguous full pin. Other repository/history hashes are ignored. A wrong
upstream reference fails even if the required pin occurs elsewhere. Missing,
malformed, duplicate (including identical duplicates), or conflicting reference
lines fail. An absent U0001 still permits preparation. Eleven focused pin and
fingerprint tests pass; the previous checker failed the new positive-history and
missing/ambiguous-reference regressions before implementation.

The vendored carrier regression documents A's proposed narrow exception: rk-sim
accepts empty/whitespace source strings on a stub unchanged, while uarch requires
source=None. Three cases (empty, space, tab/newline) prove actual upstream acceptance,
uarch refusal, and mutual acceptance of None. This is **proposed**, not accepted
validator equivalence or an instruction to normalize blanks.

Only these three files need overlaying onto the coordinator's original integration
copy for the code/test fix:

- `scripts/vendor_rk.py`
- `contract/tests/test_vendor_tooling.py`
- `contract/tests/test_vendored_round_trip.py`

Also carry this updated handoff and U0002 proposal. No A model or ADR was changed.
For validation, created a fresh copy `/tmp/u1-b-pinfix-zu3b9bg9` of the coordinator's
tree and overlaid those three files. The coordinator's original tree was not modified.
Using B's existing environment, with `PYTHONPATH=src:contract:.` and `uv run --no-sync`:

```text
pytest -q contract/tests --require-vendor   111 passed, no skips
pytest -q                                 115 passed, no skips
python -B scripts/vendor_rk.py --check     manifest and matrix verified
python -B -m uarch_contract.generate --check   schemas fresh
mypy src contract scripts                 no issues in 42 source files
ruff check .                              all checks passed
lint-imports                              2 kept, 0 broken
```

These checks include the actual A ModelShape, round-trip and Channel-mapping tests.
Lane B by itself remains a preparation branch without A's models: its current suite
reports **43 passed, 8 skipped**, including the three new carrier cases among the
A-dependent skips; mypy (38 files), ruff and import-linter pass. Those skips are not
counted as successes. No actual workload callable has been implemented or validated.

## Generator fingerprint and staging recipe

The human-generated snapshot and the evidence of Javid's two byte-identical runs
are preserved. `GENERATOR.json` records the script that actually generated it:

- Original script SHA256: `e13b497b1c025cc67d9a5adf5361d2a7ec939d67e54e5aa3822a18f073a15ee8`.
- Fixed script SHA256: `69a3e31f5db3b99bcf251f63ee87eb4dc84ddf4f99fccf9aa48c56843ad186bd`.
- Unchanged oracle program SHA256: `9dd67d4883206f14b8a5a00fa3d0ced95bddaa395ba634d80e08a39813ea04fb`.

The fix changes pin admission, not oracle arithmetic or the oracle subprocess.
The existing artifact's historical fingerprint is correct and must not be rewritten
to pretend the fixed script generated it. Manifest verification still passes.
Regeneration is not needed merely to validate these existing artifacts. If Javid
wants evidence generated by the fixed script, regenerating at the occupied original
destination would be refused because GENERATOR.json and MANIFEST.json would differ.
A new synthetic regression confirms fingerprint-only changes cannot overwrite an
existing snapshot.

**Human-only staging template; not run by the agent.** The final candidate has
already been generated, as recorded below; no rerun is requested now. For future
candidates, generate separately while preserving the existing directory. Start from
the exact reviewed combined tree, generator, sidecars and inputs:

```bash
candidate=$(mktemp -d /tmp/u1-vendor-pinfix-review.XXXXXX)
python3 - "$candidate" <<'PY_STAGE'
import shutil
import sys
from pathlib import Path
shutil.copytree(Path.cwd(), Path(sys.argv[1]), dirs_exist_ok=True, symlinks=True,
    ignore=shutil.ignore_patterns('.git', '.venv', '__pycache__', '.pytest_cache',
        '.mypy_cache', '.ruff_cache', '.import_linter_cache',
        'rk-sim@1e5706e0ebfcc67c1a7333079a35b75f693e9963'))
PY_STAGE
UARCH_HUMAN=1 UV_PROJECT_ENVIRONMENT=/tmp/rk-sim-u1-jjaffari-1e5706e \
  make -C "$candidate" vendor-rk SHA=1e5706e0ebfcc67c1a7333079a35b75f693e9963 \
  RK=/home/jjaff/AI-infra-simulation/rk-sim-u1-pin
UARCH_HUMAN=1 UV_PROJECT_ENVIRONMENT=/tmp/rk-sim-u1-jjaffari-1e5706e \
  make -C "$candidate" vendor-rk SHA=1e5706e0ebfcc67c1a7333079a35b75f693e9963 \
  RK=/home/jjaff/AI-infra-simulation/rk-sim-u1-pin
```

Use the already-provisioned external rk-sim environment; if it is unavailable,
Javid must provision it using the earlier locked-environment command first.
Expected candidate: 19 files, 864 oracle records, two refusal records, and two
successful byte-identical runs of the fixed script. Compare before any adoption:

```bash
uv run python -B - "$candidate" <<'PY_COMPARE'
import json
import sys
from pathlib import Path
from scripts.vendor_rk import PIN, check_manifest, digest
old = Path('contract/vendor') / f'rk-sim@{PIN}'
new = Path(sys.argv[1]) / 'contract/vendor' / f'rk-sim@{PIN}'
check_manifest(old)
check_manifest(new)
a = {p.relative_to(old): p.read_bytes() for p in old.rglob('*') if p.is_file()}
b = {p.relative_to(new): p.read_bytes() for p in new.rglob('*') if p.is_file()}
assert a.keys() == b.keys()
changed = {p.as_posix() for p in a if a[p] != b[p]}
assert changed == {'GENERATOR.json', 'MANIFEST.json'}, changed
before = json.loads(a[Path('GENERATOR.json')])
after = json.loads(b[Path('GENERATOR.json')])
assert after.pop('script_sha256') == digest(
    (Path(sys.argv[1]) / 'scripts/vendor_rk.py').read_bytes())
before.pop('script_sha256')
assert before == after
print('Only generator script fingerprint and covering manifest changed; original preserved.')
PY_COMPARE
```

This comparison is specific to the metadata-only pin-checker candidate: oracle
counts, durations, refusals, sources and sidecars must remain byte-identical. General
reviewed refreshes, including U2 PARAMS additions, use the classified comparison and
explicit review lifecycle below. Keep original and candidate intact until adoption
is separately approved. Generation/comparison alone performs no adoption or commit.

## Final candidate evidence and reviewed-refresh lifecycle (2026-10-06)

Javid required a reviewed-refresh lifecycle before final acceptance. U0002 now
specifies it while remaining **proposed**. This follow-up changes only U0002 and
this handoff. The generator, its refusal behavior, its fingerprint, both snapshots,
and A's worktree are unchanged.

### Completed candidate generation; adoption pending

| Evidence | Recorded result |
|---|---|
| Candidate tree | `/tmp/u1-vendor-final-f96kn1fp` |
| Human execution | Javid reported two successful identical runs; agent did not rerun generation. |
| Prior manifest SHA256 | `4caea65f3c217bbb2030409833be6c67c15561552f8d9c9e179ac3ff82883284` |
| Candidate manifest SHA256 | `6b0d69c5737ba2b4cdbd8bce13ec860e4750f4008d9f4ee4fb8dc6db456d8304` |
| Comparison | Coordinator reported, and agent independently verified read-only, that only GENERATOR.json and MANIFEST.json differ. |
| Numerical evidence | All 864 oracle records and both refusal records are byte-identical; no additions, removals or value changes. |
| Validation | Both manifests and required coverage pass; candidate has 19 files, all mode 0444, 432 decode and 432 prefill records. |
| Generator identity | Candidate and Lane B script both hash to `69a3e31f5db3b99bcf251f63ee87eb4dc84ddf4f99fccf9aa48c56843ad186bd`; oracle-program fingerprint unchanged. |
| Adoption/publication | **Not adopted.** Both original locations preserved. Both snapshots remain uncommitted. |

Source/module bytes, component inputs and source-attributed sidecars are unchanged.
The upstream checkout remains clean at the exact U1 pin. Current file inspection
verifies the candidate contents, not the historical act of running twice; the latter
is attributed to Javid. The reason for this candidate is the reviewed pin-checker
fix's generator provenance, not a change in oracle arithmetic or results.

### Lifecycle to apply before any adoption

1. Freeze the exact reviewed generator/supporting code, upstream pin, sidecars,
   complete PARAMS input set, and locked environment. Generate in a separate tree.
2. A human generates twice from those same inputs and verifies byte identity.
3. Verify manifest, full file inventory, required coverage/refusals and source
   attribution; run applicable integrated checks and verify the optional PARAMS
   inventory against the human's intended set.
4. Compare metadata, upstream sources/schema, component inputs/sidecars, fixture
   additions/removals and changed existing oracle values separately. Compare by
   semantic query identity as well as file bytes; review renamed identities too.
5. Require explicit human review of changed existing counts, durations, nulls or
   refusal outcomes and their reasons. Unexplained differences block adoption.
   No hand editing generated files, dropping failures or widening tolerances.
6. After approval, adopt the **whole candidate** as a reviewed artifact revision.
   Record old/new manifest hashes, reason, input identities, evidence, approver and
   approval reference; preserve published predecessors in Git history.
7. CI reads only the committed revision. An ordinary vendor rerun still refuses
   differing output at an occupied path, including metadata-only differences.

For the current U1 candidate this is **first publication**: there is no prior
snapshot in HEAD at this path. Selecting the final candidate does not pretend the
prior uncommitted snapshot was published. Preserve that local predecessor as a
review archive. For a later refresh of a committed artifact, record its existing
publication commit and manifest, require that the working snapshot matches it,
and publish a new commit without rewriting the earlier history. Artifact identity
is upstream SHA + manifest SHA256 + publication commit, not the directory name alone.

### Concrete human staging instructions for a future refresh

The previous separate-tree staging recipe remains applicable. It copies the exact
reviewed tree while excluding its occupied snapshot directory. Do not rerun that
recipe for the completed final U1 candidate merely to carry out adoption.
For U2, use the same recipe with the reviewed U2 generator/supporting tree and its
accepted upstream pin. Copy all retained and new reviewed PARAMS into the staging
tree before the first run; for example, with `candidate` set by that recipe:

```bash
mkdir -p "$candidate/review-inputs"
cp -p -- /absolute/reviewed/prior-design.yaml /absolute/reviewed/new-design.yaml \
  "$candidate/review-inputs/"
params_inputs="\"$candidate/review-inputs/prior-design.yaml\" \"$candidate/review-inputs/new-design.yaml\""
sha256sum "$candidate/scripts/vendor_rk.py" "$candidate"/contract/fixtures/model_shapes/*.json \
  "$candidate"/review-inputs/*.yaml
UARCH_HUMAN=1 UV_PROJECT_ENVIRONMENT=/tmp/rk-sim-u1-jjaffari-1e5706e \
  make -C "$candidate" vendor-rk SHA=1e5706e0ebfcc67c1a7333079a35b75f693e9963 \
  RK=/home/jjaff/AI-infra-simulation/rk-sim-u1-pin PARAMS="$params_inputs"
UARCH_HUMAN=1 UV_PROJECT_ENVIRONMENT=/tmp/rk-sim-u1-jjaffari-1e5706e \
  make -C "$candidate" vendor-rk SHA=1e5706e0ebfcc67c1a7333079a35b75f693e9963 \
  RK=/home/jjaff/AI-infra-simulation/rk-sim-u1-pin PARAMS="$params_inputs"
```

These are templates using already reviewed files, not instructions to fabricate
U2 component values now. Save the input hashes in the review record before generation.
Use an empty PARAMS set when there are no additional components. Retain every earlier
PARAMS file that should remain covered; the generator includes the two required
library components automatically but does not retain unspecified extra components.
Each distinct additional component adds 288 records with the current matrix:
864 + 288×N for N additional components. All retained fixtures must stay identical
unless changed values receive explicit review. A missing earlier component is a
coverage removal requiring review, not permission to silently discard its fixtures.
This permits U2 additions at the same upstream SHA without weakening refusal on
ordinary reruns. No U2 implementation is performed here.

### Concrete comparison before review

From the reviewed combined tree, set `candidate` to the generated candidate tree.
This read-only report is applicable to a general refresh, including added PARAMS.
Unlike the earlier metadata-only pin-fix comparison, it reports numerical changes
for review; it does not authorize any such change. Save its output outside vendor/.

```bash
uv run python -B - "$candidate" > "$candidate/snapshot-review.json" <<'PY_REVIEW'
import json
import sys
from pathlib import Path
from scripts.vendor_rk import PIN, check_manifest, digest, validate_matrix, validate_refusals
old = Path('contract/vendor') / f'rk-sim@{PIN}'
new = Path(sys.argv[1]) / 'contract/vendor' / f'rk-sim@{PIN}'
for root in (old, new):
    check_manifest(root)
    validate_matrix(json.loads((root / 'parity/fixtures.json').read_text()))
    validate_refusals(json.loads((root / 'parity/refusals.json').read_text()))
a = {p.relative_to(old).as_posix(): digest(p.read_bytes()) for p in old.rglob('*') if p.is_file()}
b = {p.relative_to(new).as_posix(): digest(p.read_bytes()) for p in new.rglob('*') if p.is_file()}
changed = sorted(k for k in a.keys() | b.keys() if a.get(k) != b.get(k))

def index(root):
    rows = json.loads((root / 'parity/fixtures.json').read_text())
    def identity(row):
        return json.dumps([row['model_id'], row['precision'], row['tp'],
                           row['component_params_file'], row['query']], sort_keys=True)
    result = {identity(row): row for row in rows}
    assert len(result) == len(rows), 'duplicate semantic fixture identity'
    return result
x, y = index(old), index(new)
value_changes = []
other_changes = []
for key in sorted(x.keys() & y.keys()):
    fields = {k: {'old': x[key].get(k), 'new': y[key].get(k)}
              for k in x[key].keys() | y[key].keys() if x[key].get(k) != y[key].get(k)}
    if fields:
        target = value_changes if {'counts', 'duration_s'} & fields.keys() else other_changes
        target.append({'identity': key, 'changes': fields})
print(json.dumps({
    'old_manifest_sha256': a['MANIFEST.json'], 'new_manifest_sha256': b['MANIFEST.json'],
    'metadata': [k for k in changed if k in ('GENERATOR.json', 'MANIFEST.json')],
    'upstream': [k for k in changed if k == 'schema.json' or k.startswith('rk/')],
    'inputs': [k for k in changed if k.startswith(('components/', 'model_shapes/'))],
    'all_changed_files': changed,
    'added_fixtures': sorted(y.keys() - x.keys()),
    'removed_fixtures': sorted(x.keys() - y.keys()),
    'changed_existing_oracle_values': value_changes,
    'changed_existing_fixture_context': other_changes,
    'refusals': {label: json.loads((root / 'parity/refusals.json').read_text())
                 for label, root in [('old', old), ('new', new)]},
}, indent=2, sort_keys=True))
PY_REVIEW
```

Inspect actual file diffs for every listed metadata/source/input path, not just the
hash change. Review every added/removed identity and context change, including any
rename masking a replacement. Record old/new values and the human's decision for
all changed existing oracle values; tolerances do not grant permission to change a
reference. For the completed U1 candidate the report must show metadata only, no
fixture additions/removals or changed values/context, and identical refusal records.

### Concrete human adoption, only after explicit approval

**Do not execute yet.** Javid has not adopted the final candidate. Before adoption,
record this review record in the handoff/ADR or a linked review document:

| Field | Current final U1 candidate |
|---|---|
| Publication kind | First publication; prior snapshot is uncommitted |
| Prior publication commit | None; for a future refresh record the real prior commit |
| Prior manifest | `4caea65f3c217bbb2030409833be6c67c15561552f8d9c9e179ac3ff82883284` |
| Candidate manifest | `6b0d69c5737ba2b4cdbd8bce13ec860e4750f4008d9f4ee4fb8dc6db456d8304` |
| Reason | Pin-checker fix reflected in generator provenance; oracle values unchanged |
| Review evidence | Read-only comparison above and recorded human double run |
| Adoption approver/date/reference | **Pending Javid's explicit approval** |
| New publication commit | **Pending**, record after human publication |

After that approval, from the target reviewed combined worktree, the following
human-only adoption recipe verifies both approved manifests, copies a complete
candidate, preserves the prior directory outside the worktree, and replaces the
working snapshot. It never patches generated files or invokes the vendor operation.
For a later refresh, substitute the explicitly approved old/new hashes and candidate
path. Pause other worktree consumers during the directory switch.

```bash
uv run python -B - /tmp/u1-vendor-final-f96kn1fp \
  4caea65f3c217bbb2030409833be6c67c15561552f8d9c9e179ac3ff82883284 \
  6b0d69c5737ba2b4cdbd8bce13ec860e4750f4008d9f4ee4fb8dc6db456d8304 <<'PY_ADOPT'
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from scripts.vendor_rk import PIN, ROOT, check_manifest, check_generator, digest
source = Path(sys.argv[1]) / 'contract/vendor' / f'rk-sim@{PIN}'
destination = ROOT / 'contract/vendor' / f'rk-sim@{PIN}'
relative = destination.relative_to(ROOT).as_posix()
for root, expected in ((destination, sys.argv[2]), (source, sys.argv[3])):
    check_manifest(root)
    assert digest((root / 'MANIFEST.json').read_bytes()) == expected
published = subprocess.check_output(['git', 'ls-tree', '-r', 'HEAD', '--', relative], cwd=ROOT)
if published:
    # A refresh starts from the actual committed revision, not local unreviewed edits.
    subprocess.run(['git', 'diff', '--exit-code', 'HEAD', '--', relative], cwd=ROOT, check=True)
    assert not subprocess.check_output(
        ['git', 'ls-files', '--others', '--exclude-standard', '--', relative], cwd=ROOT)
staging = Path(tempfile.mkdtemp(prefix='.reviewed-adoption-', dir=destination.parent))
complete = staging / destination.name
shutil.copytree(source, complete, copy_function=shutil.copy2)
check_manifest(complete)
assert digest((complete / 'MANIFEST.json').read_bytes()) == sys.argv[3]
archive = Path(tempfile.mkdtemp(prefix='rk-uarch-vendor-review-archive-', dir=ROOT.parent))
prior = archive / destination.name
destination.rename(prior)
try:
    complete.rename(destination)
except BaseException:
    prior.rename(destination)
    raise
staging.rmdir()
check_manifest(destination)
assert digest((destination / 'MANIFEST.json').read_bytes()) == sys.argv[3]
print('Complete candidate adopted locally; prior snapshot preserved at', prior)
print('Candidate staging tree remains intact. Nothing has been committed.')
PY_ADOPT
uv run python -B scripts/vendor_rk.py --check
uv run pytest -q contract/tests --require-vendor
uv run python -B -m uarch_contract.generate --check
```

If any verification fails, stop and preserve the prior archive and candidate for
investigation. Do not continue to publication. Review the exact complete-directory
Git diff, together with the recorded old/new manifests, approval, reason and any
reviewed generator/sidecar/PARAMS changes. A human then publishes the approved
artifact and its review record in a new commit. For a refresh, retain the prior
publication commit in history; do not amend or rewrite it to erase the earlier
snapshot. Record the new commit identity in the review evidence. CI then consumes
only that committed revision. No publication or adoption command was executed in
this documentation-only follow-up.

## Stop condition

The final candidate is generated and verified but **not adopted**. Both snapshots
remain in their original locations; the generator and its fingerprint are unchanged.
The lifecycle and concrete adoption recipe are ready for Javid's review. U0002 and
the narrow carrier exception remain proposed. No Reza approval, real workload parity,
G1 completion or U1 completion is claimed. All changes remain local and uncommitted.

## Stage 2 RESPONSE — 2026-10-06 (current status)

Read [U1-lane-B-response.md](U1-lane-B-response.md) first. This is the author's response,
not reviewer adjudication. It answers every B F1–F16 and A-F12. Javid approved:

- total absolute deviation budget ≤5% per fixture/channel, residual ≤0.5%, rejection
  of unnecessary/zero/null-channel adjustments, and separate reporting of all four quantities;
- strict script/oracle fingerprint equality and verified/recorded locked oracle environment;
- revising A's flop_parity carrier before G1, with attribution/classification surviving serialization;
- retaining unchanged rounded nominal U1 inputs with exact documented parameter offsets;
- chmod as a local precaution, with manifest/compatibility/review/history enforcement;
- A-F12 interim refusal of unsupported uniform-/tp projections, without dropping coverage.

These are specific policy/scope approvals, not acceptance of all U0002, revised code,
any artifact, the narrow stub-source exception, or G1/U1. No Reza approval is claimed.
Accepted [U0019](../decisions/U0019-standalone-preparation-and-prepared-input-replay.md)
and coordinator commit `89313ee` govern preparation/replay ownership; U0003 owns the later
prepared-input schemas and U-P3 the producer/adapter, including component precision selection.

### Fingerprints, preserved candidates and validation limits

The revised generator SHA256 is
`4d2304002b262f2ee03dfe4f8fb338b350aacd80ea2488952849c416ee135317`.
The unchanged ORACLE_PROGRAM SHA256 is
`9dd67d4883206f14b8a5a00fa3d0ced95bddaa395ba634d80e08a39813ea04fb`.
F3/F4/F5/F6/F7/F10/F11 change the full script fingerprint. None alters the oracle bridge's
actual iteration_cost calls. Environment inventory is a separate interpreter command.
Future snapshots add the pinned upstream uv.lock and environment metadata, for 20 files
at the required baseline; the 864 records and two refusals must be compared, not assumed equal.

Both prior manifests remain untouched:

- Lane B snapshot: `4caea65f3c217bbb2030409833be6c67c15561552f8d9c9e179ac3ff82883284`.
- Human final candidate: `6b0d69c5737ba2b4cdbd8bce13ec860e4750f4008d9f4ee4fb8dc6db456d8304`.

Javid's report of two identical runs remains attributed human evidence. Read-only inspection
still confirms identical 864 oracle/two refusal bytes across them; only GENERATOR/MANIFEST
differ. Both are **historically intact, currently incompatible, unadopted**. The old external
environment's package identity cannot be reconstructed from those artifacts; no metadata was
backfilled. All reproduction/mutations used disposable code or synthetic test bytes.

Disposable Stage 2 integration: `/tmp/u1-b-response-r14129fi/integration`; evidence beside it.
A input is the frozen reviewed A proposal in `/tmp/u1-final-integration-84hif1_r`, originally
A HEAD `af3b1bc3df3171d196394a58f62202ad50845dfa` plus content inventory
`fc9522cc8daad2a8f21128657d9f3bfcab01e2154495d8fe9bf1c8076dae7b8f`.
This does not claim validation against later mutable A edits. The frozen coordinator baseline
is `89313eef20e6b252d235b40a680a1464c52c636a`. The original overlap resolutions are preserved;
B's new U-P2/build-spec passages merge cleanly on top. No source A or coordinator edits.

- New regression file: 47 fail / 3 pass before fixes; all 50 pass after fixes.
- New regressions plus existing harness/tooling tests: 85 pass.
- Strict contract: 203 pass / 1 fail; full suite: 207 pass / 1 fail; no skips.
- Both failures are `test_current_snapshot_generator_compatibility`: stale script fingerprint
  and absent environment metadata. Strict vendor --check fails for the same reasons.
- Mypy 43 source files, ruff, import-linter (2 kept), schema freshness and prompt sync (2) pass.
- Historical integrity/identity verification passes separately and cannot replace strict checks.
- No actual U2 workload parity, hosted CI or Linux-box cold-clone result is claimed.

### Handoff to A and remaining scope decisions

[Precise carrier proposal](U1-lane-B-flop-parity-interface.md) and
[representative payloads](U1-lane-B-flop-parity-payloads.json) are ready for A. A independently supplied its carrier/schema/toy proposal during this session. B then
captured it and implemented `contract_payload` with seven cross-lane tests proving kind,
fixture/channel/unit attribution and all four quantities survive. They all pass. No substitute
contract was added; integrated review and full acceptance remain pending.

A-F12 reproduces 10,161,390,592 versus 9,490,301,952 bytes (+7.0713%) at tp16/kv_heads8.
The aggregate/tp oracle is not an actual replicated-KV sharding oracle. Javid has approved
interim unsupported-projection refusal; the new guard and complete coverage report implement
that decision. Embedding accounting remains separately pending. The latest validation section
below supersedes the earlier scope/readiness state. No frozen values or tolerances changed.

### Exact future human generation procedure — NOT executed

First finish Stage 2 review/adjudication of all generator fixes/policies and the newly
integrated A carrier. Review the resulting combined source tree and rerun applicable checks.
If any generator byte changes, recompute its hash before following this recipe; do not use
the hash above as a promise for an unreviewed future edit. Existing candidate adoption recipes
are superseded. Generate in a new staging tree, preserving both current snapshots.

The following is a human-only recipe, not an action performed by this authoring session.
Use the final reviewed combined tree (the current disposable proposal path below is only a
candidate for that review; the new A carrier is captured and tested there):

```bash
set -euo pipefail
reviewed=/tmp/u1-b-scope-integration-3d8bfs06
rk_pin=/home/jjaff/AI-infra-simulation/rk-sim-u1-pin
pin=1e5706e0ebfcc67c1a7333079a35b75f693e9963
candidate=$(mktemp -d /tmp/u1-stage2-vendor.XXXXXX)
(tar -C "$reviewed" --exclude='./.venv' --exclude='./.git' \
  --exclude='./contract/vendor/rk-sim@*' --exclude='__pycache__' \
  --exclude='./.pytest_cache' --exclude='./.mypy_cache' --exclude='./.ruff_cache' \
  --exclude='./.import_linter_cache' -cf - .) | tar -xf - -C "$candidate"
uv sync --project "$candidate" --locked --extra dev --offline
oracle_parent=$(mktemp -d /tmp/u1-stage2-oracle-env.XXXXXX)
oracle_env="$oracle_parent/venv"
UV_PROJECT_ENVIRONMENT="$oracle_env" uv sync --project "$rk_pin" \
  --locked --no-default-groups --offline
UV_PROJECT_ENVIRONMENT="$oracle_env" uv sync --project "$rk_pin" \
  --locked --check --no-default-groups --offline
sha256sum "$candidate/scripts/vendor_rk.py" "$rk_pin/uv.lock"
git -C "$rk_pin" rev-parse HEAD
git -C "$rk_pin" status --porcelain --untracked-files=all --ignore-submodules=none
git -C "$rk_pin" ls-files -v
git -C "$rk_pin" ls-files --others --ignored --exclude-standard
# Human verifies exact pin, pristine status, H-only index flags and no ignored files.
cd "$candidate"
UARCH_HUMAN=1 UV_PROJECT_ENVIRONMENT="$oracle_env" \
  make vendor-rk SHA="$pin" RK="$rk_pin" PARAMS='' | tee generation-first.log
UARCH_HUMAN=1 UV_PROJECT_ENVIRONMENT="$oracle_env" \
  make vendor-rk SHA="$pin" RK="$rk_pin" PARAMS='' | tee generation-second.log
uv run --no-sync python -B scripts/vendor_rk.py --check
uv run --no-sync pytest -q -rs contract/tests --require-vendor
uv run --no-sync pytest -q
uv run --no-sync mypy src contract scripts
uv run --no-sync ruff check .
uv run --no-sync lint-imports
uv run --no-sync python -B -m uarch_contract.generate --check
uv run --no-sync pytest -q tests/unit/test_prompt_sync.py
sha256sum "contract/vendor/rk-sim@$pin/MANIFEST.json"
```

Expected generation messages are **created: 20 files** then **verified-identical: 20 files**
for the unchanged required matrix and no extra PARAMS. The expected matrix is 864 records
and two refusals with original nominal sidecars; no expected *manifest* hash can be supplied
before the human run. Generation refuses environment drift, ignored source files, pinned
input mismatches or occupied differing output. The environment is external and its verified
runtime inventory/lock digest are recorded; CI need not use the same interpreter/packages.

For a reviewed future PARAMS refresh, copy retained/new inputs into staging, inventory their
hashes, and supply the complete list. U2 must first settle its component-specific precision
and prepared-input interfaces. Do not assume an FP16-only matrix can cover BF16-only npu-l4.

Save the two run logs and compare against **both** preserved snapshots. Classify metadata,
added uv.lock, upstream/source/component/sidecar changes, fixture additions/removals and changed
existing counts/durations/null/refusal outcomes. The existing handoff's comparison procedure
is read-only; it does not approve changes. Any changed existing oracle value requires explicit
human review and a reason. Do not hand-edit metadata or silently accept changed values.

Before adopting any future candidate, from the actual final reviewed target tree, verify the
candidate with **that target's** current checker (this was missing from the earlier recipe):

```bash
uv run --no-sync python -B - "$candidate" <<'PY_VERIFY'
import sys
from pathlib import Path
from scripts.vendor_rk import PIN, ROOT, check_contract_pin, check_manifest, check_generator, check_snapshot_inputs
candidate = Path(sys.argv[1]) / 'contract/vendor' / ('rk-sim@' + PIN)
check_contract_pin(ROOT)
check_manifest(candidate)
check_snapshot_inputs(candidate)
check_generator(candidate)  # binds target script/oracle and required environment metadata
print('Candidate compatible with target implementation; adoption still requires human approval')
PY_VERIFY
```

Only after explicit approval use the complete-directory adoption procedure, preserve prior
artifacts, and record old/new manifest hashes, reason, approval/date/reference and publication
commit. This will be first publication if no snapshot has yet been committed. Neither the
commands here nor any adoption operation were executed in Stage 2. Keep snapshots unmodified;
ordinary reruns must continue refusing replacement. U0002, G1 and U1 remain pending.

### Final captured-A carrier integration (supersedes the initial Stage 2 totals)

A's source worktree advanced independently during this response. B did not edit it.
Captured complete A proposal identity:
`aa568a839e401047a242f24b176274fc144ac364e8d9924ca4880480b1a03258`, HEAD still
`af3b1bc3df3171d196394a58f62202ad50845dfa`. Fresh disposable tree:
`/tmp/u1-b-response-carrier-9sinndh2`. Input copies, inventories, commands and conflict
resolutions: `/tmp/u1-b-response-r14129fi/carrier-integration/`.

Two U-P3 doc conflicts (prompt/build-spec) preserve coordinator U0019's prepare/replay text
plus A's added omission/shared-SRAM/shard notes. The captured A production files and schemas
are unchanged in the copy. B's adapter uses A's actual FlopParity, not replacement classes.
Seven carrier tests: 6 failed/1 passed before B adapter, **7 passed after**; all 50 initial
review regressions also pass. The seven include 864×3 preserved oracle echoes serialized
with explicit self-test classification, not actual U2 workload parity.

Final strict tests: **360 passed, 1 failed**, full tests: **364 passed, 1 failed**, no skips.
The only failure remains old-snapshot current compatibility. Mypy **46** files, ruff,
import-linter (2), schema freshness and prompt synchronization pass. Historical integrity
passes separately. The generator fingerprint is unchanged by the adapter work; both existing
snapshots remain intact, stale under the revised strict policy and unadopted. Further mutable
A changes after this capture require another integration run, not an expanded claim here.

## Latest A-F12 follow-up and captured-A validation — 2026-10-06

This section supersedes the earlier scope status and integration totals above. Author
dispositions: **B-F1–F15 APPLIED; A-F12 APPLIED; B-F16 DEFERRED to U2**. These are not
independent reviewer adjudications. Embedding accounting remains the separate unresolved
numerical-scope question; nominal inputs and approved tolerances remain unchanged.

### Exact integration inputs and conflict resolutions

Fresh disposable tree: `/tmp/u1-b-scope-integration-3d8bfs06`.
Evidence, input copies, command logs/JUnit, audit and merge records:
`/tmp/u1-b-scope-evidence-5st8n19o/`.

Coordinator main remains `89313eef20e6b252d235b40a680a1464c52c636a`. The assembly starts
from the previously validated combined tree, preserves its coordinator/A/B overlap resolutions
and combined Makefile, then applies the delta from captured A revision `aa568a83…3258` to
A's newly delivered complete follow-up. Current captured A **content identity** is
`3f408194c6e26165770e35675b72939469dfe74d660b7e5d6b778bad18a3f773`, with HEAD
`af3b1bc3df3171d196394a58f62202ad50845dfa` on `u1/contract`. Identity hashes the sorted
path→SHA256/mode inventory in `A-input.json`; this identifies uncommitted bytes, not a commit.
The captured A handoff includes approved A-F1/A-F2/A-F12 and the exact B-F8 delivery.

B's adapter targets **that revision's** actual `FlopParity`, `ParityChannelComparison`
and `FlopDeviation`. It adds no A field/schema and edits no A worktree. Relative to the
previous A capture, carrier implementation and schemas are unchanged; current A documentation
and additional regression are integrated. Exact SHA256s:

| A interface file | SHA256 |
| --- | --- |
| `contract/schema/FlopDeviation.json` | `7cb60d212136f1f588b369ef9ad1bfe26b4d59bc8886d90dba07c25c4f2a071d` |
| `contract/schema/FlopParity.json` | `7235d5bc4152498dddc076948c674e23a98bee88c1e19ee5fa8710b5d6380118` |
| `contract/schema/ParityChannelComparison.json` | `8f6ba28d16c1ce0afdacafecd801582a3827ccd28c7480530a4c7345d15383dd` |
| `contract/uarch_contract/table.py` | `0ddfdc94d5dcaac9e26e7c27577fa82d9b06feb7fc9da60df5f9ccd594779749` |
| `docs/reviews/U1-U-P1-handoff.md` | `deb1a6c1c36400052d520395f961661ac7ce8da3a2b898f138a5af693467ccc8` |

All 88 captured A production/schema/toy files match the disposable tree byte-for-byte.
The two mirrored documentation conflicts (build-spec and U-P3 prompt, two hunks each)
retain coordinator U0019's validated prepared-graph engine and prepare/import/replay flow,
and append A's typed parity/ratio requirements plus table/request/spec identity and condition
resolution requirements. U-P1 and U-P19 changes merge cleanly. B's new U-P2 wording is
applied to both prompt and build-spec; prompt-sync passes. `assembly.json` and
`resolutions.json` preserve the exact old/new/merged text. Neither source worktree nor
coordinator main was modified to resolve a conflict.

### Scope regressions and exact validation results

`contract/tests/test_projection_scope.py`: **17 passed**. First 15 cases failed before
the scope/report fix (`scope-red.log`); the additional over-budget diagnostic case failed
before its metric-preservation fix, while the added valid-A padding case already passed
(`scope-extra-red.log`). Final targeted evidence: `scope-green-final.log`.

- The reproduced 70B/tp16/kv_heads8 case preserves 9,490,301,952 aggregate/tp versus
  10,161,390,592 rank-local read bytes (+7.07130967%). This arithmetic is the review's
  synthetic reproducer, never replacement oracle generation. A accepts the legitimate
  request; B refuses its projection before calling a candidate, even an exact echo.
- A-valid padded vocabulary and nondivisible FFN/expert widths are unsupported. Supported
  tp1/2/4/8 cases and all 864 preserved baseline fixtures retain passing self-test coverage.
- Mixed coverage reports retain supported, unsupported and numerical failures. A synthetic
  +6.54% count probe stays failed, not an embedding exemption or measured embedding offset.
  A +3%/+3% declaration remains over-budget despite zero residual, preserves all four
  quantities, and does not prevent reporting a later supported fixture.
- Incomplete/nonpassing reports cannot serialize through A's successful carrier. Duplicate
  fixture ids fail before collapsing coverage. All seven carrier tests still pass, preserving
  explicit self-test kind, fixture/channel attribution, units and all four quantities.

Commands ran in `/tmp/u1-b-scope-integration-3d8bfs06` with UARCH_HUMAN unset. Setup:
`uv sync --project /tmp/u1-b-scope-integration-3d8bfs06 --locked --extra dev --offline`.

| Exact command | Result |
| --- | --- |
| `uv run --no-sync pytest -q contract/tests/test_projection_scope.py contract/tests/test_parity_carrier.py contract/tests/test_flop_parity.py contract/tests/test_u_p2_review.py --require-vendor` | **84 passed** |
| `uv run --no-sync pytest -q -rs contract/tests --require-vendor --junitxml=/tmp/u1-b-scope-evidence-5st8n19o/strict-contract.xml` | **378 passed, 1 failed, no skips** |
| `uv run --no-sync pytest -q -rs --junitxml=/tmp/u1-b-scope-evidence-5st8n19o/full-suite.xml` | **382 passed, 1 failed, no skips** |
| `uv run --no-sync mypy src contract scripts` | Passed, **47 files** |
| `uv run --no-sync ruff check .` | Passed |
| `uv run --no-sync lint-imports` | **2 kept, 0 broken** |
| `uv run --no-sync python -B -m uarch_contract.generate --check` | Schemas fresh |
| `uv run --no-sync pytest -q tests/unit/test_prompt_sync.py` | **2 passed** |
| `uv run --no-sync python -B scripts/vendor_rk.py --check` | Expected **exit 1**, stale artifact |
| `PYTHONPATH=. uv run --no-sync python -B /tmp/u1-b-scope-evidence-5st8n19o/audit.py` | Historical integrity/inputs and preservation pass; strict incompatibility explicitly asserted |

The **only** failing test in strict/full runs is
`test_current_snapshot_generator_compatibility`: `GENERATOR current incompatibility:
generator script fingerprint differs; locked oracle environment metadata missing`.
No skips, xfails, metadata edits or relaxed check flags conceal it. The integrated suite
is **not green**. No unexpected implementation failure remains. Optional-SRAM, explicit
DRAM mode, revised table hardware identity/conditions, ModelShape and vendored round trips
are included in these runs. Synthetic harness probes/echoes establish no actual U2 workload
parity, hosted CI result or Linux-box cold-clone result.

### Preserved artifacts and readiness for human review/freezing

Read-only audit verifies both historical manifests, complete 864-record/two-refusal coverage,
and identical oracle/refusal values. The two historical snapshots still differ only in
GENERATOR.json and MANIFEST.json. Final human candidate manifest remains
`6b0d69c5737ba2b4cdbd8bce13ec860e4750f4008d9f4ee4fb8dc6db456d8304`; the prior B manifest
remains `4caea65f3c217bbb2030409833be6c67c15561552f8d9c9e179ac3ff82883284`. Javid's
reported two identical successful runs remain attributed human evidence, not agent execution.
The disposable integration uses an exact copy of the final human candidate. Both originals
remain **historically intact, strictly incompatible and unadopted**; rk-sim remains clean
at its exact pin. A/coordinator contents are unchanged since capture.

The scope fix and alignment against the delivered A revision are complete. No known pending
B implementation work requires another generator edit. The script fingerprint is unchanged
by this follow-up: `4d2304002b262f2ee03dfe4f8fb338b350aacd80ea2488952849c416ee135317`;
ORACLE_PROGRAM remains `9dd67d4883206f14b8a5a00fa3d0ced95bddaa395ba634d80e08a39813ea04fb`.
Inputs are **ready for review and an explicit freeze, not declared frozen or approved**.
Review-driven script changes would change the full fingerprint and must precede the human
candidate step. Preserve approved nominal sidecar inputs, exact upstream pin and PARAMS=''.
Embedding accounting remains a U-P3 workload-parity decision; it grants no permission to
alter these inputs, adjust oracle outputs or turn an ordinary failure into unsupported scope.

After review/freezing, Javid can use the handoff's future-human recipe, now pointing at this
captured combined tree: separate staging; verified external locked environment; two identical
human generations; manifest/matrix/strict integration checks; classified comparison against
both preserved artifacts; explicit review of changed existing values; then separate approval
for complete adoption/publication. Expected revised baseline is 20 files (including uv.lock),
864 records and two refusals. No replacement manifest is invented. No generation, artifact
patching, adoption or UARCH_HUMAN setting occurred here. Strict tests must actually pass with
the human-generated compatible revision before an integrated-green claim.

**B-F16 remains deferred to U2.** Lane B's vendor/parity maintainer owns the deferred matrix
change; Lane A's U-P3 preparation/workload owner implements the prepared/imported-bundle
adapter; the U0003 author owns the component-precision interface. Javid receives this concrete
handoff as acting U1 owner/approver. Acceptance requires a BF16-only npu-l4 PARAMS fixture,
validation against its declared supported compute peak (no substitute), and parity adapter
coverage of the actual prepared bundle under U0019. Review any later generator change and
refresh at the same upstream SHA through the approved artifact lifecycle. No successor work
is implemented now.

Complete ADR acceptance, reviewer adjudication, embedding-accounting scope, human candidate
review/generation/adoption/publication and G1/U1 acceptance remain outstanding. All proposals
remain uncommitted. No Reza approval or physical-correctness certification is claimed.
