# Stage 2 shared proposal input — B author addendum

This supplements, without replacing, [B-F1–B-F8](../U3-lane-B-response.md).
A's Stage 1 report was read **read-only** in the coordinator checkout; SHA256
`b69965a70dc4262141c2d52b877cb9ce253566c1aba3bbf5d64e8e198e774233`.
The updated coordination note requests these inputs. Calculations below target A's
**published proposal** `43ab3e0809b58f7691396161c591c83726bb778d`, specifically
[interface admission/observations](../U3-native-stage-design-v2/interface.md),
[E2/E4/V01–V21](../U3-native-stage-design-v2/verification.md) and
[delivery/budgets](../U3-native-stage-design-v2/delivery.md). No semantic acceptance follows.
B read the intervening A author response; an unavailable A report is no longer a dependency.
Exact M carriers, human decisions, frozen fixtures and implementation remain dependencies.

B-F1/F8 corrections are finished **as proposals**, with their original receipts unchanged.
The unapplied repair remains SHA256
`4c73d73d1c7ec1e1453e7ef7ccf1bd3de55238a4469069dcaa75e89bc764fa81`.
No repair execution is repeated or newly credited by this addendum. Historical analytic
21/24 and 22/24 results, reason codes and partial/not_run reports are untouched.

## A-F1: proposed finite variant catalogue and ownership

The following is a **catalogue design**, not a NativeTestProfile, installed HardwareSpec,
new corpus or arbitrary-parameter admission. Names below are proposal labels. Unless
stated otherwise, vary one listed field family against A's exact npu-l4 baseline, retaining
work, placement, precision, other hardware and assumptions. Combined clock case C3 is
explicit, not a Cartesian product. B will later supply actual full specs, rationale per
changed SourcedValue, case graphs and expectations; A owns admission/identity semantics;
Javid decides them after coordinator reconciliation. Values are synthetic **stipulations**,
with source/provenance null where the accepted format requires, never chip measurements.
Each eventual spec belongs in `hw/designs/test-fixtures/`, design_status proposed. Preserve
existing baseline provenance; do not infer sourced accuracy from a baseline-shaped fixture.

| Label / exact proposed variants | Purpose and required case / fault mapping |
| --- | --- |
| P0 baseline test invocation | Cold/resident E3 and E4 controls, V06–V16. Same baseline hardware can have verification_only test admission without registering the production baseline as test-only. Cold production component tuple remains separate; no full-model admission. |
| CRED1/2/32: DMA max_outstanding 1, 2, 32 per engine | V08/V17, isolate credit response. Same-channel two, three and 33-request controls distinguish caps and early release; compare issue/acquire/release, not only makespan. Rationale: bounded in-flight population, no physical queue-capacity claim. |
| C1: core 1 and 2 GHz at frequency ratios 1 and 2; C2: NoC 1 and 1.2 GHz with core/DRAM 1 GHz; C3: core/NoC/DRAM 0.8/1.2/0.9 GHz | V04/V10/V14/V17, isolate compute scaling, edge alignment and all-domain crossings. Resolved integer clocks and scales_with_core flags must agree; no double application of ratio. Other A-allowed core 1.2 GHz cases need concrete entries before use. Independent E2 edges do not assume E4; E4 timings do. |
| BW1/2: DRAM bw_bytes_per_s 10^12 and 2×10^12, unchanged channels/refresh | V13/V17, isolate rational channel capacity. Compare channel service and valid work; do not require twice overall speed. Removing refresh is a fault, not a successful alternate profile. |
| LAT1/2: t_rp/t_rcd/t_cl each 16 and 32 cycles; t_rfc/t_refi remain 350/3900 | V08/V13/V17, isolate fixed latency versus serialization. At one credit the idle two-hop single-read bound is latency-limited. Larger streams require proved saturation before a bandwidth claim. No simulator-preset or physical-DRAM evidence. |
| RATE1/2: operand_bytes_per_cycle 1024/2048; separately DMA bytes_per_cycle 256/512 | V09/V12/V17, isolate compute staging versus shared core port. A ≤256-byte request still costs one port cycle in both DMA variants: this is a useful equality control, **not** a strict-speedup discriminator. Never pool fragment remainders to force a speedup. |
| DELAY1/2: separately router_latency_cycles 2/4, compute job_overhead_cycles 32/64, barrier_latency_cycles 32/64 | V10/V12/V14. Doubling one delay must affect only its represented mechanism. DMA keeps zero compute overhead; barriers use only their NoC-domain latency. Rationale: expose misplaced delay/attribution, not calibrated latency. |
| ACC1/2: accumulator_bytes 131072/262144 | V11, supplied 256×256 output requires 262144 bytes; low-capacity case refuses, high exactly fits. No retile/spill or spill-monotonicity credit. Smaller positive tile must still fit low capacity. |
| CAP boundary cases on unchanged spec | V11/R10: SRAM 16777216 bytes, operand buffer 1048576, HBM 32000000000. Check exact-end allocations versus one-byte-over and overlap/lifetime; for operand capacity use a shape-valid fixture if the required boundary is reachable under B limits. Do not invent an oversized executable tile to reach it. A reachable smaller operand/SRAM hardware variant would be a separately reviewed catalogue extension, not already allowed by this row. |
| SYM/IDLE: symmetric core relabeling; one unused column, 2×3 | V16/V17, equal represented work and routes/owners remapped explicitly; unaffected used subgraph required before equality. A owns canonical owner/address/bank enumeration. “Idle” must not silently change controller/channel routes. |
| TDP100/200 | Identity/unmodeled-effect control only. Timing/count equality with all represented fields fixed; no energy inference, energy stays unverified. NoC bandwidth/VC/physical queue checks stay unsupported until modeled. |

