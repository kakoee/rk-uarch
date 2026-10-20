# U4 ordinary-runtime simplification — independent review, Stage 1

Reviewer: a fresh session that authored none of the proposal, its package or earlier A/B work.
This is evidence, not a verdict. It does not install the proposal, approve U4/G3a closure,
qualify anything or open another review cycle. It assesses the proposal against the approved
simplification scope only. The retired startup-assurance requirement (A-F3) was not retried,
transferred or reconstructed.

_Status: Stage 1 complete (2026-10-19). The review is unstaged and uncommitted._

## Findings at a glance

**No blocking finding.** On the exercised selection, installed execution, binary-free replay,
semantic admission, result validation and process handling behave as specified.

| # | Severity | Behaviour | Blocks |
| --- | --- | --- | --- |
| F1 | NON-BLOCKING (medium) | `--test-only` admits hardware outside the shipped independent checker's law domain. Native treats `job_overhead_cycles` and `barrier_latency_cycles` as parameters; the checker hardcodes 32 for both. | Any claim that the test-only path supports arbitrary fixture hardware, and parameter-varied verification of those two parameters through the ordinary consumer. Production is unaffected (hash pinned; fails closed). |
| F2 | NON-BLOCKING (low–medium) | The shipped checker copy has no parity guard. Default tests exercise only the `validation/` copy. | Nothing now (copies are AST-identical). This is a gap in regression protection. |
| F3 | NON-BLOCKING (low–medium) | No automatically run test executes the shipping `/4` binary path: there is no Rust test, and the Python process tests skip unless `ORDINARY_NATIVE` is set. | Nothing now (executed manually here and by the author). This is a gap in regression protection. |
| A1 | Advisory (not an acceptance requirement) | `package_version` is a schema literal `"0.0.1"` and must equal the installed version for both run and replay. | — |
| A2 | Advisory (documentation) | Four existing statements will contradict installed behaviour once the transition is installed. | — |

## Subject and identity (executed)

| Item | Value | Result |
| --- | --- | --- |
| Proposal commit | `12be87558c5a3312068ab1c5aa147fd95df232da` (fresh GitHub clone in session scratchpad) | pinned |
| Base | `669bdb0f7032e8955dbd0daaea059b733d4aa250` | matches `base-commit.txt` |
| `transition.patch` SHA-256 | `80224d607fea488ee36ded7198a861941f05a41b5e7bf3280369514ee3e48527` | matches `transition.sha256` |
| Reconstructed tree | `b0f1755e52bfe1a3a7ee6f3b37da77a4f8ce3ac0` | reproduced twice: by `reconstruct.py` into a new directory, and by an independent index-only `git apply --cached` |

File and line references below are to the reconstructed tree `b0f1755e`.

## Method and environment

* **Checkouts.** Fresh clone and disposable reconstructions under the session scratchpad.
  The author's `/tmp/rk-uarch-simplify*` artifacts were only read, for byte comparison.
  The primary checkout gained this directory and nothing else. A `git fetch origin` early in
  the session advanced that checkout's `origin/main` tracking ref to `12be875`; the working
  tree, index, branches and HEAD (`669bdb0`) are unchanged.
* **Wheel.** `uv build --wheel --offline` (uv 0.12.9) from the reconstruction produced
  `3309b119…6c41`, byte-identical to the author's wheel.
* **Native.** Built in the accepted image `sha256:e9f69f41…0523` (rustc/cargo 1.99.0), using the
  offline Cargo cache read-only, `--locked`, and a reviewer-owned target directory. Results:
  debug `92b6b891…040b`, release `6b4c3a2e…2e42`, byte-identical to the author's binaries
  (not required; noted as corroboration). Probe: [native_build.py](probes/native_build.py).
* **Runtime.** A copied uv CPython 3.12.14 with a stdlib venv. Locked dependencies were
  installed via `uv sync --frozen --offline --no-dev --no-install-project`, then the wheel
  `--no-deps`, non-editable, with no `.pth` hooks.
* **Containers.** The local `python:3.11-slim` image (`sha256:93584440…6634`) served only as a
  userland, run with `--network none --read-only --cap-drop ALL`. Mounts: runtime, inputs,
  mutants, probe and outputs. No source, `.git`, cache or docs was mounted. The run container
  had the two shipping binaries; the replay container had none.
  [smoke_driver.py](probes/smoke_driver.py) created 11 containers in total, all removed by
  exact 64-hex ID ([ledger](receipts/containers-ledger.jsonl)). No label sweep or prune was
  run, and the two pre-existing containers were left untouched.

## What holds — new execution in this review

1. **Installed execution outside a checkout, using the shipping CLI and binaries.**
   `python -m rkuarch.engines.native.ordinary run` was run with the release and debug
   `uarch-engine`. The production job was assembled through the *installed* `prepare_bundle`/
   `prepare_job` API from the existing mapped fixture point ([prepare_inputs.py](probes/prepare_inputs.py)).
   Production: **656000 ps**, `component_only`. Four test-only fixtures, converted by the
   reviewer's own `/3`→`/4` development migration: 121000 / 147000 / 121000 / 146000 ps, all
   `verification_only`. Debug and release output bytes were equal for all 5 positives and all
   21 mutants. All rkuarch/uarch_contract modules loaded from the runtime site-packages.
   ([run report](receipts/smoke/run.stdout): 56/56 checks.)
2. **Binary-free saved replay.** A separate container without `/native` replayed all 5 saved
   results through the CLI. No `rkuarch.mapping` module was imported.
   ([replay report](receipts/smoke/replay.stdout): 23/23 checks.)
