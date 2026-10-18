# Final A binding/3 runtime integration and private build handoff

A completed the engineering transition requested by B's final disposition **07af1a93c009abfd8fb987995dd6cb854364db9b**, preserving human installation **6f5a4bf8cf0c283964ffe3a87ef46e5f024cbb2c**. The coherent new source freeze is **cc899d289c84aa837cd72ca23956c29443a2af40**. Both actual ordinary executables and cfg(test) executables were built privately from that committed source using fresh isolated targets and the accepted offline environment. The old c67d558 candidate retains its original files, binaries, receipts and verdict scope.

[Identities](identities.json), [executed versus inherited checks](checks.json), [reconstruction verification](verification.json), [evidence archive index](evidence-files.json), and [final B review batch](peer-final-review.md) define this candidate. The package manifest binds these leaves without including its own hash or its publishing commit. This is a private preparation handoff, not independent adversarial acceptance, deployment, genuine runtime authority, public first use, performance qualification or closure. B's prior bounded author audit is acknowledged; B's response to these new actual identities remains pending.

## Exact changes and identities

B's A-binding3-unapplied.patch applied cleanly and exactly. It changes only the preparation tool's independent consumer binding path to `U4-B-component-runtime-final-v1/consumer-bindings-v3.json`. The registry and definition selection remain B's reviewed selection/2. A did not reapply the installed annotation or edit protected files. The three new regression cases are ordinary A test additions; the three human contract-test postimages are unchanged and lie outside BuildInputs.

Exactly three of the 228 BuildInputs entries differ from c67d558; the other 225 match:

| Entry | Reason |
|---|---|
| `validation/component/runtime_checks.py` | already installed, exact int argument/return annotation; checker behavior unchanged |
| `validation/component/issue-amendment-binding.json` | human-installed three test identity updates; not omitted from the build transition |
| `native/tools/component_runtime_candidate.py` | exact B binding/3 path amendment |

[complete-build-input-delta.patch](complete-build-input-delta.patch) reconstructs these three entries from c67d558, including the already installed peer/human changes for audit only; do not reapply it to current main. [A-owned-source.patch](A-owned-source.patch) is the ordinary A tool/test delta from07af1a9. The complete joined source is `git archive cc899d289c84aa837cd72ca23956c29443a2af40`; applying the A-only patch to an older checkpoint does not supply peer history. The verification record applies both routes in fresh private exports and compares exact postimages.

| Identity | Exact value |
|---|---|
| BuildInputs / implementation | `sha256:e1b11298b075da071d43d27288d7387261b1d17589e7c17b22b9e7f3613db3cb` |
| model native-intervals/2, unchanged | `sha256:745d0dfbb369ae9f16525ebfc188488dc0d4847c14ca5d8ae259945795a3d6a4` |
| ToolInputs, unchanged | `sha256:db8b8956f0c060416d0d3c6c11f8eccc6b3ece7433b5075cb093e602febcb73d` |
| debug ordinary executable | `sha256:90198b1c9f3e61597d3f67491dbea2566ac9c827d25b204900e7d83719aaf472` |
| release ordinary executable | `sha256:54b76fdc8530771d59842a4ae2f37013c6396bc2fe0fe58c976ff1b5b71c3577` |
| debug cfg(test) executable, unchanged bytes | `sha256:979b8440964754e79eea96d39212f7cc2884b4a98f8bdfd0ba4637ceecbdb609` |
| release cfg(test) executable, unchanged bytes | `sha256:0f01e110f07c9f68c3e9204720832dbeed5375c56889f3f09354cff4cc79011b` |
| B independent binding/3 file | `sha256:32ed90dfe5fd26b962b9078f1023bc4b4c462e82f561b21e5ca78f90e9cba6bb` |
| final prospective payload, local v2 | `sha256:f400ad69681856e62ecc873d6c8e9cdf3ce43db2f0eada2745f292b70cbd7541` |

