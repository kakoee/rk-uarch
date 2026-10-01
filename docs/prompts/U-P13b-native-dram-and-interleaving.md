# U-P13b · U7 · Lane A — Native DRAM: queues with back-pressure, Ramulator 2, and interleaving

_From build-spec §8. One prompt, one fresh session._

```text
CONTEXT TO LOAD: CLAUDE.md, native/README.md, build-spec §2.3.2 (memory, presets, queues and
credits), §2.4 and §2.8, ADR U0011, U0012, and U0008's DRAM L2 report. Ramulator 2
documentation (its External frontend, for use as a library).

TASK: DRAM at levels 1 and 2, with the controller back-pressure the spec now describes, and
the address interleaving that decides which cores talk to which controller.

1. DRAM level 1 with cycle timestamps ("1+ts"): a per-channel queue with a row-buffer
   approximation, the spec's page policy, and the spec's read and write queue depths. It
   stays the fast path.
2. DRAM level 2: Ramulator 2 linked as a library through its External frontend, at the SHA the
   engine image pins, one instance per memory controller, configured from the spec's DRAM
   organisation, timing, timing_preset and queue depths, and never from a preset or default
   the spec does not name; what Ramulator needs and the spec lacks is listed as
   unrepresented. The bridge is its own crate, crates/uarch-ramulator-sys: a thin C++ shim over
   the External frontend, compiled by build.rs, bound with cxx, and the ONLY crate allowed
   unsafe, every unsafe block with a SAFETY comment. The engine crate calls it through a safe
   API and stays #![forbid(unsafe_code)]. Register Ramulator 2 and cxx in
   third_party/LICENSES.md.
2a. Driving a cycle-ticked library from the event kernel, EXACTLY AS build-spec §2.8
   ("Cycle-ticked models inside the event kernel") SAYS:
   - Ramulator cycle c is edge next_edge(dram, 0, c); its clock comes from
     clock_domains.dram, and a configuration whose clock disagrees (including a
     data-to-command clock ratio the spec does not give) is refused with both values named;
   - busy: one MEM_TICK ticks the instance in one bridge call through every cycle before the
     horizon H = min(next pending event's t_ps + L_in, earliest MEM_REQ already scheduled
     for this controller, window end), stopping early after the first cycle that completes a
     request or admits a waiting one. L_in is computed from the spec (the final router and
     link at the attach point), never configured;
   - idle: no events; the next MEM_REQ first catches the instance up through the idle cycles
     in one bridge call, so refresh happens exactly as if it had ticked throughout. No
     shortcut that is not byte-identical to catch-up;
   - completions are returned sorted by (cycle, request id); request ids come from a
     per-controller counter in arrival order; same-edge requests are sent in event total
     order;
   - a debug flag ticks every DRAM cycle with one MEM_TICK each: the REFERENCE MODE.
   Simulator metrics report busy ticks and catch-up ticks per simulated DRAM cycle
   separately.
3. Back-pressure: a controller whose queue is full withholds NoC credits (noc_credits), so
   requests wait in the network rather than vanishing into an unbounded queue.
4. Addresses map to channels and controllers by memory.interleave, so the NoC sees the
   traffic pattern the interleaving creates. The job chooses the DRAM level; EngineResult
   reports which ran, and fills dram_bw_util_ratio and dram_row_hit_ratio where the level
   models them.

ACCEPTANCE TESTS (write first):
1. L0, L0m and L1 pass at both new levels; L2 DRAM (vs standalone Ramulator 2) is recorded
   against the native engine, with each >5% deviation attributed where it can be.
2. Interleaving bites: changing memory.interleave's granularity changes the per-controller
   traffic split and the NoC diagnostics, at equal bytes.
3. Back-pressure bites: halving a controller's queue depth under saturating traffic never
   shortens duration, and raises NoC latency at that controller's attach point.
4. No preset fallback: a spec without timing and without timing_preset is refused at DRAM
   level 2, naming the missing fields.
5. Determinism: byte-identical at 1 and N workers; the bridge's tests run clean under
   AddressSanitizer in the nightly job.
6. unsafe appears nowhere outside crates/uarch-ramulator-sys (a test greps the workspace).
7. Batching is exact: at DRAM level 2, every golden request and a saturating-stream fixture
   produce byte-identical EngineResults in batched mode and in the tick-every-cycle
   reference mode (simulator metrics excluded).
8. Idle refresh: a request arriving after an idle gap longer than t_REFI sees the same
   latency in batched and reference modes, and a different latency from a run with refresh
   disabled in Ramulator, which proves catch-up is not skipping refresh.
9. Causality: the debug build's assertion (no MEM_REQ arrives at an edge the instance has
   already ticked past) holds on every golden request, and a test that forces L_in too
   large makes it fire.
10. Clock agreement: a spec whose Ramulator configuration implies a clock different from
   clock_domains.dram is refused, naming both values.

GUARDRAILS: No threads yet. Keep DRAM level 0 and level 1: they are the fast modes. Do not
tune DRAM parameters toward Ramulator's defaults; record the gap.

ADR: none here; U-P13d's U0013 records these levels, the fields Ramulator could not take,
the measured cost of busy and catch-up ticking, and each controller's L_in.
```