3. **Independent timing derivation.** [derive_timing.py](probes/derive_timing.py) imports
   nothing from the project. It applies the U0011 E3/E4 laws to the job's hardware values:
   DRAM latency t_cl+t_rcd+t_rp = 48 cycles; refresh-derated channel service
   256 B/(125 GB/s·3550/3900) = 159744/71 ps → 2250; zero-hop NoC; port FIFO; 32-cycle
   overhead; staging 1; WS fill/steady/drain M+K+N−2 = 513; output 1. Duration 656000 ps,
   all 8 milestones and the attribution split (compute 515000 / memory 104250 / noc 4750 /
   overhead 32000) match both binaries ([receipt](receipts/derive_timing.txt)).
4. **Semantic admission at both layers.** Mutants were generated with all integrity hashes
   recomputed, so that the targeted law is what fires ([make_mutants.py](probes/make_mutants.py),
   [manifest](receipts/smoke/mutants-manifest.json)). Python and native both refused, with
   the expected codes:
   * non-production hardware under production invocation (`UnsupportedHardware`);
   * clock ratio 2 (`UnsupportedFrequency`);
   * steady state, fixture-resident state and priming 1 (`UnsupportedInitialState`);
   * SRAM capacity (`SramCapacityExceeded`), live buffer alias (`LiveBufferAlias`) and a
     dropped producer dependency (`InvalidDependency`);
   * fractional bytes; fp8; NoC fidelity 1; model version 1; package version 0.0.2;
   * a transport fixture relabelled as production (`UnsupportedCheckpointScope`);
   * a historical `/3` job (`UnsupportedProtocol`); an unknown field; a truncated job; a
     duplicate key; a stale hash.

   A non-canonical saved job is refused by Python. The binary parses it, which is consistent
   with EOF JSON transport. Test/production invocation must match explicitly at both the CLI
   and the binary (`AdmissionMismatch`).
5. **Result identity, and that independent checking is load-bearing.** Replay refused each
   of these: a cross-job result, a changed result package version, a non-canonical result,
   an empty result, and a test result replayed without `--test-only`. The decisive case is a
   **self-consistent wrong-law result**: native output for 16-cycle-overhead hardware,
   relabelled with the production job hash and admission. Structural `validate_result`
   **accepts** it; the shipped `check_v3` refuses it ("mechanism duration"), and therefore
   `replay` refuses it, also under `PYTHONOPTIMIZE=2`. The checker is wired in and catches
   what structure alone does not.
6. **Process handling** ([transport_probe.py](probes/transport_probe.py), [receipt](receipts/transport_probe.jsonl)):
   * a hang with a grandchild, and an exited child whose grandchild still holds stdout:
     `Timeout`, process group killed, 0 survivors;
   * stdout and stderr caps enforced;
   * status 3, 0+stderr and 2+stdout give `ProtocolViolation`; a valid refusal decodes; an
     unknown refusal code is a violation;
   * SIGKILL and status 1 give `OperationalFailure`; a non-executable file gives `SpawnFailure`;
   * through the CLI, operational failures exit 2 and never write the output file;
   * no failure path left a survivor.
7. **Packaging.** Compared with the base wheel, the new wheel drops exactly the 10 historical
   host/review modules and adds the ordinary modules, schemas and seven checkers
   ([receipt](receipts/wheel_vs_base.txt)). No shipped module imports an excluded one. The
   `uarch` console script still starts from the wheel ([receipt](receipts/console_scripts.txt)).
   The seven checkers are AST-identical to their `validation/` originals apart from the
   import prefix ([receipt](receipts/checker_ast_parity.txt)).
8. **Static checks on the exact tree.** Ruff, both mypy commands, import-linter, the three
   schema `--check`s and `export_ordinary.py --check` all exit 0
   ([receipt](receipts/static_checks.txt)). The proposal's ordinary tests pass 21/21 with
   each of the reviewer's binaries ([receipt](receipts/ordinary_tests_with_binary.txt)).
9. **No weakened semantics, dummy identities or historical changes.**
   * I compared `OrdinaryBundle`/`OrdinaryJob` with `MappedBundle`/`MappedEngineJob`+`admit()`,
     and the Rust `validate_inner` ordinary branch with the trust branch. Only the
     profile/registry/case joins were removed.
   * Retained: production hash, component scope, cold/no-priming, ratio-1/1 GHz clocks, the
     fixed-delay refusal, resources, owners, fidelity and precision, plus native capacity
     limits. Added: a result-protocol binding.
   * No path under golden, fixtures, historical schemas, native testdata or carriers,
     L3 predictions, third_party, the Python/Cargo manifests or the lockfiles changed.
     Added lines contain no placeholder hashes ([receipt](receipts/change_inventory.txt)).
10. **Retired tests.** The three deleted test files and the trimmed
    `test_installation_identity.py`/`test_stage2_selection.py` assertions are startup-assurance
    and source/ADR-pin checks; their own docstrings exclude them from behavioural scores.
    No behavioural law test was removed. The coverage gaps that remain are F2 and F3.

## Findings

### F1 — Test-only capability is wider than the shipped checker's law domain (NON-BLOCKING, medium)

* **Where.** `native/crates/uarch-engine/src/component_admission.rs` `hardware_model` pins
  channels/request bytes (:1469) and the 256×256 array (:1475) as `UnsupportedHardware`, but
  reads `job_overhead_cycles` (:1513) and `sync.barrier_latency_cycles` (:1520) as parameters.
  `src/rkuarch/verification/component/observations_v3.py:120` and `:128` hardcode 32 for
  both. `contract/uarch_contract/ordinary.py:88-92` restricts hardware only for production.
  Before this transition, test hardware needed a registry entry plus a reviewed profile; every
  registered spec available in testdata uses 32/32/256, so the mismatch was latent and is
  now reachable.
