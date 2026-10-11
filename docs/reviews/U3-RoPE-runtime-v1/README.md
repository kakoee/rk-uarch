# U0022 additive runtime — local implementation handoff

**Local author checks; not integrated acceptance, independent review or permission to push.**
Javid's [runtime authorization](../U3-RoPE-install-and-runtime-v1/README.md) governs this work.
The coordinator's installation receipt was read and verified: human commit
`eeb2f4d74d4c751c55edec1b5ee40f7a40162562`, parent
`df4caf81969c5aafa90ea183dfc8d9e69334d9f0`, tree
`cb0d7fd650426706a7cdadf2058bf49637c1ec4d`. It remains an ancestor. No live protected path
was edited, no human flag set, and no source-bound commit pushed. Javid acts for both lanes;
no Reza approval is claimed.

## Exact local work and preserved history

| Commit | Owned change |
| --- | --- |
| `37703fbdfbf090bad9d7f219d480c2ed8f9d1e39` | Ordinary merge of published installation/release coordination into local human-installed main |
| `88b2faa441f35b65ae6f7d0b2c2c5b0ace198063` | First 50 boundary/count/replay specifications, observed failing on absent runtime module |
| `b5c1a9e89aa1a7a8d83aad48bb345f75f92e0bb0` | Additive admission, coefficient-input preparation, protocol/mirrors, analytic execution, dispatch/capture and tests |
| `be328c554694482b60065df5aa25b7e46d2ac6d5` | Exact accepted prototype schema equality, including required-field ordering; regression failed before correction |
| `a02085de78d6a4d84eec0869b8ebf57b92c64b79` | Ordinary merge of peer main through `4815b7c2ef994ccd70d397f688ab6fbec3d3921d` |
| `e1aa04c75faf3c92e1e8e97f98a05e6aa4349f65` | Stronger normalized-result, MoE multiplicity and representative-rank tests; runtime bytes unchanged |
| `24c03f42083d9beaccb1a1a8ef6e62069b73cd96` | Static relative-import resolution complies with the unchanged protected production-isolation guard |
| `279134164ee526e10cc5d2a8ee36f22828c8a9ed` | Changed-byte refusal across direct/transitive engine, hardware, capacity and protected carrier dependencies |
| `7f735526a0563049ec726884be4aa6bf377359b9` | Complete independent duplicated-job, reconstructed-request and fully rebound active-assumption controls; runtime bytes unchanged |
| `7f735526a0563049ec726884be4aa6bf377359b9` | Complete independent duplicated-job, reconstructed-request and fully rebound active-assumption controls; runtime bytes unchanged |

Use Git diffs across these commits, not copied checkpoint trees. Existing source paths under
`src/` are unchanged: all runtime changes are additive. In particular core.py, old entry point,
protocol.py, workload prepare/prepared/characterize, table/build.py and CLI/public table/report
remain byte-identical. Old core hash remains
`sha256:fa3938f8c009c7b80700d35feba7504e4b4da06e628d2e387480c358963974ea`.
B's standalone-v1 fixes and published evidence were integrated without edits. Prior planning,
protected proposals, accepted ADRs and all historical payloads remain intact.

## Implemented boundary and dependency closure

- `workload/prepared_v2.py`: strict v2 loader, grid/rank/hardware/graph admission, active
  assumptions, request reconstruction, job preparation and execution. Imported instances are
  serialized/reparsed to avoid accepting unchecked `model_copy` updates. Bare bundle admission
  does not certify an engine/assumption identity; complete execution always joins active assumptions.
- `workload/producer_v2.py::prepare(intent, hardware, *, coefficients, ...)`: explicit v3 intent
  and supplied coefficient carrier are mandatory. Builds new v2 nodes directly, never upgrades
  or strips a submitted v1 bundle. No coefficient generator or named-model inference exists.
- `workload/capacity_v2.py`: known weights, paged KV and one shared full coefficient allocation;
  total peak stays null. Existing weight-fit refusal and incomplete-capacity warnings remain.
