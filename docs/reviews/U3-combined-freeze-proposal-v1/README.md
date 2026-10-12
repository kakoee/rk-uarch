# U3 combined source/input freeze — proposal for coordinator review

**PROPOSED; no oracle generation, adoption, protected-test activation or A push.**
Javid already approved the runtime and later combined U0002 lifecycle. This package
makes that lifecycle's source/input selection concrete under
[coordinator reconciliation](../U3-RoPE-runtime-reconciliation-v1/README.md).
It is not acceptance of a candidate or an independent U-REVIEW verdict. Javid acts for
both lanes; no Reza approval is inferred.

## Exact proposed selection

| Binding | Proposed identity |
| --- | --- |
| A local unpublished source | `187fe3b035bee9cbeae13b03c8b4ac6ef0ee276f` |
| A tree | `fe10c7d4b08a6910f165da9b92f8e13a2a37c107` |
| Human schema ancestor | `eeb2f4d74d4c751c55edec1b5ee40f7a40162562` |
| Published peer ancestor, including SR-C1 and CI portability | `4815b7c2ef994ccd70d397f688ab6fbec3d3921d` |
| New input SHA256SUMS digest | `27c6238d42e57dc4f2b1baf0c8846c11f1eec2968176dcefcdc463beb64bc80f` |
| Prior U2 input digest, not reused | `08d0e905cc50943d286b9c6dbcfb2cf844c969dda28b9446162d12734870871c` |
| Current adopted artifact MANIFEST.json digest | `20eee19b0e864ad07a7b122da7544e385116fdd50d279e1fac1bfbbf03a697ad` |
| Pristine upstream pin | `1e5706e0ebfcc67c1a7333079a35b75f693e9963` |

[proposal.json](proposal.json) binds exact clone/environment/output locations, generator
and oracle-program hashes, and normal safety-hook bytes. A's HEAD/tree/clean state and
ancestry were checked read-only. No A index, source file, dependency or HEAD was changed;
none of A's source-bound Git history was fetched into B or published main. A must remain
at this revision until the proposed two-run generation finishes. Drift requires coordinator
reconciliation and a new selection, not a helper override.

The exact [input manifest](input-SHA256SUMS) describes 23 payload files plus SHA256SUMS:
three component descriptors, three attributed model sidecars, seven content-addressed
artifacts, six retained historical-source files, precision declarations, the support
manifest, PIN and ADOPTED-MANIFEST-SHA256. Bulk input payloads are reproducibly staged by
A's unchanged `scripts.u2_inputs.prepare_inputs`; they are not duplicated in this proposal.
`load_inputs(..., check_support=True)` verified the new staging. These are pure input/export
operations, not oracle calls. Staging differs from current adopted `u2-inputs/` **only in
support-files.json and SHA256SUMS**; every other input byte is unchanged.

The existing input member ADOPTED-MANIFEST-SHA256 still names retained U1 provenance
`b3a575d0e3f27a4057678a2298609a580fd5a5e1dd858b0f4af086f2dc9e0e1d`.
That historical identity is distinct from the current U2 artifact manifest above. Neither
historical integrity nor unchanged nominal values establish current support compatibility.

## Complete support delta and scope

The unchanged `scripts.u2_inputs.support_files()` enumerates **97 files**, up from 87.
[Support files](support-files.json) and [exact old/new delta](support-delta.json) are artifact
provenance, not a second source-control system. All 87 old support entries have identical
bytes; none is removed. The ten additions are:

- `contract/uarch_contract/{rotary_v2,generate_rotary_v2}.py`;
- `src/rkuarch/engines/analytic/{rotary_v2,identity_v2,dispatch}.py`;
- `src/rkuarch/engines/protocol_v2.py`;
- `src/rkuarch/workload/{prepared_v2,producer_v2,capacity_v2}.py`;
- `src/rkuarch/table/capture_v2.py`.

The recursive Python support enumeration includes every additive v2 module/carrier and
all 36 files of `identity_v2.execution_dependencies()`, including old shared dependencies.
Its exact execution identity is
`sha256:c5420668fb3db8781168f4b8b9495a28474f001356cff10f1df9915158f8cdf6`.
Producer/capture code remains in the broader U0002 support set even where outside the
engine's execution closure. Old source/scripts, pyproject/uv.lock, npu-l4 PARAMS, explicit
comparison/adaptation helpers, pinned source inputs and retained provenance remain present.
Generated schema mirrors are covered by Git source identity and separate freshness checks,
not newly added to the established Python support enumerator. No exclusion was changed.
The future test-activation file is outside that existing support set, with no new exemption.
No support/tooling implementation change is needed for this proposal.