* **Reproducer.** [hw_sweep.py](probes/hw_sweep.py), [receipt](receipts/hw_sweep.jsonl),
  [barrier detail](receipts/barrier_detail.txt), and the smoke `observations` entry. Run the
  production component with `--test-only` and `job_overhead_cycles` 32→16 (all hashes
  recomputed):
  `uarch-engine --protocol uarch-engine/4 --test-only` returns status 0 with **640000 ps**.
  `python -m rkuarch.engines.native.ordinary run --test-only …` exits 2 with
  `mechanism duration`. On the transport fixture, barrier 32→16 gives a native barrier of
  13334 ps (16 NoC cycles) and the same consumer refusal. The 128×128 array is refused up
  front (`UnsupportedHardware`). Operand rate, DMA rate, NoC latency, t_cl and DRAM bandwidth
  variants agree between native and checker.
* **Expected vs actual.** Expected: capability admission and independent checking agree on
  the admitted domain. The binary should either refuse hardware it cannot have checked (as it
  already does for the array), or produce results the shipped checker validates. Actual: the
  binary admits and simulates; the consumer refuses with a message that blames an engine law
  violation.
* **Requirement.** U0011 amendment: "Preserve model/capability admission, actual input and
  result validation, independent tests"; capability validation is kept without an inventory.
* **Severity / blocks.** Non-blocking for ordinary production execution: production hardware
  is hash-pinned, and the outcome fails closed. It blocks any statement that the test-only
  route supports arbitrary fixture hardware, and its use for verification that varies these
  two parameters. A direct-binary result on such hardware is unchecked (`verification_only`).
* **Minimal correction.** Add `job_overhead_cycles == 32` and `barrier_latency_cycles == 32`
  to the existing native `hardware_model` capability pins, mirrored in `OrdinaryBundle` if
  desired. If those values are meant to be parametric, have the checker read them from the
  job; that changes the stated E3 law and needs human semantic acceptance.

### F2 — Shipped independent checker is an unpinned duplicate (NON-BLOCKING, low–medium)

* **Where.** `src/rkuarch/verification/component/*.py` (7 runtime copies) versus
  `validation/component/*.py`. Every behavioural checker test (for example
  `test_f5_mechanism_duration.py`, `test_phase_laws.py`, `test_matrix_order.py`) imports the
  `validation` copy. Only `tests/native/test_ordinary_process.py` (native-marked, skipped
  without `ORDINARY_NATIVE`) touches the shipped copy. The removed source pins used to bind
  checker bytes; nothing replaces them for the copy users actually run.
* **Reproducer.** [checker_drift.sh](probes/checker_drift.sh), [receipt](receipts/checker_drift.txt).
  Change `("compute_overhead", 32)` to `31` in the shipped copy only. With test-fast markers,
  23 tests pass. With all markers and no binary, 23 pass. Only with `ORDINARY_NATIVE` set does
  `test_positive_and_replay[False]` fail. At runtime this drift would reject every production
  run and replay. After restore, 32 pass.
* **Expected vs actual.** Expected: the default suite fails when the runtime checker diverges.
  Actual: it passes.
* **Requirement.** Normal build/test discipline; "Keep independent mathematics … discriminating
  faults" applies to the code that ships.
* **Severity / blocks.** Non-blocking. The copies are identical today. This is a gap in
  regression protection.
* **Minimal correction.** Keep one source: have `validation/component` import from
  `rkuarch.verification.component`, or add a default-suite parity test such as
  [checker_ast_parity.py](probes/checker_ast_parity.py).

### F3 — Shipping `/4` binary path has no automatically run test (NON-BLOCKING, low–medium)

* **Where.** `protocol.rs::respond_with_test_mode`, `component::execute_ordinary`,
  `component_admission::validate_ordinary` and its `ordinary` branches (including the
  `CARGO_PKG_VERSION` identity check at :585), and the `main.rs` argv handling. No Rust test
  references them; Rust tests call `respond()` only for `InvalidJson` and for
  `UnsupportedProtocol` on `{}`. `make native-test` (Makefile:25) is plain `cargo test`.
  `tests/native/test_ordinary_process.py:20` skips unless `ORDINARY_NATIVE` is set, and no
  Makefile or CI target sets it.
* **Reproducer.** The grep results in this review, and the F2 drift run (the native-marked
  file is skipped or deselected in both default modes).
* **Expected vs actual.** Expected: one positive and the key refusals of the shipped
  production path run under normal `make` targets. Actual: they run only when someone does so
  manually (the author's 23-pass run; this review's smoke).
* **Requirement.** "Preserve … normal build/test discipline"; the U0011 amendment keeps
  saved-input replay and fresh-process/debug-release determinism tests.
* **Severity / blocks.** Non-blocking. Behaviour is correct in executed evidence; this is a
  gap in regression protection.
* **Minimal correction.** Add a Rust unit test of `respond_with_test_mode` on one production
  and one fixture `/4` job (positive, `AdmissionMismatch`, `UnsupportedHardware`), or have
  the native test target build the binary and export `ORDINARY_NATIVE`.

### A1 — Package version is a literal that locks replay (advisory)

`contract/uarch_contract/ordinary.py:33` (`Literal["0.0.1"]`),
`src/rkuarch/engines/native/ordinary.py:64` and `component_admission.rs:585`
([probe](probes/version_lock.py), [receipt](receipts/version_lock.txt)). Simulating an
installed 0.0.2 makes replay of a valid saved result fail with `EngineIdentityMismatch`, and
a local build identifier `0.0.1+g12be875` is refused by the schema. Consequences:

* the U0011 amendment's optional build-time commit identifier cannot be recorded;
* any version bump needs a protected contract change, and the newer install refuses (never
  silently accepts) earlier saved `/4` jobs and results;
* in practice `0.0.1`, unchanged since 2026-09-29, does not distinguish builds.

Engine `native-stage/2` and model `native-intervals/2` do carry meaning. No action is
required by the approved scope; a decision will be needed at the first bump.

