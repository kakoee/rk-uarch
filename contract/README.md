# contract — THE shared vocabulary (human-owned)

Everything rk-sim and uarch exchange is defined here, and nowhere else: SourcedValue (with
kind claim|stipulation), HardwareSpec, the operator vocabulary, ModelShape, the
CharacterizationRequest, the UarchCostTable, the ModelCard, hashing and the error taxonomy.

## Rules
- Agents propose changes for human review; every change has an ADR. For U1, Javid
  (@jjaffari) is acting approver for both lanes while Reza is off duty. U0001 is proposed.
- Additive change = MINOR bump of uarch-contract; breaking change = MAJOR bump.
- Names copy rk-sim's where rk-sim has the concept. The vendored round-trip test proves it.
- Units live in names. HardwareSpec inputs may carry cycle quantities; execution results
  must not. Only provenance.conditional_on[*].value may echo hardware stipulations in cycles.
  U-P3 must verify each path/value against the referenced proposed HardwareSpec.
- After changing anything: `make gen`, review generated contract/schema/ changes, update fixtures.

## After integration
rk-sim adopts this contract into rk/schema/characterization.py (rk-sim P18's boundary ADR).
From then on rk-sim is the source of truth and this directory vendors it back.