Actual binaries and the private data export are retained at `/tmp/u4-a-runtime-build-cc899d2`. Evidence archive members retain their actual command/stream/generated-source and source/import paths. Binaries, Cargo targets and cache are not embedded in the archive; actual file hashes are verified, not hypothetical build outputs. The sole image is `sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523`. The existing 1719-file cache, lock/features, wrappers and tool versions were verified before/after the builds. No dependency or toolchain change occurred.

BuildInputs precedes generated identity and engine-bound jobs; actual executables precede BuildReceipts and payload. Independent review and any later human decision/HostRecord/selector would follow. No record includes its future hash. Schema versions remain BuildInputs/2, construction trust/2, payload/1, model2, observations3 and profile2. The payload versions named v1/v2 are local data-export versions within this new candidate, not replacements for the old candidate's payloads.

All 124 old/new raw jobs are explicitly joined in `private-component/previous-candidate-job-transition.json`. Only engine.implementation_hash and the enclosing job_hash change. Every profile, policy, mapping, bundle, point, graph, registry and expectation stays unchanged. The 104 positive definitions pass complete preparation. The 20 finite negative definitions retain hash-bound original envelope expectation provenance; four new refusal executions are distinguished below from the 16 definitions not newly executed. These prospective negative bindings create no public bypass.

The new initial payload was expanded explicitly to local v2 with observed Python mapped files and B's two already hash-bound orchestration helpers, as in the prior reviewed preparation. Both local preimages are preserved. Final executable/consumer/replay probes use v2 with 1297 current-file checks. No c67d558 result is relabelled as a cc899d2 execution. Runtime setup/current-byte/import checks and session limits remain the reviewed implementation: session_seconds bounds call start, per-call timeout is separate, and an outer campaign must enforce total elapsed time.

## Executed controls and reusable evidence

| Check | Result and attribution |
|---|---|
| test-first binding baseline | six known stale-source refusals reproduced; new matching-path assertion also failed; both deliberate wrong/stale controls passed:7 failed,2 passed |
| exact path amendment | all9 focused controls passed; no source guard disabled |
| actual final payload binding controls | complete matching104-positive payload accepted; prospective stale/wrong bindings refused specifically at runtime_checks.py before dispatch |
| final tracked-export integration | 38 passed:32 runtime integration cases, including all6 formerly stale cases plus matching/wrong/stale binding controls;6 unchanged unapplied D3 tests |
| root Ruff | passed in clean source export; final publication export separately recorded |
| strict types | cold mypy with PYTHONPATH unset passed4 sources:3 maintained integration modules plus exact privately exported D3 v3; no skip/suppression |
| necessary builds | actual debug/release ordinary and unit executables; source/generated/cache postchecks passed |
| fresh private native processes | 12 distinct bounded containers:cc0 and transient O2 initial/replay in both modes (8 positives), SRAM guard in both modes (2), historical C04 profile refusal in both modes (2) |
| actual positive results | cc0=121000ps and O2=2735000ps; structural validator, check_v3 and B binding/3 wrapper/literals all passed; one Runtime::run entry each |
| actual refusals | exact SramCapacityExceeded and TestVariantNotAdmitted with pointer null; zero Runtime::run entries; profile refusal is not mislabelled a resource-guard result |
| fresh replay comparisons | debug/release and initial/replay complete bytes equal for the four selected definitions; old positive observations equal after excluding only engine/job_hash/result_hash; old error bytes exactly equal |
| independent saved-output replay | four actual new positive outputs consumed again with producer exports unavailable through both validators and B binding/3/literals |
| unchanged D3 proposal | four actual new native refusal envelopes/profile joins accepted privately; zero-entry evidence remains separately bound, not inferred from envelope validity |
| ordinary-executable transport | eight actual processes: malformed UTF8, unsupported protocol, absent component authority and K2 substitution per mode; correct exit2 refusals, no public success |