For each actual case freeze checkpoint, invocation, scope/state/priming, full hardware
bytes/hash, resolved clock map/ratio, graph/point identities, allowed jobs, seed, selection
revision and exact positive or named refusal. Follow A's proposed acyclic profile→bundle/
job→result identity; bind the semantic implementation separately from its version string.
A's phrase “signed case manifest” still needs the actual signer/approval mechanism in M;
B's authorship does not create cryptographic or human authority. No hashes are fabricated here.

Proposed admission attacks pair valid controls with missing/mismatched profile/case,
unlisted tuple, wrong stage/scope/state, renamed/copied registered test hardware, stripped
admission, and rehashed result relabeled production. Assert A's proposed specific errors
(TestProfileMismatch, TestVariantNotAdmitted, UnsupportedCheckpointScope,
UnsupportedInitialState, TestOnlyHardware, TestOnlyScope, AdmissionMismatch). Every
consumer must refuse verification_only where product eligibility is required. Positive
K2 fixed-delay/null-fidelity results do not count as B subsystem verification; private K1
has no public result. A supplies the exact parser/dispatch/registry patch before these
become executable checks; B audits all reads/imports and strict public-loader refusals.

This small family list supplies neither 24 distinct cases per applicable V17 relation nor
a replacement for analytic C1's 22/24. Propose the finite concrete case list and invocation
budget **before** discovery; retain all attempts/refusals and fixed-work checks. Freeze
qualifying identities and run producer-disabled replay only in a separately authorized
phase. No favorable rerun, skip-to-pass or cross-mode/native coverage substitution.

## A-F2/F3: independent calculations under the exact revised E4 law

[check_shared_math.py](check_shared_math.py) is a standard-library scalar worksheet. It
uses rational arithmetic and binary search over published clock edges, not A's inverse
formula or runtime/helper imports. It has no queue engine, native protocol, production
loader, arbitrary job input or report output. Its assertions execute author mathematics;
they are not behavioral mutant kills, human L1 fixtures or qualified suite evidence.

Premises are explicit: core0(0,0), engine0, channel6 at controller3(1,1), XY two hops,
HBM `1536+2048*j`, SRAM `256*j`, 256-byte requests, valid nonaliasing buffers, no other
traffic; core/NoC/DRAM initially 1 GHz. Reads issue all credit-admitted ready requests at
core edge0, with no finite issue cap or payload port on issue. Port rate256 bytes/core
cycle is shared by engines/read/write; credit release waits for destination commit/ack.
No compute job overhead on DMA. Writes use the port before outgoing NoC; acknowledgement
has no port service. These are **A's unaccepted conventions**, not independent hardware facts.