Matrix remains seven component/precision choices × three models × tp={1,8} × 24 queries:

| Component | Compute / KV pairs | Rows |
| --- | --- | ---: |
| asic_placeholder | FP16/FP16, FP16/FP8 | 288 |
| nvidia_h100_sxm | FP16/FP16, FP16/FP8, BF16/BF16, FP8/FP8 | 576 |
| npu-l4 | BF16/BF16 | 144 |

Models remain nominal llama-3.1-8b, llama-3.1-70b and mixtral-8x7b, with original totals,
active counts, shapes and source attribution. Decode B={1,8,32} × context per sequence
{128,512,4096,16384}; prefill n={1,4,16} × length={128,512,2048,4096}. Expected inventory
is 1,008 rows (504 decode/504 prefill) and four real UnsupportedPrecision refusals:
placeholder BF16/BF16 and FP8/FP8; npu-l4 FP16/FP16 and FP8/FP8. Refusal boundary remains
`Accelerator.peak_op_per_s`, bound to the same pinned callable source and component bytes.
No PARAMS/precision override, row selection, deviation or threshold change is proposed.

Pinned rk-sim channels do not model the new physical RoPE work. Counts remain nominal
replica scope and durations one representative TP rank without collectives. Vector counts
remain absent, and decode memory writes null, never invented zero. Refreshing support does
not introduce physical-v2 parity. A's new route explicitly requires v2 carriers/coefficient
inputs; nominal oracle construction stays v1. B's standalone reports remain v1 at their
original implementation/toolchain/corpus bindings, including eab89e0 and 85a5ad2. No new
analytic corpus, source interpretation, card attachment or positive eligibility is proposed.
STUB, unknown error and unverified energy remain unchanged.

## Proposed human helper and actual preflight

[preflight.py](preflight.py) was executed; [human_generate.py](human_generate.py) was **only
parsed/compiled and linted, never executed**, including no --help invocation. No agent set
UARCH_HUMAN. The generation command below is a future human action after coordinator review
and Javid's exact freeze/generation confirmation; it is not a claim of current permission.

Preflight loads proposal files relative to their own B/primary folder, then explicitly loads
A's modules using A's installed interpreter with `-I -B`. It checks imported origins, exact
HEAD/tree/ancestry, clean tracked/index/untracked state, hidden index flags, normal effective
hooks path and executable hook bytes, complete support, reproduced input identity, predecessor
artifact integrity, upstream pristine state and exact environment metadata/locks. Alternate
Git directory/index and Python import contexts refuse. `--proposal-commit` additionally
checks every package byte/inventory against the caller's full reviewed Git commit, without
a circular self-hash or reliance on the eventual runtime publication commit.

Source environment: A's existing `.venv`, CPython 3.12.14, 35 installed distributions;
`uv sync --locked --check --offline --extra dev` makes no changes. Oracle environment:
`/tmp/rk-sim-u1-jjaffari-1e5706e`, external to the pristine `rk-sim-u1-pin` checkout,
CPython 3.12.14, 27 distributions; locked offline base-selection check passes. Full metadata
and lock digests are in [environments.json](environments.json); uv is 0.12.9. Metadata was
read with an isolated interpreter using `importlib.metadata`, **not** `run_oracle`,
`oracle_command`, the oracle program, or an import of rk-sim. This is local WSL software
availability, not designated-host/runner readiness or authentication of installed package bytes.
A missing/recreated `/tmp` environment or any drift requires rechecking; no install is scripted.

Generation will exclusively create A's ignored `tables/U3-rope-generation-v1/`, with
`inputs/`, `candidate/` and `receipts/`. The root is currently absent; the ignored `tables/`
parent is also absent and would be created by the human helper. A draft guard incorrectly
required that parent to exist; read-only preflight exposed it, and the proposed helper was
corrected before publication. No parent/output directory was created in A by this task.
Symlink ancestors, occupied output or non-directory parent refuse; there is no overwrite,
automatic resume or cleanup of a failed run.

