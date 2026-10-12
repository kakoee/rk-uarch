# Delivery, dependencies and prospective cost

## Ownership and revised active effort

Person-hours, planning ranges, not logged time or calendar promises. A is this engine
lane; B remains evidence/product/hardware owner. No delegation or independent-review
claim is implied. Review column is additional effort by an independent reviewer and
human decision-maker, not counted in A/B implementation hours.

| Checkpoint/work | A effort | B effort | Review effort | Human/calendar dependencies |
| --- | ---: | ---: | ---: | --- |
| U3 proposal reconciliation and schema decisions | 6–12 | 6–12 | 4–8 | Javid scope/interface/runner decisions; remaining U-P6 disposition |
| M: exact schema patch, fixtures, component mapping/import | 20–32 | 12–20 | 6–10 | Protected install/commit; U0002 source freeze/lifecycle coordination |
| K: toolchain closure, single-thread fixed-delay kernel/runner | 28–44 | 12–20 | 6–10 | Pin/license acceptance; currently required Linux/runner/manual-nightly readiness |
| B: bounded compute/DMA/NoC0/DRAM0, completion observations | 32–52 | 24–40 | 8–12 | Independent corpus; human L1 working; stage review |
| T: full workload/policies/precision/table/error expansion | 64–112 | 40–72 | 12–20 | Hardware and FP8/RoPE/ragged decisions; coefficients; request/table schemas; lifecycle |
| U6: mesh qualification, diagnostics, host cost/regression | 28–48 | 32–56 | 8–16 | Designated controlled host/time; prospective workload and noise-policy acceptance |

M+K+B: A80–128, B48–80, review20–32, total148–240. U4b is an additional116–204;
U6 an additional68–120. U3 reconciliation adds16–32. Overall remaining scoped planning
range348–596 person-hours. Kernel/models occur only in U4a's line items. U5/U8 silicon,
U7 depth, U9 threading, new external adapters and optional references are excluded.
T has low confidence because FP8/RoPE and unequal-batch semantic decisions are unresolved;
re-estimate after those decisions. Host/admin/reviewer waits have no defensible calendar
bound and are **not** included in active effort. B's historical completed v1 work is not
recounted as new native verification. No further Python contention-engine allocation.

## Expansion path to the unchanged G3/G5 requirements

1. After B, extend tile reduction/K splits, accumulator spill and explicit partial sums;
   verify additional SRAM traffic and no speedup under a reduced accumulator on fixed
   supplied work. Implement vector/normalization/residual/activation, all projection/FFN
   classes, embedding/lm_head, KV writes and fused attention using the same TaskGraph.
   No component scope can be marked complete_model merely because total GEMM ops agree.
2. Add complete v2 mapped preparation: supplied coefficient closure and per-node traffic,
   Q/new-K casts, positions, projection correspondence, rank replication/embedding hit
   scope and every repeated layer. Preserve full-square/causal choice. Require BF16
   end-to-end admission before reporting a BF16 decoder layer. FP16/FP32 remain refused
   unless the selected hardware and explicit format/rate coverage admit them.
3. Resolve hardware: baseline npu-l4 declares only weight_stationary and BF16. B proposes
   a separately accepted sourced revision with output_stationary and FP8 definitions/rates,
   not a silent change to the frozen hash. Both `ws-rowsplit@1` and `os-tiled@1` require
   specified buffer depth and exact independent placement/transfer examples. Domain
   expansion may retain @1 only if its existing mapping decisions remain unchanged;
   changing an existing decision requires a new policy version and a new identity.
4. Resolve the **FP8 semantic blocker**: U0022 allows activation/KV only FP32/BF16/FP16;
   current Precision couples compute choices more tightly than a proposed mixed matrix /
   activation pipeline. Either accept an explicit versioned FP8-compatible rotary/cast/KV
   profile, or a new explicit mixed-precision contract with all conversion work. Select
   one before implementation; neither dropping RoPE nor relabeling a BF16 run as FP8
   meets G3. This package does not choose unsupported numeric semantics.