Channel rate = `10^12×71/(78×8) = 4437500000000/39` bytes/s; 256-byte service =
`159744/71` ps. First request arrival4000, DRAM latency ends52000. Exact channel end
`3851744/71` ps publishes ceil54250; return NE_noc(54250,4)=59000, port end60000.
Carry exact rational finish between requests. Each cycle-valued transition uses its named
domain; channel service itself is continuous bandwidth-time, with ceil only at publication.

| Clock tuple GHz (core/NoC/DRAM), case | Independently derived key timestamps ps |
| --- | --- |
| 1/1/1 read1 | arrival4000; latency52000; channel54250; response59000; complete60000 |
| 1/1/1 read2, same burst | exact carry; channel56500; response61000; complete62000 |
| 1/1/1 write1 | port1000; arrival5000; latency53000; channel55250; ack/core release60000 |
| 1/1.2/1 read1 | arrival3334; DRAM align4000/latency52000; channel54250; NoC align55000/response58334; core align59000/complete60000 |
| 1/1.2/1 write1 | port1000; NoC align1667/arrival5000; latency53000; channel55250; NoC align55834/ack59167; core release60000 |
| 0.8/1.2/0.9 read1 | arrival/DRAM align3334; latency56667; channel58917; NoC align59167/response62500; port complete63750 |
| 0.8/1.2/0.9 write1 | port1250; NoC align1667/arrival5000; DRAM align5556/latency58889; channel61139; NoC align61667/ack65000; core release65000 |

Receiving-mechanism attribution: baseline read noc8750 + memory51250 =60000;
three-domain read noc6917 + memory56833 =63750. Entry-alignment waits stay with the
receiving mechanism; channel/port waits are memory. Observe the actual causal predecessor
for contention rather than adding all owners' busy time. These exact partitions depend
on A's proposed attribution law; the arithmetic sum alone cannot verify causality.

| Proposed discriminating check | Correct versus explicitly worked alternative |
| --- | --- |
| Omit refresh | Five completions `[60000,62000,64000,66000,69000]` versus `[60000,62000,64000,66000,68000]`. First **four** completions mask this fault. First channel end54250 versus54048 also separates it. Preserve masking as a negative test of the test. |
| Fixed-time NoC return instead of next_edge | At 1 GHz response58250 instead of59000, but final60000 masks fault. At NoC1.2 GHz fixed return57584 gives final59000 rather than60000. Check crossings, not a tuned total. |
| Feed ceil back into channel service | Twelfth same-channel exact published finish78999 versus repeated rounded service79000. Assert exact reduced ratios too; a masked final completion cannot pass this assertion. |
| Align bandwidth finish to DRAM | First finish55000 instead of54250. Bandwidth-time has no DRAM-edge quantization rule. |
| Rounded 1.2 GHz period | Billion-cycle edge833000000000 rather than833333333334; no cumulative rounding tolerance. |
| Ignore credit cap / release early | One-credit two reads end120000 versus62000 at ≥2 credits. Three reads with cap2 finish120000 versus64000 at cap32; third issue60000 versus0. For 33 same-channel reads at cap32, request33 first issue60000; releasing at latency end makes52000. Full placement required. |
| Duplicate shared port / hide issue limit | Two channel6/7 read responses simultaneously ready59000 must commit60000 then61000, not both60000. All five ready E4 reads must issue0 with cap32; a one-per-edge law fails issue records even if some totals mask it. Freeze channel7 address1792, distinct SRAM range and tie order in this additional case. |
| Add generic overhead to DMA | Baseline isolated read60000 versus92000 if32 core cycles are inserted before issue. Barrier arrivals60000/62000 release94000, with only32 NoC cycles. |

No native code was mutated or executed for this table. Actual baseline/fault/restored
public-run controls, exact case manifests and two human L1 derivations are pending.
Physical NoC queues, bandwidth contention and refresh-event timing are not inferred.
The independent lower bounds at B use represented work/rates and latency, not a fabricated
analytic component API. Required analytic checks remain before their first actual reliance,
including R/G3a before U-P9; v1/v2 analytic admission stays unchanged.

## A-F10: observation volume, validator work and budget input