The helper requires the human-supplied flag and full approved proposal commit. It runs
A's unchanged vendor generator twice in **separate isolated processes**, identical inputs
and one candidate destination. It requires exact `created: 48 files ...` then
`verified-identical: 48 files ...` statuses; saves stdout/stderr, command/exit receipts,
before/between/after source/input/environment preflights and exact candidate manifest digest;
and performs strict candidate support/generator validation. Any error stops with receipts
preserved. It never adopts, activates tests, commits or pushes, and never calls a retired
integration checkout or relies on rg on the human host.

Read-only preflight (actually executed without --proposal-commit before publication):

```sh
env -u PYTHONPATH -u MYPYPATH -u VIRTUAL_ENV -u PARAMS GIT_OPTIONAL_LOCKS=0 \
  /home/jjaff/AI-infra-simulation/rk-uarch-u3-a/.venv/bin/python -I -B \
  /home/jjaff/AI-infra-simulation/rk-uarch-u3-b/docs/reviews/U3-combined-freeze-proposal-v1/preflight.py
```

Future human invocation, **not executed** (replace the full commit placeholder with the
coordinator-reviewed publication; the package may instead live in primary):

```sh
env -u PYTHONPATH -u MYPYPATH -u VIRTUAL_ENV -u PARAMS UARCH_HUMAN=1 GIT_OPTIONAL_LOCKS=0 \
  /home/jjaff/AI-infra-simulation/rk-uarch-u3-a/.venv/bin/python -I -B \
  /home/jjaff/AI-infra-simulation/rk-uarch-u3-b/docs/reviews/U3-combined-freeze-proposal-v1/human_generate.py \
  --approved-proposal FULL_REVIEWED_PROPOSAL_COMMIT
```

## Complete audit, decision and placement plan — not performed

1. Preserve both process logs/statuses, complete candidate (expected 48 files), frozen
   inputs, exact environments, source commit/tree and candidate manifest digest. Require the
   same source/input identities and manifest in both runs. With A's explicit import context,
   run `scripts.vendor_rk --check --output-root <candidate>`, `tests.u2_refresh inspect
   <candidate>` and strict `load_inputs` against the proposed digest. `audit_candidate` must
   return adopted=false and rows=1008; no `--historical` or check_support=False substitute.
2. Run `scripts.u2_inputs compare <current-adopted> <candidate>` and retain the complete
   machine-readable comparison. Validate exact inventory, all seven precision combinations,
   1,008 unique query identities, 504/504 phase coverage, all sidecars/nominal model fields,
   component hashes and attribution. Verify all four refusal records completely, including
   type, boundary, message, execution marker, precision, callable/source and component hash.
3. Compare every old/new row by semantic key (component, model_id, full compute/KV precision,
   tp, full query), not list order or a sample. Compare all matrix/read/write counts, durations,
   duration method, null versus missing versus zero, IDs, contributors, omissions, scope,
   badges, shapes and sources. Expected: 1,008 unchanged rows, zero added/removed/changed,
   byte-identical fixtures/refusals and unchanged upstream sources/schema/lock, components,
   sidecars and all non-support staged inputs. Expected artifact differences are only the
   expanded support manifest, its input SHA256SUMS and enclosing MANIFEST.json. Unexpected
   metadata/environment or numerical changes stop for review; never hand-edit output or
   disguise discrepancies as deviations. Expected equality is not an already executed result.
4. Return the exact complete-candidate manifest, input digest, old/new audit and received
   process receipts to coordinator/Javid. Request explicit adoption of **that complete 48-file
   candidate**, naming old manifest `20eee19b...`, exact new manifest (not yet known), source
   `187fe3b...`, reason, approval/date and intended canonical destination
   `contract/vendor/rk-sim@1e5706e0ebfcc67c1a7333079a35b75f693e9963`. Preserve old artifacts in
   Git history and all prior input/review/report evidence unchanged. No cherry-picked rows,
   partial replacement, new synthetic marker, auto-refresh or fabricated adoption review.
5. After that separate approval, the human makes the complete protected artifact placement/
   commit in A. Existing `tests.u2_refresh.adoption_authority` requires a separately trusted
   ReviewRecord digest, Javid as reviewer, accepted/independent fields and the exact manifest
   as sole subject. Only a genuine human adoption record may satisfy that API; B creates
   none here. This artifact-adoption authority is not an independent U-REVIEW verdict or
   analytic report attachment. Preserve `tests/fixtures/u2_b/received-adoption-review.json`;
   propose a new record at `tests/fixtures/u3_rope/received-adoption-review.json` after the
   candidate exists and Javid supplies the actual decision.