### A2 — Statements that will contradict installed behaviour (advisory)

* `CLAUDE.md:18` and `docs/build-spec.md:983`: "native … planned".
* `docs/build-spec.md:1302`: "Native is planned, not yet implemented".
* The `src/rkuarch/workload/mapped.py:1-6` docstring (host-owned authority, build receipts).
  The ordinary path now imports this module.

CLAUDE.md is human-owned, and the proposal correctly left it alone.

## Informational observations

* After a *successful* exchange, a descendant that has detached from all pipes survives;
  failure paths kill the whole group (transport receipt, case 13). The shipping binary spawns
  no processes (no `Command`, fork or thread spawn in `uarch-engine/src`), so ordinary use is
  unaffected.
* Native `InternalError` exits 1 (operational). Every other native refusal code is in the
  consumer's `CODES` (regex scan of the Rust sources).
* The Python CLI reports every failure as exit 2 with one line of text. The deadline is fixed
  at the 30 s default with no CLI override, which is a usability point only.

## Inherited evidence (inspected, not re-executed)

* **Native `cargo test`: 90 passed, 5 ignored; Clippy clean.** Relevant because the author's
  build source `native/` is identical to this reconstruction (only a `__pycache__` differs)
  and my binaries are byte-identical ([receipt](receipts/inherited_native_evidence.txt)).
* Final affected Python regression: 1470 passed, 3 skipped (two absent human L1 workings and
  the historical B native selection). Environment recheck: 153 passed. Prompt sync: 4 passed.
  The author's initial nonzero broad run remains recorded as nonzero; its failure scope is
  limited to retired source/ADR pins and Git-dependent checks covered by the recheck.
* These obligations remain outside ordinary execution and are not affected by this review:
  `H-L1-DMA-01` and `H-L1-GEMM-01`, the historical observations `/2` restriction, U0024,
  U4b/reference readiness, G3a and qualification.

## Limitations

* One host (WSL2, Linux 6.6) and one accepted build image; no hosted CI was polled.
* No hostile-environment or startup-substitution testing; the scope is a trusted,
  user-controlled Python environment.
* The hand derivation covers one small production case. The fixture cases rely on
  debug/release agreement and the shipped checker.
* The hardware sweep varies one parameter at a time and is not exhaustive. Refusal-code
  coverage comes from a regex scan.
* Mutant expectations are the reviewer's own. One expectation name was widened after
  observation (`ArtifactHashMismatch` for a stale job hash, still a refusal).
* One self-inflicted probe artifact: the first drift run left a stale `.pyc` in the
  disposable tree (same-size, same-second restore), which produced one spurious failure.
  The probe now disables bytecode and the receipts are from the corrected runs.
* The full Python suite, native campaigns and historical mutation campaigns were not
  repeated, as instructed.

---

## Bounded successor recheck — 808076a (2026-10-19 local)

**Verdict: no blocking runtime defect found in this bounded selection. F1 and F3 are
resolved; F2's duplication is resolved, but its regression-coverage concern is only partly
resolved. One non-blocking residual checker-coverage finding is described below, including
a concrete test-coverage loss associated with cleanup. A1/A2 are handled.** No proposal
was installed or fixed, and this report and its new evidence remain unstaged/uncommitted.

**Attribution:** the session writing this appendix also authored successor `808076a`.
This is an author recheck, not a fresh independent review or a substitute for one. The
Stage 1 report above retains its original authorship and claims. Its original **20,684
bytes** are preserved exactly (SHA-256
`81da67502129a60d3d73007c88d15147ae96dd9ecf3e5e2b2308656c75f7ccac`). New probes and receipts
are isolated under [recheck-808076a/](recheck-808076a/).

### Pinned subject and reconstruction

A fresh local clone was detached at **`808076a8f1786f00ef9e3cd0de6ab8f2adea83ad`**.
I began with its correction package README, `verification.json` and `reconstruct.py`.
The complete successor patch was applied to its recorded base
`12be87558c5a3312068ab1c5aa147fd95df232da`; the v1 patch was **not** applied first.
The patch SHA-256 is `b0de563bc3a6433b205649b3ed4db2861856636629dc715a18ff264f6eda4da4`,
and reconstruction reproduced tree `9a86cab622504e68746534c94e93b659cacf794d`.
Moving main was neither reviewed nor fetched. A separate v1 reconstruction supplied the
exact comparison tree, `b0f1755e52bfe1a3a7ee6f3b37da77a4f8ce3ac0`.
All temporary sensitivity mutations were restored; a final index-only tree calculation
reproduced the successor tree again. [Integrity receipt](recheck-808076a/receipts/final-integrity.json).

### Disposition and sensitivity checks

