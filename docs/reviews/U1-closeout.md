# U1 closeout — published implementation and validation evidence

**Prepared and accepted:** 2026-10-07. **Status: G1 APPROVED; U1 closeout ACCEPTED**
by Javid (@jjaffari), the recorded acting human owner/approver of both U1 lanes.
Implementation publication and validation are complete. Closeout commit, push and
`u01-end` tagging remain separate pending steps; no tag or closeout publication is
claimed here. No Reza approval is claimed.

## Final human approval

Javid explicitly authorized the coordinator on 2026-10-07:

> I approve G1 and accept the U1 closeout, including U0020. Record my approval and
> prepare the final documentation commit. Keep commit, push and `u01-end` tagging
> as separate steps.

This approves the gate and the complete closeout against implementation revision
`44559fb1672e4d3468b4b6fc930cfdf4b4c1e99e`, accepted ADRs/reviews, same-commit hosted CI
and cold-clone evidence under U0020. It authorizes preparing the documentation commit;
commit execution, push and tagging remain separate steps. The U2 obligations below
remain in force.

## Publication and artifact identity

The published and validated rk-uarch commit is
`44559fb1672e4d3468b4b6fc930cfdf4b4c1e99e` (2026-10-07), built on coordinator base
`89313eef20e6b252d235b40a680a1464c52c636a`. The closeout session began with clean HEAD
at that exact publication. Documentation changes remain local and uncommitted.

| Identity | Exact value |
| --- | --- |
| Contract version | `uarch-contract/0.1` |
| Upstream rk-sim pin | `1e5706e0ebfcc67c1a7333079a35b75f693e9963` |
| Adopted snapshot manifest SHA256 | `b3a575d0e3f27a4057678a2298609a580fd5a5e1dd858b0f4af086f2dc9e0e1d` |
| Full `scripts/vendor_rk.py` SHA256 | `4d2304002b262f2ee03dfe4f8fb338b350aacd80ea2488952849c416ee135317` |
| `ORACLE_PROGRAM` UTF-8 SHA256 | `9dd67d4883206f14b8a5a00fa3d0ced95bddaa395ba634d80e08a39813ea04fb` |
| Pinned oracle `uv.lock` SHA256 | `d984e55723326751ac3f888712f98462a525315ad4693691dbc3f2f5dc7f577c` |
| Verified oracle environment record SHA256 | `02ffc090d0411265faa165cb60b6cfc7db24e7ed5697b746bcfda72528c5308b` |
| Generation staging manifest SHA256 | `cb19332e9c1c3c88ad90bf6c0b8cdcf2d8f991b302d472fd5bfac2e497e0e8b0` |

The complete [20-file snapshot](../../contract/vendor/rk-sim@1e5706e0ebfcc67c1a7333079a35b75f693e9963/)
contains 864 oracle records and two unsupported-precision refusals. Its identity is the
upstream pin **plus manifest plus publication commit**, not the upstream pin alone.
[GENERATOR.json](../../contract/vendor/rk-sim@1e5706e0ebfcc67c1a7333079a35b75f693e9963/GENERATOR.json)
records CPython 3.12.14 and the 27-package pinned base-selection oracle environment.
The original generation used uv 0.12.9 with no default development groups or project
extras. Retained [environment inventory](U1-publication-records/oracle-environment.json),
[locked check](U1-publication-records/oracle-locked-check.log) and
[staging manifest](U1-publication-records/staging-manifest.json) identify those inputs.
This oracle-generation environment is distinct from the manual and CI test environments.

## Human acceptance, adoption and independent reviews

Javid accepted **complete U0001 and U0002**, including defaults, schema choices and the
narrow strict stub-source exception, on 2026-10-06 (America/Los_Angeles). The exact
[authorization and approved inputs](U1-acceptance-and-adoption.md) include:

> I accept the complete U0001 and U0002 proposals, including the stub-source exception,
> approve adoption of the identified snapshot, and authorize integration of the final
> publication proposal. Keep commit and push as separate steps, with commit comments
> covering them.