B accepts A's **proposed narrowing of the performance fixture**, not of admitted B
correctness. Retain every required event, request, transfer, membership, owner, allocation,
causal interval and result binding. Before measurement A must enumerate the actual record
multiplicities/field widths and parser storage; 32/request is a planning allowance, not a
proven upper bound. No summary, truncation or separately hashed artifact is authorized.

| Input | Requests | Four-record minimum / 32-record planning | Planning request bytes at 256 / 512 bytes per record |
| --- | ---: | ---: | ---: |
| E4 burst33 | 33 | 132 / 1056 | 0.258 / 0.516 MiB |
| Single cold C1 | 576 | 2304 / 18432 | 4.5 / 9 MiB |
| Maximum B, 16 ops×4 tiles×1536 requests | 98304 | 393216 / 3145728 | 768 / 1536 MiB |

Widths256/512 are **sensitivity assumptions**, not observations; jobs/buffers/envelope are
additional. Maximum payload is25165824 bytes. The review's ~79.7 MiB four-record estimate
uses different explicit widths; it is compatible with this sensitivity calculation and
is not a measured floor on the final serialization. No encoded-byte number proves RSS.
At65536 records, 256 bytes/record alone consumes the proposed16 MiB cap, leaving no room
for other serialized material if the cap covers it. Freeze whether the cap counts just
observations or full result; record both actual sizes. Do not fit by removing required data.

B's proposed validator cost accounting, once carriers exist:

- Parse strict canonical data, validate shapes/identities and hash all bound bytes: at
  least O(S) for S encoded bytes; include fresh subprocess serialization, transport,
  Python parsing and validation in all-in wall/RSS. Hashing is not a substitute for checks.
- Build unique request/job/owner/buffer ID joins and check all issue/completion/credit/
  byte relationships: O(N) expected indexing for N records, with bounded hostile-input
  behavior. Missing, duplicate, mismatched and terminal in-flight cases must refuse.
- For finite-window/capacity/credit checks, sort endpoints per owner/population and sweep
  clipped half-open intervals: O(E log E) conservative, E≤2N for interval records. At the
  request planning count alone, maximum B gives up to6291456 endpoints, about145 million
  comparison-scale operations (E×ceil(log2(E))). The small65536-record cap gives at most
  131072 endpoints and about2.23 million by the same model. These are work estimates,
  neither measured comparisons nor seconds; existing canonical order may reduce sorting.
- Track bytes plus object/index/endpoint allocations, child and parent overlap. Materialized
  validation costs O(S+N+E) storage, with unknown constants/copies. A 512 MiB all-in claim
  is not established by the small file cap and is implausible at some maximum-size assumed
  widths even before parser objects. Measure peaks under the accepted host protocol later.

Retain finite-window clipped-residence/credit/capacity observations and checks **at B**
(V21). Stationary Little's-law ≤1% belongs at first stationary claim, normally U6 or earlier
reliance, with population, window, boundary residents, censoring and nonzero-flow premises
frozen. Transient conservation does not prove stationarity; premise-invalid runs cannot pass.

Proposed decision: 5 s/512 MiB applies only to A's named K2≤256 jobs/1024 edges, single
cold/resident C1, or E4≤33 invocations, each separately, and only after exact fixture and
all-in measurement definitions are accepted. Full B correctness retains maximum shapes
with an adequate authorized memory allocation; separately decide full-size wall/RSS/record
budgets before a performance claim. Overflow is incomplete/refusal with diagnostics, never
success. Do not retrospectively select a favorable case. Later U0011-Q representative
budgets, U0012 protocol and controlled-host/full G5 prerequisites are distinct and pending.

## Reconciliation decisions and next owners