| Item | Disposition | Executed evidence |
| --- | --- | --- |
| F1 | **Resolved.** Python and native require overhead/barrier 32/32 and explicitly refuse unsupported values. No expanded hardware domain is claimed. | Existing Python controls cover 16/32/64 for each parameter. Removing only the Python capability check gives **4 failed, 2 passed**; restoration gives **6 passed**. Removing only the native pin makes its focused regression fail because an unsupported input returns success; restoration passes. The normal binary positives still give 656000/121000 ps. [Python controls](recheck-808076a/receipts/python-controls.json), [native controls](recheck-808076a/receipts/native-controls.json). |
| F2 | **Single implementation corrected; regression concern partly open.** All seven active checker implementations are under `rkuarch.verification.component`; duplicate `validation/component` files are gone. Remaining behavioral consumers import the shipped implementation. | Changing shipped `phase_laws` overhead 32→31 fails its positive test. Changing the shipped model-2 barrier law 32→31 fails **3 of 4** saved-result tests; restoration passes. However, the original compute-overhead drift still survives the focused default selection; see R1. No hash/parity framework is required or proposed. |
| F3 | **Resolved.** The existing native target discovers process tests that spawn `CARGO_BIN_EXE_uarch-engine`, exercise production and fixture `/4`, repeat bytes, and check invocation, JSON and protocol refusals. | Host `make -n native-test` expands to the unchanged Cargo command. Executing that exact recipe in the accepted image passes **85 unit + 2 binary integration tests, 0 ignored**. Flipping the shipping `main.rs` invocation flag causes the binary positive regression to fail; restoring it gives **2 passed**. [Recipe](recheck-808076a/receipts/make-native-test-expansion.txt), [normal run](recheck-808076a/receipts/normal-native-test-recipe.txt), [broken entry](recheck-808076a/receipts/f3-shipping-invocation-broken.txt), [restored](recheck-808076a/receipts/f3-shipping-restored.txt). |
| A2 | **Handled.** The two build-spec statements, the corresponding human-owned CLAUDE statement, and the shared mapped-loader docstring no longer describe native as unimplemented or ordinary execution as build-receipt/host-authority dependent. | Read-only statement checks and shared-loader AST comparison. These changes remain in the unapplied proposal. [Receipt](recheck-808076a/receipts/docs-packaging.json). |
| A1 | **Handled honestly.** Documentation states literal package version `0.0.1`, same-installed-version run/replay, unsupported build suffixes, and inability to distinguish builds. Compatibility policy remains deferred until a version change. | Verified the statements against `SoftwareIdentity` and the installed-version equality check; reused Stage 1's version-lock evidence. No new compatibility framework is requested. [Receipt](recheck-808076a/receipts/docs-packaging.json). |

The accepted native image does not contain `make`: the initial direct attempt exited
**127**, and its container was removed. This is retained in
[normal-make-native-test.txt](recheck-808076a/receipts/normal-make-native-test.txt).
The successful execution was the exact host-expanded Cargo recipe, not a claimed
successful `make` invocation inside that image. No dependency or tool was installed.

### R1 — residual checker regression coverage (NON-BLOCKING)

There are two bounded witnesses, both restored afterward:

1. **Original F2 drift remains undetected by the focused default tests.** Changing only
   `("compute_overhead", 32)` to `31` in the shipped `observations_v3.py` leaves **57 tests
   passing** (ordinary unit tests plus phase, runtime, issue and matrix checker tests).
   The default model-2 saved-result fixture `sr2-v3` contains DMA, unicast and a barrier,
   but no compute task. The old `/2` observation tests exercise a distinct historical
   implementation. With `ORDINARY_NATIVE` set, the existing optional process test catches
   the drift: **1 failed, 8 passed**, with production rejected for `mechanism duration`.
   Restored process tests: **9 passed**. The complete default suite was not rerun; this
   statement concerns the selected tests and inspected imports/fixtures.
   [Default drift](recheck-808076a/receipts/f2-original-compute-drift.txt),
   [process detection](recheck-808076a/receipts/f2-original-drift-with-process.txt).
2. **Cleanup removes a useful consumer-wiring assertion without an equivalent replacement.**
   Deleted `tests/unit/test_component_runtime.py::test_independent_checker_is_mandatory_for_valid_saved_response`
   explicitly tested that the former consumer invokes the independent checker. That
   particular runner is retired, but invoking independent validation is a retained
   requirement. Temporarily disabling only `ordinary.consume`'s `check_v3` call leaves
   **31 ordinary unit/process and saved-result tests passing**, even with a real binary.
   The process test's wrong-law control calls `check_v3` directly; its `consume` mutants
   fail structural validation, so neither detects this disconnection. Restoration also
   yields **31 passed**. [Probe](recheck-808076a/probes/cleanup_wiring_control.py),
   [disabled](recheck-808076a/receipts/cleanup-checker-call-disabled.txt),
   [restored](recheck-808076a/receipts/cleanup-checker-call-restored.txt).

This is a **regression-protection gap**, not evidence that the present consumer bypasses
checking or produces an incorrect result. Its implementation is byte-identical to reviewed
v1 and still calls the shipped checker. Stage 1's self-consistent wrong-law result showed
that call rejects what structural validation alone accepts. A small default saved-result
regression covering a compute case and a structurally valid wrong-law result through
`consume` would address these witnesses. No source hashes, authority checks, campaign or
new framework is needed. No implementation change was made during this recheck.

### Cleanup assessment

**No concrete runtime/import/packaging regression was found. The concrete coverage loss
is R1(2); therefore it would be inaccurate to describe every deleted test as enforcing
only retired requirements.** The deleted runtime test file mixed authority/startup/source
checks with framing, result binding, producer-disabled consumption and checker invocation.
Framing, binding, ordinary replay and numerical tests remain, but the invocation assertion
was not carried over effectively. [Deleted test functions](recheck-808076a/receipts/deleted-test-functions.json).

The diff from reconstructed v1 stays within the native assurance transition and its
callers/tests, the requested documentation, and packaging/lint adjustments needed for the
deletions. No unrelated analytic, table, report or provenance implementation, dependency,
lockfile, hosted workflow, hardware input, golden artifact, historical mapped schema or
native testdata changed. **6,196 historical review files** present in v1 remain byte-exact.
The seven shipped checker bodies are unchanged; their former duplicates are deleted.
[Scoped inventory](recheck-808076a/receipts/inventory.json),
[exact correction paths](recheck-808076a/receipts/correction-changes.txt).

Shared functionality was checked explicitly:

- The ordinary Python runtime is byte-identical to v1; transport changes only its docstring
  and default protocol `/3`→`/4`. The ordinary caller already passes `/4` explicitly.
  Existing transport tests ran in the **71-pass** initial focused selection.
