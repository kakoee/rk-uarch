# U4 ordinary runtime — correction and bounded cleanup proposal

This is one coherent **unapplied installation proposal**, succeeding reviewed commit
`12be87558c5a3312068ab1c5aa147fd95df232da`. It includes the original ordinary transition,
the Stage 1 corrections and only the obsolete U3/U4 native assurance cleanup. No protected
files or sealed deployment were installed. This is implementation evidence, not an
independent review, U4 closure or qualification.

The coordinator's `docs/reviews/U4-ordinary-runtime-independent-review-v1/` and the original
`U4-ordinary-runtime-implementation-v1/` package are unchanged. Their file digests are
recorded in [preserved-packages.json](evidence/preserved-packages.json). The inspected
publication baseline remains `12be875`; no later peer commit was present at the final fetch.

## Exact successor

Apply [transition.patch](transition.patch) as a complete change to the baseline in
[base-commit.txt](base-commit.txt), only after human protected installation approval.
Do not apply the v1 transition first. The successor includes its changes and preserves its
package. [transition.sha256](transition.sha256) identifies the patch;
[source-tree.txt](source-tree.txt) identifies the reconstructed source.

```sh
python docs/reviews/U4-ordinary-runtime-correction-v2/reconstruct.py /tmp/u4-successor-review
```

This exports the base and applies the proposal privately, then checks the resulting Git
tree. It does not install changes into the caller's checkout. `CLAUDE.md`, contract carriers,
schemas and tests, and the U0011 amendment remain inside this proposal.

## Response to Stage 1

| Item | Correction and result |
| --- | --- |
| F1 | Ordinary Python admission and native hardware admission require job overhead **32 cycles** and barrier latency **32 cycles**, returning `UnsupportedHardware` otherwise. Focused controls rebind real input hashes and exercise 16/32/64 for each parameter. The installed smoke checks both refusals through Python and debug/release binaries. No model law or hardware registry was added. |
| F2 | `rkuarch.verification.component` is the single active implementation of the seven shipped checker modules. The duplicate `validation/component` implementations are deleted; behavioral tests and remaining consumers import the shipped modules directly. No parity hashes, manifest or parity framework replaces the duplication. |
| F3 | Normal `cargo test`, and therefore existing `make native-test`, executes the shipping binary on ordinary production and fixture jobs, repeats each for byte determinism, and checks invocation/protocol/JSON refusals. A normal Rust unit test covers hardware capability refusals through `respond_with_test_mode`. Optional Python process tests remain additional coverage. Hosted native CI is unchanged and deferred under U0024. |
| A2 | The patch corrects the two build-spec status statements, the shared mapped-loader docstring, and the corresponding human-owned `CLAUDE.md` statement. Native and validation READMEs describe the actual simplified commands and removed machinery. |
| A1 | Documentation records that package version is the literal `0.0.1`, both run and replay require that installed version, build suffixes are unsupported, and this version does not distinguish builds. Compatibility policy is deferred until a version change requires it; no cross-version replay promise remains. |

## Cleanup and retained dependencies

The pre-deletion [caller inventory](evidence/legacy-callers-before.json) and
[import listing](evidence/imports-before.txt) informed the cleanup.
[Deleted operational files](evidence/deleted-operational-files.json) lists 64 files removed
in this correction, in addition to the seven duplicate checker implementations and the
startup/source-identity tests already deleted by v1. No remaining active Python module
imports the deleted operational modules; archived importers are named in
[remaining-historical-importers.json](evidence/remaining-historical-importers.json).

Removed:

- Ten Python native host/selector, record, component review, construction/build review,
  image adapter and historical runner modules. Shared bounded transport is retained in
  `rkuarch.engines.native.transport`, and its tests import it directly.
- Thirteen old `native/tools` candidate, identity-generation, frozen-input, corpus campaign,
  private adapter, container-guardian, startup-inventory and trusted-start tools. The two
  schema exporters remain.
- Capture tracing/monitoring, ordinary-build and EOF attestation/campaign orchestration,
  runtime campaign/receipt/resource-discovery, installation-identity machinery, campaign
  reduction/selection and their direct tests. The old public K2 launch test is replaced by
  ordinary binary coverage; no campaign is run.
- Rust external trust checks and their authority-specific assertions, dead historical
  protocol dispatch, and ignored file/directory campaign export hooks. Historical DTO
  parsers are test-only; shipping code accepts `/4` only.
- Current-source hash assertions in historical selection tests and source-attestation
  orchestration in `runtime_checks.py`. Its independent literal assertions remain.

Retained dependencies are specific:

| Retained helper/data | Remaining consumer and reason |
| --- | --- |
| `src/rkuarch/workload/mapped.py` | Ordinary run imports `validate_component_completeness`; `test_u4_a_mapped_loader.py` and mapper/contract tests use the historical pure loaders. No launch or host resolver remains there. |
| Historical mapped DTOs, fixtures, `admission.rs`/`accounting.rs` test paths | Contract semantic tests and Rust fixed-delay/component accounting and exact `/2` byte regressions still consume these shapes and laws. No ordinary authority path uses them. |
| `validation/component/{corpus,native_inputs,synthetic_carrier,consistent_carriers,transient_carrier,...}.py` | Named corpus, mapper-join, lifetime, issue and contract tests still use these independent synthetic inputs. They carry historical metadata, not current executable permission. |
| Historical `observations.py`, `observations_v2.py`, `transition_checks.py` | Existing carrier, lifetime and wrong-law tests exercise historical observation formats. Shared math now imports the shipped implementation. |
| `runtime_checks.assert_literals` and `runtime_literals` | `test_runtime_checks.py` retains real structural, numerical and literal discrimination against saved model-2 results, using the shipped checker. Source-pin/authority tests are removed. |
| `native_check.check_native` → `selection.assert_case` | Archived `U4-B-component-native-v1/{check_forgeries,run_private}.py` and
`U4-B-component-native-audit-v1/{projection_controls,supplemental}.py` probes consume the historical literal checker. Only pure assertions remain; six-call campaign orchestration is removed. |
| `native/test_register_linkage.py` | Existing dependency/license role verification remains. Only its obsolete README assertion changes. |