- `engines/protocol_v2.py`: four exact accepted engine roots and their separate `schema/v2/`
  mirrors. `validate_engine_job(job, bundle, request, *, assumptions)` joins all duplicates and
  rederives sourced hardware. `validate_engine_result(result, job, bundle, request, *, assumptions)`
  recomputes every admitted result field, including scopes, counts, durations, attribution and nulls.
- `engines/analytic/rotary_v2.py::run_analytic(job, *, bundle, assumptions)` requires complete
  closure; parsing a job is insufficient. The internal evaluator and isolated `counts` helper
  are not full admission APIs. Nonrotary formulas are explicit v2 code with their new identity;
  no v1-core delegation on a graph with RoPE removed occurs. Contributor selectors conservatively
  bind the complete point, coefficient table, profile, rank and assumptions, plus timing leaves.
- `engines/analytic/dispatch.py`: one explicit protocol choice; no retry/fallback. V1 delegates
  unchanged to the old core. V2 requires bundle/assumptions. The additive module CLI takes one
  job on stdin plus `--bundle` and `--assumptions` files for v2. Existing public CLI is unchanged.
- `table/capture_v2.py`: explicit raw `CapturedWorkV2(bundle, assumptions, request, jobs, results)`;
  `capture(..., workers=1)` and ordered, complete imported `replay(...)`. No public v2 table,
  report, evidence/card attachment, subprocess worker pool or new shared carrier is introduced.

Q and newly appended K alone rotate; exact fused/unfused producer roles, local heads, TP/KV
replication, positions, table/profile/cache bindings, full-tail transfers, FP32 coefficient
reads and scalar cast counts follow U0022. Existing cache values are declared, not authenticated
by this scalar model. Projection Y[b*S+s,h*D+d] corresponds logically to rotary
X[b,h,s,d]; this is no claim of physical byte-layout equivalence or a free transpose. BF16-only matrix hardware admits supplied FP32 coefficient storage without
requiring an FP32 matrix peak or adding a hardware format: the table's fixed four-byte scalars
are defined by U0022. If an FP32 storage descriptor is present, its width/block policy is checked.
X/Y and KV still require the same supported FP32/BF16/FP16 hardware format and valid compute rates.

The execution identity is
`sha256:c5420668fb3db8781168f4b8b9495a28474f001356cff10f1df9915158f8cdf6`, model
`physical-resolved/2`, engine `resolved-ops/2`. `identity_v2.execution_dependencies()` is the
single reproducible source of its **36-file local Python closure**, not a maintained manifest.
It traverses static imports, including function/conditional imports and package initializers,
from exactly the five accepted roots: rotary_v2, dispatch, protocol_v2, prepared_v2 and protected
rotary_v2. The additional owned dependency is capacity_v2 plus identity_v2 itself. Reused harness
modules are hw/derive, old protocol/core (the explicit legacy dispatch branch), and package
initializers. Contract dependencies are the actual imported carrier, hashing, comparison,
derivation, registry, source/fidelity/evidence/report-scope/model modules and initializer.
After v2 dispatch, all 36 imported module origins matched these local source paths.
No dynamic local imports occur in this closure; adding one requires explicit closure review.

The sorted relative-path/content-hash mapping is hashed under `analytic-rope-implementation/1`.
Fresh bytes are checked on each identity call; source changes after import refuse until process
restart, avoiding labeling loaded old code with new disk bytes. A fresh process under changed
bytes gets a different identity even with the same version and refuses old jobs/assumptions.
Producer and capture orchestrators are not engine execution dependencies; producer bytes have
its separate Producer identity, captured inputs bind outputs, and **both remain U0002 support-bound**.
The hash does not claim to identify interpreter/installed dependency bytes; lock/environment
and the broader support set remain separate U0002 obligations. No new support exclusions exist.

B/coordinator must reconcile only future shared uses: v2 table/report carriers, eligibility,
new relation corpus/model bindings, coefficient closure and conservative contributor selectors.
B's authorized standalone v1 work requires no API change and gains no v2 evidence eligibility.

## Tests first, fault removal and pending protected patch

Initial boundary collection failed on the missing runtime module. Producer and contributor
specifications separately failed before those APIs existed. Literal expectations never call
production formulas to generate expected values. The source-change regression failed before
adding the imported-source guard; exact schema comparison failed on job required-field ordering
before fixing it. No expected count, traffic or protected fixture was changed to make code pass.