6. Prepare an exact **human-owned adoption pin update**, once actual hashes exist, for
   `contract/tests/test_u2_historical_snapshot.py`: CURRENT_MANIFEST, REVIEW_SHA256 and
   the current review path only. Keep historical authentication and all strict assertions.
   Also separately review B-owned current-canonical pin updates in
   `tests/unit/test_u2_b_stage2_reference.py` (CURRENT_MANIFEST) and
   `tests/integration/test_u2_b_r202_public.py` (MANIFEST). Keep their historical fixtures,
   reference values and refusal/closure guards intact. These are future adoption-test changes,
   not a present support/tooling change; none of these test files is in the current support
   enumerator. Do not edit expected hashes to make an unapproved candidate pass.
7. Separately request human approval/installation/commit of A's one-file
   `docs/reviews/U3-RoPE-runtime-v1/protected-tests.patch` from `187fe3b...`, SHA256
   `4280f13077b703283d3e8237011f18bd6641ee9c4580337d8b822d5193613e26`. It only removes the
   28 admission skips, updates pending prose and renames their test; fixtures are unchanged.
   It remains unapplied and unapproved for installation by this proposal. Currentness does
   not activate those tests, and activating them does not adopt an artifact.
8. After human placement/activation and normal integration of peer main, verify unchanged
   complete support against this input digest (including newly added files). Any support or
   frozen-input change requires reconciliation and a fresh lifecycle before publication.
   Required final commands in A's own environment, with PYTHONPATH/MYPYPATH unset:
   `ruff check .`; `mypy src contract/uarch_contract scripts`;
   `mypy --no-explicit-package-bases contract/tests`; `lint-imports`;
   `python -m uarch_contract.generate --check`;
   `python -m uarch_contract.generate_rotary_v2 --check`;
   old `rkuarch.engines.protocol.generate(check=True)` and
   `python -m rkuarch.engines.protocol_v2 --check`;
   `python scripts/vendor_rk.py --check`;
   `python -m pytest -q -rs contract/tests --require-vendor`;
   focused `tests/rotary_v2`, activated rotary tests, `validation/reporting`, and legacy
   prepared/capture/table/report/public workflow regressions; then one `pytest -q` full
   integrated suite. Old/new schemas, both version routes and producer-disabled replay
   must pass. Keep capability skips explicit. Only after successful currentness, exact
   adoption, final checks and coordinator reconciliation may A perform a separate normal
   main push. Do not push the source-bound history while the old snapshot remains stale.

## Checks actually executed and remaining limits

This task executed source/ancestry/clean-state and hook inspection, complete support delta,
pure input staging/strict loading, all non-support input byte comparison, 36-file execution
closure inclusion, pristine upstream checks, locked offline environment checks, metadata-only
interpreter probes, Python syntax compilation and scoped Ruff. Final
[preflight receipt](preflight-result.json) records the read-only result. No runtime workload,
oracle command, generation helper, protected patch, adoption command or full suite ran.
No dependency installation, runner/container/server change, candidate simulator build/run,
new analytic report/corpus or independent review occurred.

Coordinator's 270 passed / 28 skipped focused run, 651 passed / 28 skipped / two expected
currentness failures, 102 scratch activated passes and 14 fault refusals remain inherited
coordinator results. A's full 1,656 passed / 57 skipped / two currentness failures remain
A's earlier run at 2791341, not a new execution here. The two strict-currentness failures
are pending regeneration/adoption, not waived by this proposal. The portability fix and
SR-C1 are in the reviewed source; historical B execution receipts retain their old bindings.

**Next human action:** first coordinator review of this exact proposal commit, source/tree,
input digest, environment checks and helper; then Javid confirms the exact source/input
freeze and two-run generation and personally runs the guarded helper. Return receipts and
manifest, then stop for the separate complete-candidate audit/adoption and protected-test
activation decisions above. Candidate hashes and actual review identities cannot be filled
in before those events. Nightly/runner work with Reza, independent review, v2 report
integration, fork choice/U0005/G2 and U3 closure remain separate pending work.
