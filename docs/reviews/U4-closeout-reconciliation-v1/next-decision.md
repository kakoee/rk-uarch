# Remaining U4 closeout decisions

This is prepared decision text, **not an approval record**. The implementation, corrected
human L1 workings, benchmark correspondence, documentation and prediction-order check are
ready. The [reconciliation](README.md) records current evidence and exact limitations.

Two existing readiness items need disposition before an unqualified U4/G3a closeout:

1. **Benchmark agreement.** Accept the unchanged 52 IDs and boundaries in
   [BENCHMARK-PLAN.md](../../../validation/L3_silicon/tpu-v5e/BENCHMARK-PLAN.md), with the
   existing reference preparation/U-C0 APIs replacing the incompatible legacy
   `uarch characterize` instruction. The nominal model stays at nine facts and 17 STUBs.
   Final A/B measurement signatures are absent. Either obtain the existing finite
   agreement, or explicitly accept a human-owned agreement in its place. No names will
   be signed on somebody else's behalf.
2. **Diagnostic and observability scope.** The proposed initial U5 comparison is the
   complete device duration and declared work/traffic envelope. Critical-path diagnostics
   remain explanatory, with F3/F6 limits; they cannot support a verified causal attribution
   claim. Compiler event boundaries, materialization and retention must be checked before
   freezing the corresponding prediction; a mismatched or unobservable envelope returns
   for a unit/target decision. Treating this as sufficient planned readiness to end U4,
   while reserving actual device-observability confirmation for U5 before freeze, requires
   explicit acceptance of that scope rather than claiming the observations already exist.

If these decisions are accepted, record the actual acceptance and update the existing
readiness status consistently before tagging `u04-end`. If the original requirement for
completed A/B agreement or demonstrated observability is retained, those items stay open;
there is no tag merely because the software is implemented.

Neither choice authorizes hardware access/spend, measurement, a new campaign, diagnostic
repair, compatibility cleanup or deferred native CI. U0024 and the reported unresolved
limitations remain in force. No new broad independent review is requested.