5. Full tables use npu-l4 × [70B-class shape](../../../contract/fixtures/model_shapes/llama-3.1-70b.json),
   fp8 and bf16, tp8, both policies; tp1 where weights fit, otherwise retain the real
   weight-capacity refusal. Freeze exact sourced ModelSpec/ModelShape, precision, complete
   coefficients/profile, rank and mappings, not just the model name. Include all layers,
   once-only head/tail, no collectives. Complete default grid: decode B=[1,2,4,8,16,32,64,128],
   C=[128,512,1024,2048,4096,8192,16384,32768]; prefill n=[1,2,4,8],
   L=[128,512,2048,8192,32768]; frequency=[1,0.6]. That is 168 points/precision/policy,
   672 points for two precisions/two policies, excluding tp1 and error experiments.
6. Implement public preparation/capture/table/report integration and pool workers 1/8,
   ordered assembly, hardware residency checks and explicit omissions. Outside grid
   refuses; interpolation uses the stipulated log-coordinate/1/f law and protected
   interpolation vectors. G3 LOO median≤5%,max≤15%, uniform weights agree; composition,
   layer reuse, cold/steady and priming2-vs1 errors have seeded finite observations and
   n_samples. Re-run the frequency points, never infer timing from attribution.
7. **Composition coverage is a semantic dependency:** U0022 rejects ragged/offset positions.
   U-P7's unequal-batch experiments cannot be manufactured by silently changing uniform
   v2 graphs. Prepare exact independent batches/positions under a separately approved
   extension and save all sampled work. If that extension is absent, required error
   coverage is missing and G3 stays pending. Imported bundles with missing main/error
   query/state/frequency coverage refuse; no hidden local producer fills the gap.
8. T must include long prefill L32768 with score tiles fitting SRAM and only declared
   Q/K/V/O attention DRAM traffic, complete count/transfer checks and all applicable
   L0/L0m/L1. Retain failures; optional references cannot replace these. Complete model
   table results must preserve diagnostic nulls, truthful fidelity, STUB and unknown error.
9. U6 adds the initial npu-m256 table (ws-rowsplit initially), complete traces/diagnostics,
   replay/determinism and absolute host-cost qualification. Mesh routes, memory binding
   and clock domains require exact fixtures; torus/multiple-NoC support is not claimed
   by B's 2×2 mesh. U-P11c/U-P12 qualify the existing core; U5 silicon can follow G3
   without waiting for G5. U7 detail and U9 threads remain later decisions.

## Environment and license closure proposal

No build, container, host change, install or dependency resolution was performed. Use
`x86_64-unknown-linux-gnu`, a pinned stable Rust release and Cargo.lock, explicit rustfmt
and clippy components; initial direct crates serde/serde_json, dev proptest only.
Require a reviewed pin manifest containing full Rust release/commit/checksums, exact
transitive crate versions/checksums/features/licenses, cargo-deny version, base OS image
digest/architecture, OS package snapshot/versions and build commands. Cargo uses --locked;
separate networked dependency acquisition from the reproducible offline build. No moving
stable/latest tag in the installed recipe. Debug and release use the same pinned source,
compiler and lock. Rust types must pass all approved Python schema/canonicalization fixtures.