The owned tests cover rehashed graph/job/result adversaries with valid controls, all supported
precisions, both attention forms, both analytic modes, decode/prefill, partial R, repeated layers,
MoE multiplicity, selected/equivalent ranks, replicated/sharded KV, coefficient replacement,
producer-disabled imported replay, three byte-identical fresh-process executions and v1 routing.
Pairing and separate FP32 RNE/low-precision tie/cancellation examples are independent **normative
reference tests**, not a numerical RoPE kernel or physical instruction evidence.

[protected-tests.patch](protected-tests.patch) is an **unapplied one-file human proposal**:
remove the 28 skips, update their pending docstring and rename the test function. Keep the
historical filename and all positive/counterexample fixtures unchanged. No further carrier
schema/test changes are required by this implementation; broader job/result regressions live
in A-owned tests. The human must review/install/commit this patch separately. Applicability:

```sh
git apply --check docs/reviews/U3-RoPE-runtime-v1/protected-tests.patch
uv run --no-sync python docs/reviews/U3-RoPE-runtime-v1/exercise.py --revision 7f735526a0563049ec726884be4aa6bf377359b9
```

The [exercise](exercise.py) exports that Git commit to disposable scratch and applies the patch
**only there**. It executes **102 protected tests, zero skips**, including the 28 formerly pending
admission checks. It injects/removes 14 exact faults: omitted casts, wrong pair arithmetic,
coefficient rereads per head, omitted K coefficient reads, dropped tails, double repeats, extra
TP division, page-rounded rotation, missing rotary graph admission, missing engine identity join,
missing result recomputation, coefficient retention across layers, missing active-assumption
validation and missing reconstructed-request validation. Every fault causes a
regression assertion failure; baseline and restored controls pass. The fresh-process identity
experiment also refuses old work after changed source with an unchanged version. Compact exact
outcomes are in [exercise-results.json](exercise-results.json); no export tree or captured input
payload is retained. These are author regression experiments, not independent U-REVIEW or G2.

## Checks and remaining publication gate

Final author-check results are recorded below. Counts from focused, full and
export runs overlap; they must not be added as unique coverage. The live protected suite still
has its 28 intentional skips until the human test-patch commit.

- `uv run --no-sync ruff check .`: passed.
- `env -u PYTHONPATH -u MYPYPATH uv run --no-sync mypy src contract/uarch_contract scripts`:
  passed, 78 source files. The corresponding `mypy --no-explicit-package-bases contract/tests`
  command with both variables unset passed, 31 files.
- `uv run --no-sync lint-imports`: both contracts kept; 101 files, 600 dependencies.
  Protected production-isolation regression also passes; its guard was not weakened.
- Old contract `uarch_contract.generate --check`, new `generate_rotary_v2 --check`, old engine
  `protocol.generate(check=True)` and new `python -m rkuarch.engines.protocol_v2 --check`: fresh.
  All four new engine schemas equal the accepted prototype exactly.
- Final focused command selects `tests/rotary_v2`, both installed rotary test files and
  `contract/tests/test_u2_schema_freshness.py`: **270 passed, 28 skipped** (73.83s).
  Breakdown: 132 owned tests + 74 installed carrier/fixture tests + 64 old schema tests.
  The 28 human-owned admission checks remain skipped live, not counted as runtime passes.
- Disposable export at `7f735526a0563049ec726884be4aa6bf377359b9`: **102 passed, zero skipped**
  after proposed activation; 14 injected faults detected, all restored controls pass. The 74
  carrier passes and the 28 activated cases overlap live tests/owned counterexample coverage.
- `uv run --no-sync python scripts/vendor_rk.py --check`: **expected refusal**, exit 1,
  `input support inventory changed`.
- `uv run --no-sync pytest -q -rs contract/tests --require-vendor`: **651 passed, 28 skipped,
  2 failed** (6.79s). Both failures require current support:
  `test_committed_snapshot.py::test_current_snapshot_generator_compatibility` and
  `test_u2_historical_snapshot.py::test_current_canonical_is_exact_adopted_1008_four_real_refusals`.
  Both report `input support inventory changed`. These are not waived or called green.