The historical corpus helper previously hashed its own source into old fixture metadata.
Redirecting its checker import therefore changed every regenerated historical bundle.
It now reads the recorded producer metadata from the existing immutable
`synthetic-component-jobs.json`; it explicitly identifies the archived author, not the
current helper. Frozen corpus and input identity tests pass without changing fixtures.
The existing Ruff configuration classifies `native` and `validation` as local namespaces
so deleting old modules does not force edits to immutable review probes.

Historical reports, receipts, oracle/golden artifacts, native testdata, hardware inputs,
old schemas and observation restrictions remain. Old operational probes require their
recorded Git implementation; preserving their evidence does not keep the retired framework
active. No analytic/table/report implementation, dependency or hosted workflow is changed.

## Ordinary use and dependencies

After complete human installation:

```sh
python -m rkuarch.engines.native.ordinary run --job job.json --executable /path/to/uarch-engine --output result.json
python -m rkuarch.engines.native.ordinary replay --job job.json --output result.json
```

Fixture jobs also require `--test-only`. Python preparation uses
`rkuarch.workload.ordinary.prepare_bundle` and `prepare_job`; execution/replay uses
`rkuarch.engines.native.ordinary.run` and `replay`. The executable accepts one EOF JSON
request via `uarch-engine --protocol uarch-engine/4 [--test-only]`.

Dependencies are Python 3.12+, the ordinary wheel and its existing locked libraries,
the selected native binary and its system loader/libraries, and input/output files.
Replay needs the Python installation and saved job/result, with no native binary or
mapping producer. No checkout, source archive, review, registry, host selector, build
receipt, compiler cache or startup loader is a runtime dependency.

## Executed checks and reused evidence

- One final affected Python integration selection: **1285 passed, 2 skipped in 201.44 s**.
  It includes ordinary unit/process tests, retained U4 mapper/loader/transport tests,
  `validation/component`, all contract tests with `--require-vendor`, and prompt sync.
  The two skips are the absent human L1 workings, not runtime gates. Full command and
  outcome: [final integration](evidence/final-integration.txt).
- Normal native Cargo test: **85 unit tests + 2 binary integration tests passed, 0 ignored**;
  [native test log](evidence/native-test.log). Release build and all-target Clippy passed.
- Default Python test discovery: **2485 collected**, no import errors. Ruff passed;
  mypy passed for 100 source files and 39 contract-test files; both import contracts held;
  three schema generators and both Rust carrier exporters passed `--check`.
- Targeted correction checks: 31 ordinary/checker tests, 22 literal/transport/prompt tests,
  and the 11 historical corpus/input identity rechecks passed. These are development
  selections; the single final affected selection above is the integration result.

The final installed smoke used a fresh non-editable wheel and copied existing Python
3.12.14, in offline read-only containers with only runtime/input/output mounts and binary
mounts for execution. No source, `.git`, docs, Cargo cache or review evidence was mounted.
The separate replay container had no binary mount. Production is **656000 ps**; fixture is
**121000 ps**; debug and release are byte-identical. All **26 negative controls** passed,
including unsupported overhead/barrier values in Python and both native builds. CLI
run/replay and producer-disabled replay passed. See [run](evidence/smoke-run.stdout),
[replay](evidence/smoke-replay.stdout), [wheel inventory](evidence/wheel-inventory.txt) and
[artifact digests](evidence/artifact-digests.json). Ten task-created containers were removed
by exact full ID; [cleanup](evidence/container-cleanup.json) confirms their absence.
No label sweep, prune, new image/tool installation or historical campaign ran.

Reused explicitly, not rerun: v1 and Stage 1 hand-derived timing, the broader reviewer
hardware sweep outside the two restricted parameters, detailed process/grandchild probes,
and unaffected analytic/table/report checks. Transport implementation is unchanged apart
from its `/4` default and docstring; its current bounded I/O/framing tests ran again.
Mathematical checker bodies are unchanged from the reviewed shipped implementation; only
consumer imports change. The new final selection exercises those shipped bodies directly.
Historical source-attestation or campaign outcomes are not attributed to the new path.

During edits, focused checks caught integer/float normalization in a new test input,
an incomplete hardware projection in its Rust counterpart, shared collection imports
removed with trust scaffolding, historical self-hash fixture coupling, and lint namespace
classification. Those were corrected. Retained intermediate Python failure output is
explicitly nonzero; the final results above supersede it for this source. No exhaustive
mutation campaign was added.

## Limitations and approval boundary

The ordinary environment is trusted and user-controlled. A-F3 remains **retired by scope
change**, not passed; its stopped startup-substitution experiment was not retried or
transferred. Historical staging/trace/container findings remain historical findings.
The package-version replay limitation is as stated in A1. No new runtime defect remained
in the exercised scope, and this is not exhaustive capability validation.

Actual human L1 workings/review (`H-L1-DMA-01`, `H-L1-GEMM-01`), the historical `/2`
restriction, U0024, U4b/reference readiness, G3a and qualification remain unresolved where
previously unresolved. Protected installation remains human-owned. No runtime approval
framework is reinstated, and no sealed deployment is modified.
