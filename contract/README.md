# contract — THE shared vocabulary (human-owned)

Everything rk-sim and uarch exchange is defined here, and nowhere else: SourcedValue (with
kind claim|stipulation), HardwareSpec, the operator vocabulary, ModelShape, the
CharacterizationRequest, the UarchCostTable, the ModelCard, hashing and the error taxonomy.

## Rules
- Agents propose changes and stop. Both founders approve; every change has an ADR.
- Additive change = MINOR bump of uarch-contract; breaking change = MAJOR bump.
- Names copy rk-sim's where rk-sim has the concept. The vendored round-trip test proves it.
- Units live in names; no field carries cycles.
- After changing anything: `make gen`, commit contract/schema/, update fixtures.

## After integration
rk-sim adopts this contract into rk/schema/characterization.py (rk-sim P18's boundary ADR).
From then on rk-sim is the source of truth and this directory vendors it back.
