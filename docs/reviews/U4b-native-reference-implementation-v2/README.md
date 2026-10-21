# U4b bounded B1/B2 correction — unapplied successor

**Ready for the same independent reviewer's focused B1/B2 recheck. Do not install the v1
`transition.patch`.** This successor corrects the two blocking findings in
`docs/reviews/U4b-native-reference-independent-review-v1/README.md`, reviewing publication
`0a5cebb9e81a2a382bcbaf4b9dfe5d13a2d2d58d` and proposed source publication
`4ce1a0aab0c9435a4158a4e3d1d96147bb3dd7f6` (source tree
`8739acc691ee2a81efcf14a035f28dd897024e0d`). The independent review directory is preserved,
not edited or republished as author evidence; its supplied files are identified in
[evidence/review-manifest.json](evidence/review-manifest.json).

The corrected source tree is `6b186db2dd90c09f97ba86282dfaaadd234da7cd`.
The [review delta](correction.patch) changes exactly three files:

- `src/rkuarch/workload/reference.py`: read the regular packaged JSON beside `__file__`.
- `src/rkuarch/verification/component/reference.py`: bind first activity readiness and job
  start to dependency readiness.
- `tests/reference/test_process.py`: the reviewer's resealed impossible schedule, direct
  checker and shipped replay controls, and legal equality/delayed HBM issue boundaries.

No protected-file delta is introduced relative to v1. The complete successor still contains
v1's protected proposals, **unapplied**, for the existing human-installation procedure.
The approved TPU v5e nominal model, labelled STUBs, 52 units and six benchmark classes,
component behavior (including the unresolved F4 below), single native engine, ordinary
execution and basic provenance are unchanged. No authority, attestation, startup guard,
build tracing, new approval framework or optimization is added.

## Exact reconstruction

Use the files from this successor publication in a clone with the recorded base available.
Python 3.12+ is required. From the repository root:

```sh
cd docs/reviews/U4b-native-reference-implementation-v2
sha256sum -c transition.sha256 correction.sha256
cd ../../..
python3.12 docs/reviews/U4b-native-reference-implementation-v2/reconstruct.py /tmp/u4b-b1-b2-review
```

The destination must not already exist. The helper exports base
`776321470cd5edf722adc97ae036a45398403704`, applies **this package's complete**
[transition.patch](transition.patch) only in the new disposable directory and checks the
recorded source tree. Do not first apply v1 or additionally apply `correction.patch`:
that second patch is the small review delta against v1's source tree, not an additional
installation step. [base-commit.txt](base-commit.txt), [source-tree.txt](source-tree.txt) and
[prior-source-tree.txt](prior-source-tree.txt) make these identities explicit.

No changes are installed into main by these instructions. Any later protected installation
must use the existing human-owned-file procedure for the complete coherent transition and
preserve intervening peer changes. This correction requests recheck, not installation.

## Response to each finding

| Finding | Correction or disposition | Evidence and limits |
| --- | --- | --- |
| **B1** | Replaced `importlib.resources` with `Path(__file__).with_name("tpu_v5e.json").read_text(encoding="utf-8")`. The wheel ships that regular package file. No isolation allowlist exception or repository fallback. | Existing production-isolation test and related contract tests pass (150 total); a new noneditable wheel loads the resource and runs/replays outside a checkout. |
| **B2** | Each sequence's first activity must have `ready_ps == job_ready`, or `>= job_ready` for HBM reads whose existing FIFO/window laws bind issue; job start must also be `>= job_ready`. | Both checker and replay reject the exact resealed 41 ps forgery; lawful 42 ps passes with vector start equal to its input arrival at 26 ps. HBM issue equal to readiness and delayed by spacing both pass. Removing only the guard admits the forgery and makes both regressions fail; exact restoration passes. |
| **F3** | **Unresolved, non-blocking. Behavior unchanged.** Non-HBM owner checks constrain grants relative to the preceding reported holder, not global FIFO or work conservation. | Reviewer's reordered, idle-owner 43 ps schedule still passes on the corrected source. A global per-owner arbitration check remains follow-up work. |
| **F4** | **Unresolved, non-blocking. Behavior unchanged.** A typical 65 MiB direct `/4` CLI input is refused as `InvalidJson` instead of the base's `CapacityExceeded` because parsing precedes the cap check on truncated input. | Reviewer observation inherited; native source is byte-unchanged. Refusal is still before execution. Ordinary Python still checks its 64 MiB limit before invoking the engine. No compatibility cleanup in this correction. |
| **F5** | Disclosure below; staging policy and all model values remain unchanged. | Reviewer analysis of simulator outputs, inherited and attributed. No new campaign or device measurement. |
| **F6** | **Unresolved, non-blocking. Behavior unchanged.** Critical-path intervals cover duration and satisfy activity bounds, but consecutive parts need not be connected by a recorded cause. | Reviewer's non-causal W-latency to X-service path still passes on the corrected source. Explicit adjacency/cause linkage remains follow-up work. |