| Accepted input | SHA256 before acceptance annotations |
| --- | --- |
| [U0001](../decisions/U0001-the-integration-contract.md) complete proposal | `a4ddff1ec26e46f53e31f1221022d4361d3aee3d45f76a381a174f6a958951be` |
| [U0002](../decisions/U0002-the-vendored-snapshot-and-parity-discipline.md) complete proposal | `66eedb5ce47774c58de5a2d69b62a0828f3f55dd4e8dc999f87b464e7951804c` |
| Complete publication patch | `4c73a75e8fe548fe59919e76faa0179badd9554ad0a36b0753ed978cc5aacead` |

[U0019](../decisions/U0019-standalone-preparation-and-prepared-input-replay.md) remains
accepted architectural direction for standalone preparation and prepared-input replay;
concrete U0003 schemas and implementation are future work. Full U0001/U0002 acceptance
supersedes their historical pending-acceptance statements without rewriting their history.

Javid approved adoption of the complete reviewed snapshot together with its exact generator.
This was the first publication, not a refresh of an already published snapshot. His two
human generation logs show [created: 20 files](U1-publication-records/generation-first.log)
and [verified-identical: 20 files](U1-publication-records/generation-second.log).
The [classified comparison](U1-publication-records/snapshot-comparison.json) preserves
both earlier manifest identities, `4caea65f3c217bbb2030409833be6c67c15561552f8d9c9e179ac3ff82883284`
and `6b0d69c5737ba2b4cdbd8bce13ec860e4750f4008d9f4ee4fb8dc6db456d8304`:
only GENERATOR.json/MANIFEST.json changed and uv.lock was added; all oracle/refusal bytes
remain identical. No generation or selective artifact mixing occurred during adoption or
this documentation pass.