- `uv run --no-sync pytest -q`: **1656 passed, 57 skipped, 2 failed** (812.27s).
  The only failures are the same two strict-currentness tests above. This full run collected
  at `279134164ee526e10cc5d2a8ee36f22828c8a9ed`; production/support bytes stayed unchanged.
  Its 117 owned rotary tests overlap the final focused run. The later 15 added join controls
  at `7f735526a0563049ec726884be4aa6bf377359b9` passed separately and in the final 270-test
  selection; they are not counted among the 1656 full-run passes. No full rerun for subsequent
  test-only/prose changes. Legacy public capture/table/report tests are included; no functional
  failure remains outside the currentness gate.
  The 57 skips are 28 pending human-owned admission activations plus 29 pre-existing analytic
  capability/precondition skips: 14 unobservable/deferred relations in each of two modes and
  one per-op exact-clock premise invalidated by memory-only embedding. They are not passes or
  new waivers; see `validation/L0_invariants/test_analytic_capabilities.py`.

The earlier full run was deliberately interrupted at 768 passed after the separate strict run
exposed the forbidden `importlib.util` helper import. That is **not a full-suite result**.
The existing protected isolation test failed before the owned static-resolution fix and passed
afterward. The full run was restarted on the corrected fixed source. No protected guard changed.

The failed focused invocation naming nonexistent `contract/tests/test_u2_schemas.py` ran no
tests; it was corrected to `test_u2_schema_freshness.py`. No dependency/system installation,
container, simulator, benchmark, runner/nightly action, oracle generation/adoption or historical
currentness substitution occurred. The full-suite command is local pytest, not a manual nightly.

New support-bound paths are the eight added runtime Python modules above (prepared, producer,
capacity, protocol, rotary, identity, dispatch, capture), plus the human-installed protected
rotary carrier and its generator. Existing recursive enumeration also retains all old source,
scripts, lock, PARAMS and explicit retained inputs. Mirrors need both schema freshness families.
The proposed contract-test activation is human-owned even though it adds no support exemption.

Next dependency is **coordinator reconciliation of this exact local implementation/patch**, then
one combined source freeze. Preserve ordinary local Git history and integrate peer work before
that freeze. Human U0002 generation/adoption remains required:

1. Freeze reviewed source, complete support inventory, lock/environment, PARAMS/precision matrix,
   sidecars/attribution and pristine upstream `1e5706e0ebfcc67c1a7333079a35b75f693e9963`.
   B/coordinator prepares the exact frozen input identity; never reuse an old manifest.
2. Human generates the candidate twice from identical frozen inputs in separate processes with
   the guarded vendor tooling; retain created/verified-identical receipts. Drift starts a new cycle.
3. Strictly check candidate/current support, complete inventory/coverage/attribution/refusals and
   compare old/new inputs, query identities, counts, durations and nulls. Preserve U2 nominal rows
   and absent RoPE channels; investigate changed existing values rather than hiding them.
4. Javid approves the exact complete candidate and makes protected test/adoption commits, recording
   manifests, frozen revision and approval. Agents neither set the human flag nor adopt artifacts.
5. On that exact integrated tree, rerun both schema families, Ruff, both CI-form mypy commands,
   import contracts, strict vendor/contract checks, focused rotary/legacy public workflows and
   full suite. Any source-bound change after freeze needs a new lifecycle. Only then may a
   separately verified normal main push occur. This handoff performs none of those human steps.

Bounded implementation is ready for coordinator review, subject to the check results above.
Allow 4–8 additional A engineering hours for review fixes/revalidation if requested; no further
runtime work is authorized by this handoff. Coordinator/B interface reconciliation remains
4–8 active hours; human freeze/generation/audit/adoption 4–8 active hours plus the small protected
activation review/commit; independent review 4–8 active hours if separately commissioned.
These are estimates, not recorded hours or approvals. Human/reviewer calendar waits are separate
and unbounded. Public v2 product/report work is outside this estimate. Reza's runner/manual-nightly
wait is separate; no host reservation/waiver is granted. Tool selection, instrumentation, fallback,
U0005's proposed 200-second synthetic diagnostic and G2 verdict remain pending. No U3 closure.