| Decision/input | Owner, first-use deadline and B position |
| --- | --- |
| A-F1 admission/profile/registry and catalogue | A exact M patch; B specs/rationales/case design; Javid semantics and hardware decision before fixture installation/public use. Accept direction, request explicit signer and exact capacity reachability review. Audit all new registry/profile/spec/expected-case reads and import/initializer dependencies before M installation under unchanged U0002 or separately accepted migration. No projected inventory count. |
| A-F2/F3 exact E4 law and cases | A semantics, B independent expectations, two separately assigned human L1 fixtures; Javid before native corpus freeze. Calculations agree with A43ab3e0; unlimited issue, compute-only overhead, continuous rational service and wait attribution remain explicit human decisions. Changed law invalidates dependent expectations, not old history. |
| B-F3 component/analytic boundary | B accepts independent component bounds at B; coordinator disposition pending. No new analytic API/admission. C1 anchors/deferred analytic relations/v2 corpus keep separate decisions and first-use deadlines. |
| B-F5 Linux CI/tool-pin ownership | B accepts 6–10 hours (pins/wiring2–3, refusal/origin2–3, receipts2–4), A consultation1–2 within existing K1 allocations, no double charge. Before any K1 credit: accepted tool/license/image/lock pins, A's exact targets/debug-release tests/resource requirements, actual approved Linux job. K2 adds public tests. Missing-source/no-op, wrong pin, absent build mode and intentional failure must refuse. No workflow execution now; coordinator assignment/effort decision pending. |
| B-F6 finite/stationary schedule | B observation/check owner, A telemetry semantics, coordinator exact V21 reconciliation. Required finite observations at B, stationary ≤1% first claim with frozen premises. No objection to A's revised wording; no author acceptance on Javid's behalf. |
| B-F7 H-DMA/H-CLOCK | Exact replacements and human-decision rows already in current readiness supplement and A delivery; unchanged and unapplied. Both memory-only ops and C2 base-clock dominance align (B-F2); v1 supersession stays row-level (B-F4). Javid decides live prompt changes separately. |
| A-F10 observation/budget | A concrete observation enumeration, B validator/noise/budget preparation, Javid exact measurement scope/resources/limits before measurement. Accept narrow fixture direction; reject using estimates as evidence or reducing full correctness/records to fit. |

Proceed only to coordinator reconciliation and the **same B reviewer's Stage 3**.
No findings are closed, no new policy/carrier/hardware/budget is installed, and no gate,
performance/nightly, migration, independent-review or sprint acceptance is claimed.

## Executed addendum checks (2026-10-12)

Started and integrated clean main `a7f4acb12d4bd4adf29668a9707440738aa44f09`; origin was
already current. Private checks used `git archive` of that commit plus only this owned
proposal delta; no repair applied. Each command below ran sequentially with
`env -u PYTHONPATH -u MYPYPATH PYTHONDONTWRITEBYTECODE=1` and executable prefix
`/home/jjaff/AI-infra-simulation/rk-uarch-u3-b/.venv/bin/` from the disposable export:

| Actual command | Result |
| --- | --- |
| `python -I -B docs/reviews/U3-B-stage2-v1/check_shared_math.py` | PASS: seven fixed timing rows, arithmetic alternatives and volume estimates above; no native/suite result |
| `ruff check .` | PASS, no exemptions added |
| `mypy src contract/uarch_contract scripts` | PASS, 78 source files; unchanged live policy, not the prior 80-file repair export |
| `mypy --no-explicit-package-bases contract/tests` | PASS, 31 source files |
| `mypy docs/reviews/U3-B-stage2-v1/check_shared_math.py` | PASS, 1 source file after local corrections |
| `lint-imports` | PASS, 101 files/600 dependencies, 2 kept/0 broken |

Initial extra worksheet mypy check found five diagnostics: variable-length tuple inference
and comparisons of literal unequal constants. Corrected the annotation and compared fault
values to independently derived rows; expected numbers unchanged. Re-ran the worksheet,
all-tree Ruff and extra mypy before completing import-linter. The two exact CI mypy target
sets were already passing and unchanged, so were not redundantly repeated. Import-linter's
existing editable src/contract roots were verified byte-identical to the export (119 Python
files); the worksheet uses `-I` and imports only the standard library. Exports were removed.

Owned local Markdown links and `git diff --check` passed. Patch and both reviewer report
hashes retain their recorded bytes. No new fault touched source/data, temporary or live.
Prior repair baseline/fault/restored/static/strict-vendor results in evidence.json are
**inherited, not rerun**. No pytest/full suite, strict-vendor rerun, real migration, native
run, host measurement, hosted CI or nightly was performed for this prose/worksheet delta.
These omissions reflect unchanged source/enforcement and the bounded author scope; required
future native controls remain not_run, not skipped successes. Publication commit is supplied
in the Git handoff rather than hashed into its own content.
