# Next decision requested from Javid

**PROPOSED. Nothing below is accepted or executed by publishing this package.**
Javid (@jjaffari) acts as decision-maker for both lanes. No Reza approval is inferred.

## Recommended authorization: bounded U-C1 amendment design

Accept the source-feasibility disposition at the exact publication revision of this package:
no faithful complete adapter-only route is established at the two comparison pins. Defer
U-P5 builds/adapters/G2 evaluation and commission the following **design-only** task:

> A and B prepare one U-C1 alternative under docs/reviews/: (1) a compute-contention model
> and declared NoC/DRAM/state/mapping scope consuming the complete accepted v2 work;
> (2) literal diagnostic expectations and discriminating acceptance cases for compute
> overlap, queues/outstanding requests, rank/repeats, fused paged attention and RoPE;
> (3) a separate execution/result/evidence boundary proposal preserving v1/v2 analytic
> history; (4) exact proposed execution-plan and U-P5/U-P7/U-P8/U-P11c/U-P12 amendments,
> with any further affected dependency listed; (5) implementation/verification cost and
> an explicit go/no-go decision. Cap combined A/B active work at 28 hours (expected 16–28).
> If a coherent design is not available within the cap, report the unresolved issue and stop.
> Publish ordinary owned review-document commits; stop for Javid's acceptance/human ADR
> and plan commits before implementation.

This is category 5 **proposal work**, not automatic activation of the plan's “both fail”
branch. A source-based fallback trigger requires the [draft U0005](proposed-U0005.md) and
exact human-owned plan/ADR disposition. Reading this package does not amend a gate.

Preconditions: coordinator reconciles this revision and relevant peer changes; confirms
A/B assignments and preserves accepted U0002/U0003/U0004/U0006/U0019/U0022. No host or
container prerequisite is needed for this design task. Expected A 8–14 and B 8–14 active
hours; separate reviewer/human effort 4–8 hours, calendar wait unestimated.

Success: a reviewable design that accounts for **all** required model work, names every
modeled/unrepresented hardware quantity, earns its proposed level from actual planned
contention behavior, and explicitly states what becomes of U4/G3, U5/G4, U6/G5 and the
permanent external-reference objective. It must retain matched-work/mapping/level premises,
STUB/unknown-error/unverified-energy and independent review obligations. It cannot relabel
U-C0 as C1 or silently equate future native/U-C1 agreement with independent fork accuracy.

Refusal/stop: missing faithful workload coverage; unverifiable observations; a need to weaken
accepted semantics to fit the design; inability to define matched-level G5; or exhaustion of
the cap. Report these as design blockers, not measured G2 failure. Stop after proposal
publication even on success. No fallback/native implementation, public v2 table/report path,
support-bound change, protected edit, oracle lifecycle, runner/server action or U-P7 execution.

## Decisions that remain separate

| Decision | Authority still needed |
| --- | --- |
| Tool direction | Accept defer/design option; no candidate selected and pins unchanged |
| Fallback implementation / engine behavior | Later exact design acceptance and task; not authorized by this design tranche |
| Observation instrumentation | Separate category-3 scope, sites, fields and noninterference controls; not approved |
| Workload, coverage, thresholds, fidelity, G2/fallback trigger | Human U0005 and exact plan/prompt amendments; 200 s and revised RoPE diagnostic preregistration remain pending |
| Licence exceptions / unknown grants | Exact human ADR disposition and missing grant closure; no blanket permissive exception |
| Host allocation / runner | Human/admin/B action, account-specific readiness, reservation and manual nightly; none granted |
| Build / capability experiment / G2 measurement | Three different later authorizations; a clean build or tiny capability result cannot pass G2 |
| Production evidence/report integration | Separate A/B shared-carrier design/human commit, U0002 lifecycle if support changes, independent review and eligibility |

## Nonrecommended alternative: one BF16 capability discriminator

**UNEXECUTED; conditional, not the recommended authorization.** This specifies the smallest
runtime question that could challenge the inspected P precision blocker if Javid chooses
extension research. It does not grant a build, modify a compiler or change G2. Use P
`5ec17ff2d18c08d10ae4bf5b101cd9e131a3fba3` unmodified; no moving revision, template edits,
private operator substitutions or expected-count logging.

Preconditions before scheduling: exact resolved LLVM/MLIR/Gem5/Spike source and build pins,
complete licence disposition, approved immutable source-built image/config, exact driver
review, approved native host/account/resource controls. These do **not exist in this package**;
image/compiler/config/driver digests are UNRESOLVED. A separately authorized build must come
first; fail/stop on missing closure, do not pull an artifact image as a substitute.

Exact work: one custom-device `torch.compile(fullgraph=True)` matrix multiply with BF16
X[1,128], W[128,128] and BF16 output, FP32 accumulation required. X is all 1; every column
of W is [256,1,−256,0,…,0]. Required mathematical count is 16,384 MAC = 32,768 ops; it is
only an expectation. The arithmetic target is 1 in each output element using the required
accumulation semantics. Run one FP32-storage version as a separate positive compiler control,
then the BF16 case, then repeat BF16 in a fresh process/cache directory. FP32 control success
cannot validate BF16 throughput or H1 compatibility. This is a kernel capability diagnostic,
not a prepared full-workload execution; no embedding/attention/RoPE/G2 claim follows.

Command skeleton, deliberately not an installer or an existing runnable project API:

```text
# CONDITIONAL FUTURE commands; review/approve exact driver and closure first
# <...> identities/configuration are unresolved, not shell defaults.
podman run --rm --network=none --cpuset-cpus=<reserved-core> --memory=24g \
  --pids-limit=256 --mount <read-only-driver-and-inputs> --mount <fresh-output-dir> \
  <approved-image@sha256:digest> \
  python <reviewed-probe.py> --case <fp32-control|bf16|bf16-repeat> \
  --config <approved-config> --fresh-cache <case-cache>
```

The future probe uses `ExecutionEngine.setup_device()` and the ordinary compiler/simulator
path; retain Aten/MLIR/LLVM/assembly, TOG, offline latency records and raw logs. A timeout
supervisor must contain the entire process tree, enforce **600 seconds per case + 5 seconds
cleanup**, one CPU/thread and 24 GiB/100 GiB scratch, max three cases. This is an exploratory
stop limit, explicitly **not** a new G2 threshold. No overlapping build/nightly window.
The driver/preflight must establish all controls without simulator/compiler patches or refuse.

Positive evidence requires typed BF16 operand storage and actual two-byte transfers, FP32
accumulation, correct numerical outputs through the functional path, and provenance of the
instructions/latencies actually used by TOGSim. Retain completed-work observations where
available; missing counters stay unavailable. A graph that compiles as f32, falls back to
host work, omits latency, or uses the TOG 10-cycle default is a negative result regardless of
numeric output. The FP32 case is a negative admission control for calling the result BF16;
feeding it to that claim's checker must be rejected. Static inspection of a removed-latency
copy must reject before simulation; never simulate the fabricated latency to “see if it works.”

Interpretation: FP32 control fails → inconclusive setup/capability finding, stop; BF16 fails or
emits f32 → precision route rejected, stop without patching; both succeed with complete
provenance → only that kernel survives the discriminator, stop for review. Missing observations,
timeout/OOM or mismatch → preserve evidence and stop, no retry to erase it. Even a positive
result leaves fused paged attention, full RoPE, ranks, observations and full G2 unresolved.
No broad capability suite, instrumentation or extension implementation follows automatically.