- Shared mapped-loader code is AST-identical after excluding its module docstring.
  The Rust runtime mechanics are unchanged; its diff removes test-only trust plumbing,
  while the normal native suite still exercises historical timing/accounting and frozen
  `/2` byte checks. [Native diff](recheck-808076a/receipts/shared-native-diff.txt).
- Default Python discovery collects **2,485 tests with no import errors**. Active-code
  import scanning finds no references to deleted Python modules. The retained old DTOs,
  literal corpus and historical observation helpers have semantic-test consumers.
- `native_check.check_native` has concrete archived callers in
  `U4-B-component-native-v1/{run_private,check_forgeries}.py` and
  `U4-B-component-native-audit-v1/{supplemental,projection_controls}.py`; it calls the
  retained pure `selection.assert_case`. `runtime_checks.assert_literals` is exercised by
  `test_runtime_checks.py`. Historical probes that require deleted operational tools
  must use their recorded Git revision; their presence does not keep that framework active.
- The already-built wheel matches its pinned receipt digest. All packaged Python and
  ordinary-schema members match the reconstructed source, and its native package contains
  only `__init__.py`, `ordinary.py` and `transport.py`. No tests, validation directory or
  review files are installed runtime dependencies. This was a read-only wheel inspection,
  not a new installation. [Packaging receipt](recheck-808076a/receipts/docs-packaging.json).

### Executed, inherited and limitations

Executed here: exact pin/reconstruction and restored-tree checks; scoped source/data/import
inspection; the positive/removal/drift/restoration controls above; the normal native Cargo
recipe and focused native mutants; optional ordinary process tests; default test discovery;
and read-only wheel, documentation and receipt inspection. Python used an existing locked
3.12 environment with the reconstructed source explicitly first on its import path. It was
not represented as a new source-free installation. Mutations were confined to the disposable
reconstruction, bytecode writing was disabled, and the final tree proves restoration.

Inspected and reused, **not rerun**: the author's 1,285-pass integration, static/type/schema
checks, 26-control installed smoke and binary-free replay; Stage 1's independent timing
worksheet, broader hardware sweep, detailed process/grandchild handling and version-lock
probes; and unaffected analytic/table/report evidence. The runtime/checker/transport
comparisons above bound that reuse. Historical operational assurance outcomes do not
qualify the ordinary route.

Six containers were created in this recheck, including the failed `make` attempt. Each
was removed and checked absent by its exact full ID. No other containers were touched.
No installation, new dependencies, infrastructure changes, hosted CI polling, historical
campaign, exhaustive mutation sweep or startup-substitution experiment was performed.

Remaining limitations: this appendix is not independent of the implementation author;
R1 remains non-blocking and open; supported hardware is not expanded; version/replay policy
remains as A1; human L1, the historical `/2` restriction, U0024, reference/U4b/G3a and
qualification obligations remain unchanged. This is not protected-installation approval
or U4 closure.

---

## Independent bounded recheck — 808076a (Stage 1 reviewer, 2026-10-19)

**Verdict: no blocking finding and no concrete regression from the cleanup. F1 and F3 are
resolved. F2 is resolved as scoped: there is one active checker, current behavioural tests
exercise it, and drift in it is caught for the law constants that the tests cover. A1 and A2
are handled.** One non-blocking residual coverage gap, R1, exists **in v1 as well** and is
not caused by the cleanup. One informational note on archival-only helpers. This is
evidence, not installation approval, U4/G3a closure or qualification.

**Attribution and integrity.** I wrote this section; I authored the Stage 1 report above.
The preceding section "Bounded successor recheck — 808076a" was written by the
implementation author, as it says itself, and was inserted into this report after Stage 1.
I did not write it. I treat its evidence as inherited author evidence, and I re-executed
independently everything I rely on below. Before appending, the file was 33,557 bytes
(SHA-256 `67e2c89076fe006d9848d6185ae1e03c3431cb8b97232bafebc12be3f0a1e808`). Its first
20,684 bytes are the Stage 1 text (SHA-256 `81da6750…c7ccac`). That matches the author
appendix's record and the original length, and I spot-read it against what I wrote. I had
not recorded my own hash at Stage 1 time. All earlier bytes are preserved, and nothing in
[recheck-808076a/](recheck-808076a/) was modified. New probes and receipts are in
[recheck-808076a-independent/](recheck-808076a-independent/).

### Subject

| Item | Value | Result |
| --- | --- | --- |
| Successor commit | `808076a8f1786f00ef9e3cd0de6ab8f2adea83ad`: that exact object, fetched into the session's scratch clone; moving main was not reviewed | pinned |
| Recorded base | `12be87558c5a3312068ab1c5aa147fd95df232da` (v1 was **not** applied first) | matches `base-commit.txt` |
| Patch SHA-256 | `b0de563bc3a6433b205649b3ed4db2861856636629dc715a18ff264f6eda4da4` | matches `transition.sha256` |
| Reconstructed tree | `9a86cab622504e68746534c94e93b659cacf794d` | reproduced by `reconstruct.py` and by an independent index-only `git apply --cached` |
| Comparison tree | v1 `b0f1755e…` from Stage 1 | v1→v2: 71 deleted, 50 modified, 3 added |

### Dispositions (new execution)

