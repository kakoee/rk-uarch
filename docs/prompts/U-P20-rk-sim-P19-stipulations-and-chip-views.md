# U-P20 · U10 · Lane B · RUNS IN rk-sim — Stipulations through the product, and the chip views (rk-sim P19)

_From build-spec §8. One prompt, one fresh session. **This prompt runs inside the rk-sim
repository**, and is adopted there as `docs/prompts/P19-stipulations-and-chip-views.md`, with its
text added to rk-sim's build-spec §8. The rk-sim-side copy is in this kit at
`rk-sim-side/prompts/P19-stipulations-and-chip-views.md`._

```text
CONTEXT TO LOAD: rk-sim's CLAUDE.md (invariants 2, 3 and 10), web/README.md,
web/src/components/Badged.tsx, FidelityPicker.tsx, CoverageBanner.tsx, web/src/lib/fidelity.ts,
web/src/screens/{Builder,Results}.tsx and the Compare and Assumptions screens from P9b,
rk/api/README.md, tests/api/test_contract.py (canonical routes), ADRs 0009, 0011 §5, 0016,
0021, 0027, the accepted boundary ADR, and P18's handoff.

TASK: a stipulation reaches a human as what it is — a scoped question, not a weak claim — and
a C2 component shows its evidence where the user is looking.

1. make gen after the schema PR, so web/src/types.ts carries SourcedValue.kind/rationale,
   Metric.conditional_on, the fidelity map's model_origin, fidelity_detail and table_hash,
   and ComponentDescriptor's design_status and characterization.
2. <Badged> gains the conditional state: when conditional_on is non-empty, it renders
   "conditional · N stipulations" next to the badge, and its popover lists each stipulation
   with its rationale. CONDITIONAL IS A SCOPE STATEMENT, NOT A WARNING. It is not amber, not an
   alert and not dismissable. The error band renders as the band or as "unknown", NEVER "±0".
   Keep every switch over Calibration exhaustive (a `never` default), so the compiler finds
   every place a new state must render.
3. Builder and inspector: a design_status: proposed component is labelled "proposed design".
   The inspector lists claims and stipulations under separate headings. The fidelity picker
   offers C2 ENABLED only for components whose fidelity_available includes it (ADR 0016:
   selectable = built). For any other component C2 renders disabled, with the reason, not absent.
   Update web/src/lib/fidelity.ts's three sets and tests/unit/test_fidelity_ts_sync.py
   together.
4. A chip panel in the inspector and Results for a C2 component: composite fidelity plus the
   per-subsystem detail vector; the model card (badge, evidence scope, validated band or
   "unknown"); uarch version and table hash; tp; measured interpolation, composition,
   layer-reuse and cold-vs-steady errors; the initial state and KV block size; energy marked "unverified" while
   the card has no energy evidence; flop-parity deviations; the conditional_on list. EMBED
   IT IN THE EXISTING COMPONENT/RUN RESPONSES. Do not add a route: test_contract.py freezes the
   canonical route list, and the
   boundary ADR does not amend it.
5. Compare: when the two sides differ in compute fidelity (C2 vs C0), a banner states that the
   comparison is biased AGAINST the detailed part, because it charges stalls the roofline cannot
   see, and shows the C2 part's own u_c0 duration beside it, so the detail delta is visible.
6. Assumptions page: stipulations of proposed components under their own heading, "Design
   stipulations — these define the question; they are not claims." Never listed as STUB or
   ESTIMATED.
7. Tell uarch: its vendored round-trip test asserts rk-sim refuses a stipulation. After this
   lands, that assertion is false by design. Record it in your handoff so uarch updates the
   test and its ADR together.

ACCEPTANCE TESTS (write first):
1. vitest: <Badged> with conditional_on renders the marker and count; with none it renders
   exactly as before (the existing tests are unchanged and still pass).
2. No rendered text anywhere in the app contains "±0" for a C2 component: a DOM text scan in
   the Results and chip panel tests.
3. The C2 picker is enabled only for a characterized component; it renders disabled, with the
   reason, for an uncharacterized ASIC and for the H100.
4. The Compare banner appears for C2 vs C0 and is absent for C0 vs C0: asserted as a pair.
5. Assumptions: stipulations appear under their own heading and never under STUB or ESTIMATED.
6. test_contract.py's route list is unchanged.

GUARDRAILS: Numbers render only through <Badged>. Never improve a badge in display code.
Do not add routes. Do not fill ci95 from a deterministic run. No new UI dependencies:
Tailwind defaults, as web/README.md says.
```
