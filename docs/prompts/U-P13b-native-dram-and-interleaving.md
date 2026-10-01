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

GUARDRAILS: No threads yet. Keep DRAM level 0 and level 1: they are the fast modes. Do not
tune DRAM parameters toward Ramulator's defaults; record the gap.

ADR: none here; U-P13d's U0013 records these levels and the fields Ramulator could not take.
```