| Item | Disposition | Evidence |
| --- | --- | --- |
| **F1** | **Resolved.** | Python `OrdinaryBundle` and native `hardware_model` both require overhead = 32 and barrier = 32, otherwise `UnsupportedHardware`. My unchanged Stage 1 sweep against v2 ([receipt](recheck-808076a-independent/receipts/hw_sweep_v2.jsonl)): overhead 16 and barrier 16 are refused by the binary. The 128×128 array is still refused. Operand rate, DMA rate, NoC latency, t_cl and DRAM bandwidth variants still run and pass the consumer, with timings identical to Stage 1. Production 656000 ps and fixture 121000 ps pass. **Removal detection:** removing only the native pin fails `checker_hardware_domain` (84 passed / 1 failed) under the normal Cargo recipe ([receipt](recheck-808076a-independent/receipts/native_tests_and_mutants.txt)). Removing only the Python pin fails exactly the 16 and 64 cases (4 failed) ([receipt](recheck-808076a-independent/receipts/python_controls.jsonl)). Docs state that other values refuse; no wider capability is claimed. |
| **F2** | **Resolved as scoped.** | The seven shipped modules no longer exist in `validation/component`. The only same-named definitions elsewhere are in historical `/2` `transition_checks.py`: a different AST, consumed only by historical `observations_v2` ([receipt](recheck-808076a-independent/receipts/historical_transition_checks.txt)). 28 default-collected test files (392 tests) import-reach the shipped package, against 16 v1 files that reached the v1 `validation` copy of `observations_v3` ([v2](recheck-808076a-independent/receipts/checker_reach.json), [v1](recheck-808076a-independent/receipts/checker_reach_v1_validation_copy.json)). **Drift detection with default markers:** shipped `phase_laws` overhead 32→31 is caught (`test_resident_mechanism_literals`); shipped `check_v3` barrier 32→31 is caught (`test_literal_expectation_is_not_retuned_by_result`). The compute-overhead constant inside `check_v3` is not caught (see R1). |
| **F3** | **Resolved.** | `make native-test` is unchanged (`cargo test --locked --offline --all-features --target x86_64-unknown-linux-gnu`). The accepted image lacks `make`, so I ran that exact recipe: **85 unit + 2 binary integration tests passed, 0 ignored**. `tests/ordinary.rs` drives `CARGO_BIN_EXE_uarch-engine` on production (656000 ps) and fixture (121000 ps) `/4` jobs. It checks byte repeatability, `AdmissionMismatch` in both invocation directions, `UnsupportedProtocol` and `InvalidJson`. The `checker_hardware_domain` unit test covers `UnsupportedHardware` through `respond_with_test_mode`. **Removal detection:** I made shipping `main.rs` exit 0 with no stdout. All 85 unit tests still pass, but `ordinary_production_and_fixture_are_deterministic` fails. That proves the normal workflow exercises the real executable, not only library code. Hosted CI is unchanged and deferred under U0024. The Python process tests remain opt-in. |
| **A2** | **Handled.** | `CLAUDE.md:18-20`, `build-spec.md:992-994`, `build-spec.md:1302` and the `workload/mapped.py` docstring are corrected. No "native is planned/unimplemented" or host-authority/build-receipt statement remains in those docs ([receipt](recheck-808076a-independent/receipts/docs_a1_a2.txt)). CLAUDE.md is human-owned and stays inside the unapplied proposal. |
| **A1** | **Handled honestly.** | README, `native/README` and U0011 state: literal package version `0.0.1`; no build identifier; run and replay require the same installed version; the version does not distinguish builds; any change needs a protected contract change and an explicit compatibility decision; no cross-version replay. This matches `SoftwareIdentity` and `load_job`. No new framework is introduced or requested. |

### R1 — compute-phase law constants and consumer wiring lack default coverage (NON-BLOCKING; pre-existing)

* **Where.** `src/rkuarch/verification/component/observations_v3.py` (`("compute_overhead", 32)`,
  wave and drain constants; `phase_laws.resident_phases` repeats the overhead constant
  separately), and `src/rkuarch/engines/native/ordinary.py::consume` (its `check_v3` call).
* **Reproducer** ([probe](recheck-808076a-independent/probes/python_controls.py), [receipt](recheck-808076a-independent/receipts/python_controls.jsonl)):
  * compute overhead 32→31 in shipped `check_v3`: **381 passed, 2 skipped**, i.e. every
    default-runnable test that can reach the checker passes. With `ORDINARY_NATIVE` set,
    `test_positive_and_replay[False]` fails.
  * `consume` with the `check_v3` call disabled: **390 passed, 2 skipped**, even with the
    binary. The default saved-result fixture `sr2-v3` has no compute task, and the process
    test's wrong-law control calls `check_v3` directly.
* **Not caused by the cleanup.** I applied the same compute drift to the v1 `validation`
  copy. All 263 v1 default tests that could reach it, including the 15 files v2 deletes,
  still pass: 263/263 before and 263/263 after
  ([receipt](recheck-808076a-independent/receipts/v1_drift_baseline.txt)). Disabling v1
  `consume`'s call leaves all 21 v1 ordinary tests passing with the v1 binary
  ([receipt](recheck-808076a-independent/receipts/v1_wiring_baseline.txt)). The deleted
  `test_independent_checker_is_mandatory_for_valid_saved_response` asserted only that the
  **retired** `component_runner` invoked the `validation` copy; it never covered the ordinary
  consumer. I agree with the author appendix's R1 witnesses. I don't agree with calling them
  a coverage loss from the cleanup: ordinary-path coverage is unchanged (none before,
  none after).
* **Behaviour today is correct.** v2 `replay` refuses my Stage 1 self-consistent wrong-law
  result (structural `validate_result` accepts it, the shipped `check_v3` refuses it)
  ([receipt](recheck-808076a-independent/receipts/v2_replay.txt)).
* **Severity / blocks.** Non-blocking; it blocks nothing. This is a gap in regression
  protection.
* **Minimal correction direction (suggestion, not an acceptance requirement).** Add one
  default saved compute result: the existing `native/crates/uarch-engine/tests/data/ordinary-production.json`
  plus a saved output. Assert that it replays, and that a relabelled wrong-law variant is
  refused through `consume`. Optionally have `check_v3` take its compute constants from
  `phase_laws.resident_phases`. No hash, authority or campaign machinery is needed.

### Cleanup assessment

**No concrete regression found.**