This wording supersedes v1's broad claims about “earliest resource grants” and “actual
service/issue relationships”: **not all resource ordering or critical-path linkage is
independently verified**. The B2 guard closes dependency admission, not those other gaps.
The old handoff and historical evidence remain intact as records of the reviewed version.

## F5 disclosure and U-P9 interpretation

The current mapper serializes page/chunk round-trips through **one VMEM staging slot** for
these lowerings: gather/append (`mapping/reference.py`, `before = [end]`, reviewed line 659),
attention K/V packing and the per-head attention chain (reviewed lines 710 and 785), and
activation packing (reviewed line 320). Streams instead double-buffer (lines 520 and 561).
The nominal HBM window's approximately 256 KiB potential in-flight capacity does not make
these serialized mappings overlap-capable. The engine follows the selected mapping policy.

The independent reviewer measured the following properties **of final-source simulator
results**, as reported in review §3 F5 and `evidence/serialization-analysis.txt`. These are
inherited reviewer observations, not measurements performed in this correction and **not TPU
device measurements**:

| Unit | Simulated duration | HBM bytes / peak rate | Peak HBM requests in flight | Critical path in HBM latency |
| --- | ---: | ---: | ---: | ---: |
| `gather-p16-c2048` | 862.2 µs | 19.5 µs | 16 | 95.0% |
| `operator-attention_fused-decode` | 1,278.9 µs | 60.0 µs | 20 | 90.6% |
| `operator-q_projection-decode` | 58.0 µs | 39.4 µs | 32 | 38.3% |
| `layer-b1-s1` | 2,150.3 µs | — | — | Attention decode alone ≈ 1.28 ms |

Thus the nominal gather and attention durations are dominated by counts of serialized
approximately 400 ns round-trips; the p16/p32 page-size effect is largely a round-trip-count
effect. The related 16 MiB read is VPU-bound: the reviewer reported 201.7 µs versus 19.5 µs
for HBM bytes / peak rate, with 99% of its critical path in vector/reduction work. Its literal
`(1, 32768)` stream shape underfills sublanes by 8× under the approved layout rule.

These results cannot be treated as predictions for an overlap-capable TPU mapping without
reconciling the staging policy with the intended compiler/event/state behavior. A future
staging-policy change is a model-owner decision, changes job hashes and requires rerunning
affected units. No policy change, tuning or freeze occurs here. No deterministic test
establishes the validity of STUB estimates or silicon accuracy. Persistent SMEM metadata
is residency bookkeeping: retention in this model does not shorten service.

## Verification and stopping point

[Executed and inherited evidence](EVIDENCE.md) records the focused tests, meaningful guard
ablation, static checks, fresh reconstruction and installed controls. The 52-unit author
campaign and the reviewer's 14-unit all-class comparison remain inherited evidence;
unchanged native tests and the two larger gather fixtures were not rerun. There is no new
full Python or full workload campaign. The v1 [runtime report](../U4b-native-reference-implementation-v1/RUNTIME.md)
remains the applicable host-cost account; this correction does not optimize it.

For everyday use, the existing small selection now contains 62 tests, including these two
regressions. Run the relevant contract invariant tests when changing production imports or
contracts. Use the small installed controls for packaging/replay changes; unrelated changes
do not automatically rerun all 52 units. The full milestone campaign remains appropriate
when mapping, scheduling or nominal semantics change across the suite.

Author checks are complete for this bounded correction. The next step is the same reviewer's
focused B1/B2 recheck. Protected installation, TPU accuracy, final benchmark observability,
measurements, spending, frozen U5 predictions, remote/controlled-host qualification and U4
closure remain outside this handoff. No CI polling or device work occurred.