| Independent review | Final verdict and scope | Preserved report SHA256 |
| --- | --- | --- |
| [Lane A](U1-lane-A-review.md#verdict) | **ACCEPTED**, Stage 3: all 14 findings accounted for; applied changes have failing-without regressions; A-F9 remains a U-P3 obligation, A-F12's interim guard is discharged. | `6bca5ad174d7902b49f272493687800bff817d4f821c2cd38f78682e4631cd66` |
| [Lane B](U1-lane-B-review.md#updated-overall-lane-b-verdict) | **ACCEPTED**, after F3/F7 re-adjudication of the real replacement artifact and environment; F16's U2 deferral is accepted. | `30b51fa71f222f0efb6c7e05ceb817e74dbfde75ca3920e9d74554ad800c0246` |

Both reports assert reviewer independence. Their earlier failures, pending gates and
intermediate verdicts remain verbatim historical evidence. Lane A's accepted response
preceded replacement-snapshot validation; Lane B's final re-adjudication checked the real
replacement. Neither verdict is relabelled as review of later publication housekeeping
or this closeout. Current acceptance/publication/validation status is recorded here and
in the adoption record, separately from those verdicts.

## Published-revision validation

The [original cold-clone report](U1-cold-clone-evidence/report.txt), generated
2026-10-07T07:18:30.538132+00:00, records all eight requested checks and locked sync exiting
0 at the exact publication SHA. Commands below ran from the detached checkout root.
They are historical results, not a full-suite rerun for these prose edits.

| Exact command | Result | Original log |
| --- | --- | --- |
| `uv sync --locked --extra dev --python 3.12.14` | Passed; new virtual environment | [sync](U1-cold-clone-evidence/logs/sync.log) |
| `uv run --no-sync python -B scripts/vendor_rk.py --check` | Manifest, matrix and strict current compatibility verified | [vendor](U1-cold-clone-evidence/logs/vendor-check.log) |
| `uv run --no-sync pytest -q -rs contract/tests --require-vendor` | **379 passed**, no failures/skips | [contract](U1-cold-clone-evidence/logs/contract-tests.log) |
| `uv run --no-sync pytest -q -rs` | **385 passed**, no failures/skips | [full suite](U1-cold-clone-evidence/logs/full-tests.log) |
| `uv run --no-sync mypy src contract scripts` | No issues in 47 source files | [mypy](U1-cold-clone-evidence/logs/mypy.log) |
| `uv run --no-sync ruff check .` | All checks passed | [Ruff](U1-cold-clone-evidence/logs/ruff.log) |
| `uv run --no-sync lint-imports` | Two contracts kept, zero broken | [imports](U1-cold-clone-evidence/logs/lint-imports.log) |
| `uv run --no-sync python -B -m uarch_contract.generate --check` | Contract schemas fresh; read-only check | [schemas](U1-cold-clone-evidence/logs/generated-check.log) |
| `uv run --no-sync pytest -q tests/unit/test_prompt_sync.py` | **Four passed** | [prompt sync](U1-cold-clone-evidence/logs/prompt-sync.log) |

These corroborate the integrated-tree checks in the
[acceptance/adoption record](U1-acceptance-and-adoption.md#integration-and-validation).
Strict vendor verification includes current full-script/oracle fingerprints and required
locked environment metadata, not merely historical manifest integrity. No vendor or schema
regeneration was used for validation.

### Same-commit hosted CI

[GitHub Actions run 37585143201](https://github.com/kakoee/rk-uarch/actions/runs/37585143201)
completed successfully: created 2026-10-07T07:04:45Z, updated 07:05:16Z. The preserved
[job metadata](U1-cold-clone-evidence/logs/ci-jobs.log) binds every job to
`44559fb1672e4d3468b4b6fc930cfdf4b4c1e99e`; all eight jobs succeeded with no failed/skipped
jobs or steps. [Full job output](U1-cold-clone-evidence/logs/ci-log.log) identifies GitHub
Hosted Compute Agent, Ubuntu 24.04.5, image `ubuntu-24.04`, runner 2.337.0 and labels
`ubuntu-latest`. CI used Python 3.12.3 and `uv sync --extra dev`; it supplements rather
than duplicates the exact manual Python 3.12.14 locked-sync setup.

Executed checks passed: strict vendor verification, 379 contract tests, 385 Python tests,
two licence tests, lint, type checking, imports and schema freshness. Successful job/step
status also includes these **conditional no-ops**, as wired in
[ci.yml](../../.github/workflows/ci.yml):

| Job/step | Why no check ran |
| --- | --- |
| golden | No expected files |
| determinism | No golden scenarios |
| native | No native sources |
| perf | No performance baselines |
| ordering | No predictions |
| licences-and-patches / patches | No patches; the separate licence tests did execute |

No golden, engine determinism, native, performance, prediction-ordering or patch-application
coverage is inferred from these green statuses. Node.js 20 action deprecation warnings
were recorded; they did not fail the run. This documentation session uses the saved CI
evidence and does not trigger another run.

### Cold-clone host, isolation and clean checkout

Manual host: **ElfinKidsLaptop**, Ubuntu 24.04.4 LTS (Noble Numbat), x86_64.
Exact [kernel output](U1-cold-clone-evidence/logs/kernel.log):

```text
Linux ElfinKidsLaptop 6.6.87.2-microsoft-standard-WSL2 #1 SMP PREEMPT_DYNAMIC Thu Jun 5 18:30:46 UTC 2025 x86_64 x86_64 x86_64 GNU/Linux
```

System Python was 3.12.3; validation used CPython 3.12.14 (Clang 22.1.3), uv 0.12.9
(x86_64-unknown-linux-gnu) and git 2.43.0. The uv-managed base interpreter at
`/home/jjaff/.local/share/uv/python/cpython-3.12.14-linux-x86_64-gnu` was reused;
no virtual environment was reused. Exact versions and paths are preserved in the
[report](U1-cold-clone-evidence/report.txt) and [Python log](U1-cold-clone-evidence/logs/environment-python.log).

The runner created `/tmp/u1-cold-clone-rwaqeoco`, cloned directly from GitHub and checked
out the publication detached at `checkout/`. No local worktree/rk-sim checkout or unpublished
files supplied the clone. `UV_CACHE_DIR` selected a new empty `uv-cache/`;
`UV_PYTHON_INSTALL_DIR` selected `uv-python/`; `UV_PROJECT_ENVIRONMENT` selected the new
`checkout/.venv`. The runner strips inherited `VIRTUAL_ENV` (none was present in this run).
`UARCH_HUMAN` was unset throughout. See the [environment record](U1-cold-clone-evidence/environment.json)
and [archived runner source](U1-cold-clone-evidence/audit.py.txt).

Both [initial](U1-cold-clone-evidence/logs/initial-status.log) and
[final](U1-cold-clone-evidence/logs/final-status.log)
`git status --porcelain=v1 --untracked-files=all` outputs were empty.
`git diff --exit-code HEAD --` [exited 0](U1-cold-clone-evidence/logs/final-diff.log), and
[final HEAD](U1-cold-clone-evidence/logs/final-commit.log) was unchanged.
The manifest digest matched independently via
[sha256sum](U1-cold-clone-evidence/logs/manifest-sha256.log) and a
[Python assertion](U1-cold-clone-evidence/logs/manifest-assert.log).
Ordinary ignored environments/caches remained; no source edit, artifact regeneration,
commit, push or tag was part of that run.

Infrastructure failures are retained separately: the sandbox could not start because of
`/mnt/wslg/distro`; approved escalated commands were used. An initial unqualified system
`python` probe failed, while all requested uv-managed checks succeeded. See
[preflight evidence](U1-cold-clone-evidence/logs/preflight-sandbox-failure.log).

This was **WSL2, not a separate Linux machine**. Javid's already-approved U1-only exception
is recorded in [U0020](../decisions/U0020-u1-cold-clone-validation-exception.md), with his
verbatim authorization. The fresh WSL2 validation plus same-commit hosted Ubuntu CI replaces
the separate Linux-box check for U1 only. Future runner, hardware and performance-host
requirements remain unchanged.

### Durable evidence

[U1-cold-clone-evidence](U1-cold-clone-evidence/README.md) preserves the report, command index,
environment/authorization records and all 32 logs byte-for-byte. It also retains the original
runner as `audit.py.txt` and the original checksum manifest. The archive
[SHA256SUMS](U1-cold-clone-evidence/SHA256SUMS) checks the 38 copied evidence files at their
archived names. Original absolute paths remain provenance, not the only evidence location.
The virtual environment, checkout and uv cache are intentionally not copied.

## U1 evidence scope

The [how-it-works refresh](../how-it-works.md) links implemented contract, schema,
fidelity, provenance, hashing, vendor isolation and parity behavior to their tests.
No engine exists. Toy rows, synthetic mutants, arithmetic probes and frozen-oracle echoes
are contract/harness tests, never rk-uarch engine results or actual workload parity.
No real engine row/hash, golden-design badge/composite, engine stipulation count or measured
error band can be reported; those standing-refresh requirements are inapplicable to U1.
Engine L0/L0m/L1, worker/thread determinism, native/fork and hardware/performance validation
are likewise inapplicable. Null error remains unknown; energy is unverified and no model
badge is promoted by these checks.

## U2 obligations and later boundaries

U2 remains unstarted. Javid has approved G1; finish closeout publication and tagging
before kickoff. Load
[the kickoff record](U2-kickoff-obligations.md), accepted U0001/U0002/U0019, and
[U-P3](../prompts/U-P3-hardware-workload-and-the-analytic-engine.md) before implementation.

| Obligation | Owner and required outcome |
| --- | --- |
| U0003 preparation prerequisite | U0003 author settles versioned payloads, canonical content identity, scope/hardware binding, validation, fixtures and any public contract revision before U-P3/U-P4 diverge. Preserve standalone operation and authoritative supported imports. Re-estimate affected work, especially U2/U4. |
| B-F16 precision and adapter deferral | U0003 owns the component-precision interface; Lane B vendor/parity maintainer owns matrix support; Lane A U-P3 owns the prepared/imported-bundle adapter. Require a BF16-only npu-l4 PARAMS fixture using its declared supported peak, no substitute peak, and parity coverage of an actual prepared bundle. Generator changes require reviewed human refresh even at the same pin. |
| A-F9 MoE omission | Lane A U-P3 producer adds `MOE_OMISSION` when `request.model.n_experts > 0`, with a Mixtral regression. A reader-verifiable MoE indicator remains Javid's decision, not a field silently added in U1. |
| A-F1/A-F2 artifact checks | Lane A U-P3 resolves each condition path in the proposed HardwareSpec and requires complete stipulated-value equality; require `table.hardware_spec_hash == request.hardware_spec_hash == spec_hash(spec)`. Cross-check shared-SRAM existence/detail. Carrier parsing does not perform these checks. |
| A-F12 scope | Keep the accepted interim refusal before candidate execution for projections requiring replication/padding, retaining every fixture. Component-aware projection is future reviewed U-P3 work. Test physical rank-local correctness independently; keep legitimate contract request shapes supported. |
| Embedding accounting | Lane A exposes the actual graph/oracle discrepancy; Lane B preserves attribution/reporting; Javid receives the outstanding accounting/scope decision. Keep nominal U1 inputs. The approximately 6.54% nominal 8B embedding parameter share is not an operation/duration correction. Total absolute adjustments stay <=5% per fixture/channel and residual magnitude <=0.5%; no splitting, cancellation refund, dropped fixtures or widened tolerance. Ordinary over-budget differences fail; unsupported classification needs a documented scope incompatibility. |
| Actual U2 results and replay | Lane A delivers resolved workload preparation, U-C0, table production and implementation-identified parity; Lane B delivers report/badge/applicability behavior. U-C0 aggregate parity must meet the U2 +/-0.1% gate with each fixture's own params. Export/replay must agree byte-for-byte with producers disabled, supported external fixtures must run without producer dependencies, and stale hashes/incompatible hardware/incomplete coverage must fail. U1 self-tests satisfy none of these implementation exits. |

Later U-P19 still owns reader-side table-digest recomputation, component/spec identity,
TP/KV/initial-state/envelope checks and avoiding a second tp division. U3 still requires
registration of the `uarch` self-hosted runner, re-enabling nightly and a green manual run
before U-P5. U0020 waives none of those later obligations.

## Documentation-pass validation

On 2026-10-07, `uv run --no-sync pytest -q tests/unit/test_prompt_sync.py` passed all
four checks; `git diff --check` passed. Local links/anchors and whitespace in all six
new/modified Markdown files were checked. The nine command rows above were matched to
the retained command index and logs; the U0020 authorization quote matches the saved text.
All 38 copied evidence files match the originals and both checksum manifests (with the
archived runner filename mapping documented in the archive README).

All 211 tracked non-document files were compared byte-for-byte with publication HEAD,
including implementation, schemas, fixtures, generator and snapshot. Existing ADRs and
both accepted review reports are unchanged. The initial documentation session left the
Git index unchanged. After Javid's final approval, the coordinator updated approval/status
wording and staged only the 45 closeout documentation/evidence files for a separate commit.
The full suite was not rerun for prose changes; the 379/385 results above remain attributed
to published-revision evidence. No generation, commit, push or tag was performed.

### Final approval preparation checks

After recording Javid's final approval, all four prompt-sync tests passed again.
All 38 archived evidence hashes and 211 tracked non-document files were verified;
accepted U0001/U0002/U0019 and both reviewer reports remain unchanged. Exactly 45
closeout documentation/evidence files are staged; commit, push and tag are not performed.

The staged Markdown whitespace check passes. A whole-staged-diff whitespace check reports
eight pre-existing trailing-space lines in the verbatim `ci-log.log` and `lint-imports.log`
archive. They are retained intentionally to preserve original evidence bytes and checksums;
no authored-document whitespace defect is hidden or artifact content normalized.

## Remaining human and publication steps

1. Commit the accepted closeout documentation using the prepared comprehensive message.
   G1 and closeout approval are already recorded above; implementation publication is complete.
2. Push that documentation commit as a separate step and verify its hosted CI result.
3. After closeout publication and green CI, create/publish `u01-end` as a separate human
   step and record actual hours/retro under the sprint loop. No tag is created or implied here.

No U2 work, artifact regeneration, existing ADR policy change, commit, push or tag is part
of this documentation task.