* **Scope.** The 71 deletions are:
  * the 10 historical host/selector/record/review/construction/image/runner Python modules
    (already excluded from the v1 wheel), with their own unit tests;
  * 13 `native/tools` identity, freeze, corpus, adapter, guard, startup and trusted-start tools;
  * capture, monitor, ordinary-build, EOF-attestation, runtime-campaign/resource/selection,
    reduction and installation-identity validation modules, with their tests;
  * the 7 duplicate checkers;
  * the always-skipped K2 public suite (266 native-marked tests needing a human host
    selector);
  * Rust trust/profile test plumbing, plus 5 `#[ignore]`d private-corpus probes.

  Nothing under `docs/reviews/`, golden, fixtures, schemas, native testdata, `hw/`,
  lockfiles, manifests or `.github/` changed. No analytic, table, report, provenance or study
  code changed ([receipt](recheck-808076a-independent/receipts/scope_inventory.txt)).
* **Imports and commands.** Default discovery collects **2,485 tests with no errors**: v1
  had 3,065; 587 were removed, all in the deleted files or the removed pin/inventory tests,
  and 7 were added ([receipt](recheck-808076a-independent/receipts/collection_diff.txt)).
  Ruff, mypy (100 files, previously 110), mypy-contract, import-linter, all five schema and
  carrier checks, `uarch --help` and the ordinary CLI all pass
  ([receipt](recheck-808076a-independent/receipts/static_and_commands.txt)). No Makefile
  target, script, workflow, config or doc references a deleted file
  ([receipt](recheck-808076a-independent/receipts/deleted_name_references.txt)).
* **Removed tests vs retained laws.**
  * Of the 12 removed Rust tests, 7 are trust, profile, registry or retired-dispatch tests,
    and 5 are the opt-in private-corpus probes. The retained Rust suite still covers capacity and terminal
    readers, resources, compute/DMA/credit literals, refresh, zero-hop and clocks,
    issue-edge order and event-wheel laws ([v1](recheck-808076a-independent/receipts/rust_tests_v1.txt), [v2](recheck-808076a-independent/receipts/rust_tests_v2.txt)).
  * Of the 33 modified Python modules, 23 are import- or docstring-only. The other 10 are
    the F1 additions, the transport default, inlined ADR constants, a README assertion, and
    removal of source pins and frozen-inventory gates. Examples: `runtime_checks.consume_case`
    kept its validate → `check_v3` → literal core; `corpus.materialize` now reads recorded
    producer metadata instead of hashing its own source
    ([receipt](recheck-808076a-independent/receipts/modified_module_audit.json)).
  * Framing, exact refusal envelopes, limits and reaping keep transport tests in
    `test_u4_k2_process.py`.
* **Shared runtime.** The v2 wheel `fe5ede39…` is byte-identical to the author's digest
  (my v2 build, not installed). Compared with v1 it adds and removes no members and changes
  exactly 4 ([receipt](recheck-808076a-independent/receipts/wheel_v2.txt)).
  * The v2 binaries match the author's digests.
  * Production and three fixture outputs are **byte-identical to v1** in debug and release,
    and the hand timing derivation still matches
    ([receipt](recheck-808076a-independent/receipts/v2_outputs_and_timing.txt)).
  * `ordinary.py`, `workload/ordinary.py` and the checkers are unchanged; transport changes
    only its docstring and default protocol. So the Stage 1 installed-run, binary-free
    replay and process-handling evidence still applies, and I did not repeat it.
* **Retained helpers.** Every retained `validation/component` helper has active test
  consumers ([receipt](recheck-808076a-independent/receipts/retained_helper_consumers.json)),
  with one exception, below.
* **Informational C1.** `native_check.py`, and `selection.py` which only it uses, have no
  active importer. Their consumers are four archived probes in `docs/reviews/U4-B-component-native*`
  that need private `/tmp` campaign artifacts and container argv baselines. They are
  archival-only retention rather than live consumers. This is not a regression: keep them
  documented as archival, or drop them in a later cleanup.

### Executed, inherited and limitations

* **Executed here.** Exact pin, two reconstructions, scoped diff and inventory audits; the
  normal native recipe and two native removal mutants in the accepted image; v2
  debug/release builds and output byte comparison; timing derivation; v2 replay including
  the wrong-law control; the Stage 1 hardware sweep against v2; the Python F1 removal
  control; four F2/R1 drift and wiring controls over the reach-selected default tests; the
  v1 drift and wiring baselines; default discovery for v1 and v2; static checks and CLIs;
  the v2 wheel build and inspection (not installed).
* **Environment.** Python ran in my Stage 1 scratch dev environment. Its editable path
  points at a scratch directory, whose contents I replaced with the v2 reconstruction. No
  install command ran and no dependency was added. Mutations ran in disposable copies with
  bytecode disabled, and the imported module was verified to be the mutated copy.
* **Containers.** Six created (versions, test, debug, release, two mutants), each removed by
  exact ID ([ledger](recheck-808076a-independent/receipts/containers-ledger.jsonl)). The two
  pre-existing containers were untouched.
* **Inherited, not re-executed.** The author's 1,285-pass integration selection and
  26-control source-free installed smoke; Stage 1 transport and process probes and the
  version-lock probe (code unchanged); all receipts in the author appendix.
* **Limitations.**
  * Reach selection is a static import graph; tests outside it were not run under drift,
    and the full default suite was not run.
  * Drift controls change one constant each and are not exhaustive.
  * The native workflow ran as the exact Cargo recipe because `make` is absent from the
    image.
  * One host and image; no hosted CI.
  * No source-free re-installation, startup-substitution, authority or tracing work, per
    scope.
  * Human L1, the historical `/2` restriction, U0024, U4b/reference readiness, G3a and
    qualification remain outstanding. Protected installation remains a human step.