**Exact release/digest/lock inventory is unresolved, not invented.** An attempt to consult
the [official stable manifest](https://static.rust-lang.org/dist/channel-rust-stable.toml)
was inaccessible through the web reader in this design session. The next pin-only review
must resolve the then-current stable release from that manifest and freeze immutable
checksums before any build. This remains a G2/toolchain acceptance dependency, not a
claim that the recipe is already reproducible. No requested runtime work is performed
while it is unresolved.

License checks cover transitive crates and build/run tools, not just direct dependencies.
Current [allow-list](../../../third_party/LICENSES.md) is MIT/BSD-2/BSD-3/Apache-2.0/
Apache-2.0 WITH LLVM-exception with a narrow LGPL-tool exception. The U-P11a warning
about unicode-ident/Unicode-3.0 requires inspecting the chosen lock; any actual outside
license needs a specific human ADR before use. Separate OS/compiler/tool execution terms
from linked/shipped code and retain notices. An OS base image is not made compliant by
cargo-deny alone. No blanket license exception or dependency approval is asserted.
Ramulator/cxx, loom, sanitizers for absent bridges and optional tools are not B dependencies.

## Correctness CI, measurement host and automation

- **Correctness CI:** supported Linux toolchain builds; rustfmt, clippy -D warnings,
  cargo-deny, debug/release tests, schema freshness and real public-boundary fixtures.
  Hosted Linux can supply correctness evidence if the human adopts the pending policy
  separation. Local WSL arithmetic/prose checks are not native performance evidence.
- **Performance host:** proposed existing Debian12 `v2202507191245365394`; historical
  [host receipt](../U3-preparation-v1/host-preflight-reported.json) reports 12 logical CPUs
  and 32863040 KiB RAM. Later handoff reports rootless Podman 4.3.1. These are inherited
  reports, not fresh contact, exclusive allocation or runner-account verification.
  Before measurements record CPU model/topology/governor/load/kernel, available RAM,
  container digest and cgroup limits. Reserve one physical core without sibling load,
  one process tree, one simulator thread, one point worker; ≤16 GiB RSS and 20 GiB scratch.
  Separate build window with ≤2 build jobs/8 GiB RAM. These allocations are proposed,
  not authorized use of the server.
- **Self-hosted automation:** registration/account credentials, labels, schedule enablement,
  account-specific Podman/workdir permissions and successful manual nightly executing
  actual native tests. No no-op conditional job proves readiness. B owns workflow work;
  human/admin owns registration, access and resource allocation.

Installed U0005 presently makes **all three** prerequisites before native implementation /
build/performance work. The coordinator recommendation to narrow that is pending, not
accepted. Recommend a separate human amendment allowing approved Linux correctness work
independent of runner registration, retaining designated-host performance and real nightly
automation gates. Until installed, follow the existing stricter text. Design/schema proposals
can proceed now. This file neither edits policy nor claims the runner is ready.

## Prospective absolute budgets, not observations

All limits below are per fresh invocation, including job validation/loading, subprocess
startup, simulation and complete deterministic result serialization/parse; a prebuilt
binary/container image may be used. Exclude image/build time but report it separately.
Mapped input preparation is measured separately; it is not declared free in table costs.
Measure maximum elapsed host time and maximum process-tree peak RSS over seven recorded
runs after one separately recorded warm-host setup run. Retain all eight; simulated cold /
steady is unchanged by host warm-up. No outlier deletion or favorable rerun selection.

| Scope/workload, single-thread/worker on the proposed host | Wall-time ceiling | RSS ceiling |
| --- | ---: | ---: |
| K fixture ≤4096 fixed-delay jobs/16384 edges; B component cases up to16 ops at M1024,K=N256, cold and resident separately | 5s | 512MiB |
| T npu-l4 full 70B-class model, tp8, each of the 672 required points (both precisions/policies) | 60s | 4GiB |
| U6 npu-m256 full same model/grid, tp8, ws-rowsplit, each required point | 120s | 8GiB |
| Prospective 32×32 mesh extension, same model, BF16,tp8,decode B32/C4096 and prefill n1/L2048, both f1 and0.6, ws-rowsplit | 300s | 16GiB |

Five seconds is an interactive small-fixture ceiling, not extrapolation from a fork.
At 60 s, 672 base table points allocate 40320 s (11.2h) serial execution; sampled error jobs,
tp1, preparation, repeated builds and review are additional. No 24 h complete-table guarantee
follows. The 120/300s ceilings are explicit cost envelopes for larger topology qualification,
not predicted scaling. Revisit prospectively if scope changes, never after results to
turn a failure into a pass. The 32×32 hardware spec/hash is not yet approved; that budget
is conditional and cannot authorize a stress run or satisfy U9 until exact hardware and
workload identities are frozen. Same applies to T's pending precision/coefficient closure.

Timeout at the applicable ceiling, then at most 5 s process-tree cleanup; distinguish
refusal, timeout, crash and OOM, retaining partial logs. Missing measurement leaves
qualification pending; exceeding a budget is a reported finding informing U9, never a
correctness pass or license to add threads. No old 200 s fork allocation is inherited.
Record host ns and perf instructions where permitted, events/simulated cycle and
completed job, max live events/RSS; native cycles remain internal with receipt units
explicitly labeled simulator metrics. No events-per-second headline or WSL speed claim.

For U0012 regression calibration, predeclare a 20-repeat control series, report median,
range and relative spread, and seek human acceptance of the noise-aware regression
threshold **before** using it. Require a deterministic injected 2× host delay to trip it;
if noise masks that effect, host/regression qualification remains pending. This does not
alter simulated duration or stable result bytes. Host observations never fill ci95/error
fields for predicted chip timing.

## Optional comparison map

No tool is admitted or run here; all are unavailable/unmatched/not_run until scoped
U0008 approval and exact input/tool/license pins exist. Criteria must precede outcomes;
a discrepancy cannot disappear by removing its reference afterward.

| Candidate, component | Matching needed | Evidence limit / prospective rule |
| --- | --- | --- |
| SCALE-Sim, WS/OS tile interval | Array/dataflow, resident tiles, masks, operand bandwidth, fill/drain/overhead conventions | B's proposed wave law may be unmatched; compare only corresponding phases. Propose exact integer equality for a deliberately identical isolated pipeline law, otherwise record unmatched, not a numeric pass. No whole-chip validation. |
| BookSim2, later reservation NoC | Topology, routes, packetization, clocks, VC/flow control, traffic and load | B NoC0 contention not_run. Once admitted after U-P13a, retain ≤10% latency error below 70% reference saturation; above record only. |
| Standalone Ramulator2, memory | Exact organization/direct timing, transaction/address mapping, queues/state and trace | B fixed latency abstraction is not row-model equivalence. Record matched-limit streaming separately with ±5% U-P8 criterion. Later shared Ramulator library checks are integration, not independent physics. |
| Gemmini/Verilator, isolated systolic tile | That RTL's actual geometry/precision/dataflow and boundaries | Not established for npu-l4; unavailable/unmatched until proved. No transplant of RTL accuracy to this proposed design. |
| tt-npe, later mesh NoC; optional Timeloop mapping study | Same route/traffic/abstraction or same array/work/constraints | Prospective scope/criteria first. Mapping efficiency is context, not evidence that a supplied mapping was executed; never invokes search inside the engine. |
| Energy | Every coefficient family requires its own evidence | Deferred after U8; unverified/null today. |

Silicon U5/G4 and U8/G7 are distinct frozen-prediction campaigns, with unchanged thresholds,
funding and mapping-match rules. Neither same-code agreement nor multiple component matches
composes into whole-chip accuracy. No external whole-model reference requirement returns.

## Checks actually executed and publication discipline

This task executed source/document inspection, Git status/history/ancestry/fetch and safe
fast-forward, and calculated the canonical npu-l4 identity with the existing installed
Python environment. A separate standard-library arithmetic check validates the displayed
integer/rational examples; a local Markdown-link/JSON-projection check and `git diff --check`
check the proposal package. These are documentation checks, not native tests or evidence
artifacts. These checks passed: 29 local Markdown links resolve; both JSON projections parse;
all displayed count/transfer/clock/timing/grid/effort arithmetic assertions pass. Final
staged whitespace/path-scope checks and publication are reported in the author handoff.
No full pytest, mypy or lint suite is warranted for new Markdown only; no prior runtime
suite is represented as rerun. The inaccessible web manifest supplied no toolchain pin.

Only these six Markdown files are owned changes. Normal pre-commit hooks must run; no
human flag, hook bypass, reset, force push, checkpoint copies or protected edits. Fetch
and integrate peer main before normal publication; record the final published commit in
the handoff, outside self-referential document hashes. This package stops at coordinator
review and does not authorize subsequent implementation or claim any gate accepted.