Private cfg(test) processes exit0 as harnesses while native semantic status is recorded separately. Each run has its own container identity, true output files, raw job/executable binding and runtime-entry receipt. They are not ordinary production positive executions. The per-call controls remain CPU1/RAM1GiB/PID64/FD256 with30s process timeout. No444-call private campaign or1368-call public campaign was run.

No Rust semantic source, host/runner implementation or installed checker law changed. Exact unit executable equality and non-generated Rust equality justify reusing the prior8 typed native unit controls and Clippy/rustfmt evidence; equal unit binaries do not establish production reproducibility. The earlier94 A semantic outputs,54 saved-output consumptions,40 D3 envelopes,36 K2 compatibility tests, B's12 original-candidate processes and54 original-output consumer checks retain their original labels. B's mandatory-checker and source-digest fault/restoration evidence applies to unchanged guards; this task adds the concrete path baseline/correction and explicit stale/wrong rejection controls without another mutation sweep.

The new regression tests were written before applying the exact amendment. A test-only line wrap fixed Ruff E501 after the9-case development pass; the final38-case export verifies those exact committed bytes. Raw captured red output is preserved, including its normal trailing spaces; it is evidence, not source formatting to rewrite. No semantic test was weakened to accept a stale closure.

## Read audit and remaining decisions

The100-leaf B audit and its final integration disposition were read and verified. That is completed bounded author review of c67d558 plus the proposed path amendment, not acceptance of these new actual binaries/payload. The [peer batch](peer-final-review.md) asks B to close this exact transition. No connected session route is available; publishing the batch is the coordinator relay, not a fabricated reply.

The three historical read gaps remain unresolved: debug.trace.450:11 and debug.trace.452:9 are unknown syscalls; release.trace.482:10 is unfinished sched_getaffinity. No targeted capture was performed: this change concerns source binding, and the necessary build's source/cache/command/ELF/DSO/import observations do not recover the missing historical events. Exhaustive construction-read closure remains unsupported. No diagnostic relaxation, waiver, repeated trace build or same-input production reproducibility claim is made.

| Item | Disposition / owner |
|---|---|
| A binding3 + source/build/raw-job/payload transition | complete engineering candidate atcc899d2; exact receipts attached |
| B final new-identity join | pending exact response to published batch; prior bounded author audit preserved |
| independent runtime acceptance | later reviewer decision; no author audit substitutes |
| F1 / F4 | prior accepted laws unchanged in behavior; actual model2→obs3→check_v3 plus binding3 route exercised |
| F2 | historical /2 unrepaired; affected/unclassified same-engine/same-instant acquired releases blocked regardless of direction; conservative >1 request/engine classifier and cc0-v1/ww0-v1 provenance unchanged |
| F3 | installed real-validator capacity regression and separate independent defense unchanged; prior A1b fault/restoration remains inherited evidence |
| D3 | exact v3 patch/postimage remains unapplied; later separate negative authority/profile/selector and finite public gate decision |
| compiled positive authority and deployment | later reviewed mechanism/generator, source/build/rebinding, root placement/preflight and genuine review/decision/HostRecord/selector/profile chain; existing construction binaries cannot be activated by a selector |
| human L1 / U0024 / qualification | genuine H-L1-GEMM-01/H-L1-DMA-01 workings still due; U0024 unchanged; no badge/performance/R/TPU/G3a/U4 closure |

The prior [deployment/first-use sequence](../U4-A-component-runtime-v1/runtime-first-use.md) remains prospective with this package's exact identities replacing only future candidate references. Its old typing dependency is resolved by the human/B installation and this actual binding3 transition; old records are not edited. Applicable deferred U-P11b phase-B cases remain public L0/L0m/L1, six-way determinism, public latency/attribution/critical-path checks and saved-input replay. Genuine human arithmetic is not an approval click. Full operators/decoder, extra hardware/precision, spill/priming/steady modes, R/TPU/reference qualification and artifacts remain outside this work.
