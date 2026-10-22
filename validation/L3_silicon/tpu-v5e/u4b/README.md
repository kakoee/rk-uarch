# U4b model and 52-unit suite — installed

The complete reviewed v2 implementation was human-installed at `3626273` and published
with verification at `6d443e1` on 2026-10-22. It implements the approved nominal TPU v5e
model and all 52 selected units in the existing native engine. B1 and B2 are resolved;
F3/F4/F6 remain explicit limitations, and F5's staging behavior is disclosed.

**Current benchmark and measurement status:** [BENCHMARK-PLAN.md](../BENCHMARK-PLAN.md).
It connects all 52 IDs to the saved campaign and proposed device envelopes, and separates
completed simulator verification from later device observations. Javid accepted the
52-unit agreement, reference APIs and assisted L1 workings; the
[closeout acceptance](../../../../docs/reviews/U4-closeout-acceptance.md) records the exact
G3a adjustment. The U4 tag awaits completed CI. Installation is not TPU accuracy validation.

| Artifact | Role |
| --- | --- |
| [MODEL.md](MODEL.md), [model-parameters.json](model-parameters.json) | Approved nominal laws and catalogue: nine fact leaves and 17 numeric STUB estimates; no silicon accuracy claim |
| [REFERENCE.md](REFERENCE.md) | Dated source reconciliation and rationale; proposal-era statements are historical |
| [SUITE.md](SUITE.md), [suite-proposed.json](suite-proposed.json) | Exact 52-unit definitions and planned device envelopes; original JSON status/signature fields are preserved, with current status in BENCHMARK-PLAN |
| [DISPOSITIONS.md](DISPOSITIONS.md), [candidate-dispositions.json](candidate-dispositions.json) | All 70 historical candidates accounted for without expanding the selected suite |
| [shape-regimes.json](shape-regimes.json) | Count-only coverage; Javid accepted the reference-API preparation route |
| [inputs](inputs/README.md) | Supplied RoPE coefficient table and gather indices used by preparation |
| [ARITHMETIC.md](ARITHMETIC.md), [check_model.py](check_model.py) | Independent arithmetic and catalogue consistency checks; not human L1 workings |
| [EVIDENCE.md](EVIDENCE.md), [check_package.py](check_package.py) | Historical proposal checks, preserved with their original scope |
| [IMPLEMENTATION.md](IMPLEMENTATION.md), [protected-amendments.patch](protected-amendments.patch) | Historical implementation plan and early amendment; do not apply that old patch over the installed implementation |

The [complete v2 handoff](../../../../docs/reviews/U4b-native-reference-implementation-v2/README.md)
and [human installation record](../../../../docs/reviews/U4b-native-reference-install-decision-v1/next-decision.md)
are the implementation references. The original model proposal began at `0d817ee` and
was revised at `180c6b9`; those historical records are not current installation instructions.

Ordinary installed execution and basic software/model/input provenance remain in use.
No executable attestation, custom startup assurance or build tracing is reinstated.
The nominal model may be inaccurate; its STUB estimates, compiler-chosen mapping and
unobserved device behavior remain visible. Predictions, device work, U0024 qualification
and U4 closure have not been performed by updating this page.
