# U-P16 · U8 · Lane B — The mesh measurement kit, the second validation verdict, and fidelity-level evidence

_From build-spec §8. One prompt, one fresh session._

```text
CONTEXT TO LOAD: CLAUDE.md, measure/README.md, validation/L3_silicon/blackhole/SUITE.md,
validation/ledger/README.md, ADR U0010 (how the first verdict was reached; reuse it). Tenstorrent
tt-metal documentation: TT-Metalium kernels, the device program profiler, tt-smi. PREREQUISITE:
a host with the Blackhole p100a installed, Ubuntu 22.04 as the card's docs require, and tt-smi
reporting the card. If any of that is not true, stop and say so.

TASK: measure the mesh reference, compare against every frozen prediction set, and let the
ledger say what the native engine, per fidelity level, is entitled to claim.

1. measure/blackhole/: the kit, written and dry-run BEFORE the card is used for real. One
   TT-Metalium program per benchmark in SUITE.md, with profiler zones exactly where SUITE.md
   puts them. The dry run executes on Tenstorrent's functional simulator (ttsim, Apache-2.0)
   where it supports the kernel. ttsim does not model timing, so dry-run outputs are labelled
   SYNTHETIC and are refused by the ledger. Environment capture per result: firmware, tt-metal
   version, clocks as reported, card serial.
2. Run on the card only after check_ordering passes. Raw results (profiler CSVs as emitted,
   plus the derived durations and the derivation script's hash) are committed immutable under
   validation/L3_silicon/blackhole/results/.
3. Ledger entries, one per (benchmark × prediction source): native at each fidelity level,
   U-C0, and tt-npe. The same key discipline as U-P10.
4. THE NEW THING THIS VERDICT CAN SAY, which the first could not: whether MORE DETAIL IS
   MORE ACCURATE for this class. Report the error by class for each native fidelity level
   side by side. If composite C2 is not closer to silicon than level-1, the report says so on
   its first page. Detail is fidelity, not evidence; this is the one place you can test
   whether it is also accuracy.
5. Gate G7 (execution-plan §4): the same thresholds as G4, applied to native composite C2 on
   the mesh family. Promotion is scoped to the mesh family and the passing classes only.
6. tt-npe vs silicon on NoC benchmarks goes in the report as context, labelled as an L2
   reference's own error. It is not our evidence.

ACCEPTANCE TESTS (write first):
1. The dry run completes and the ledger refuses its SYNTHETIC outputs.
2. Every result file postdates its prediction file (the ordering check is green).
3. The per-level error table exists, with ≥ 3 levels × ≥ 4 classes.
4. G7 is evaluated and recorded either way; promotion, if any, is scoped to the mesh family.
5. A large-core design's request still gets stub from mesh evidence (applicability).

GUARDRAILS: If G7 fails, publish the errors anyway and follow its fail branch. Do not average
across classes or levels to pass. Do not change the engine in this session. Do not let
tt-npe agreement stand in for silicon agreement.

ADR: docs/decisions/U0016-the-mesh-validation-verdict-and-whether-detail-helped.md.
```
