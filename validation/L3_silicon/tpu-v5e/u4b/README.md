# U4b consolidated model and implementation proposal, revision 2

**The 52-unit implementation scope is approved. The revised model/interface awaits review.**
Continues published package `0d817eebc8ff2668eae277eebc8475b09122406f` (2026-10-20).
The user's approval covers required work and six benchmark classes, not device
observability, final benchmark acceptance, protected installation or U4 closure.

Recommend a complete pre-measurement interval model for TPU v5e in the existing native
engine: four matrix resources sharing local memory, explicit vector/reduction/control
work, aggregate HBM latency/bandwidth/window service, and declared state behavior. It uses
**9 published fact leaves and 17 numeric STUB estimates**, with bases, sensitivity ranges
and limitations. A numeric STUB is a supported provenance convention, not a reason to
refuse reference execution. The earlier published/independently-established-value gate
and target-deferral recommendation are withdrawn.

| Artifact | Concrete handoff |
| --- | --- |
| [MODEL.md](MODEL.md), [model-parameters.json](model-parameters.json) | Recommended parameter values, exact service laws, fact/estimate/model-choice separation, material uncertainties and remaining observation gaps |
| [REFERENCE.md](REFERENCE.md) | Primary-source reconciliation and limits on reusing component constants |
| [SUITE.md](SUITE.md), [suite-proposed.json](suite-proposed.json) | The unchanged 52 units; actual implementation-scope approval recorded separately from final agreement |
| [DISPOSITIONS.md](DISPOSITIONS.md), [candidate-dispositions.json](candidate-dispositions.json) | Unchanged disposition of all 70 historical candidates |
| [shape-regimes.json](shape-regimes.json) | Count-only shape coverage; final admitted-reference characterization still pending |
| [protected-amendments.patch](protected-amendments.patch) | Exact unapplied U0011/interface amendment, corrected to admit numeric STUBs and use the existing provenance conventions |
| [IMPLEMENTATION.md](IMPLEMENTATION.md) | One substantial implementation milestone, finite sequence and reusable test/code inventory |
| [ARITHMETIC.md](ARITHMETIC.md), [check_model.py](check_model.py) | Independent finite service/count/traffic/reduction/rounding examples, without engine execution or TPU duration predictions |
| [inputs](inputs/README.md), [prepare_inputs.py](prepare_inputs.py) | Exact proposed FP32 coefficient table and page indices, validated using the existing coefficient carrier |
| [EVIDENCE.md](EVIDENCE.md), [check_package.py](check_package.py) | Observed versus inherited checks; preserved historical suite and scope checks |

## Decision for review, with recommendation

Approve this revised model/interface as a whole for implementation, including the explicit
STUB estimates and chosen local-memory/reload abstractions. The nominal catalogue is fully
populated; it does not require published values for undocumented internals. Its weakest
prior is device entry at 1 us (diagnostic alternatives 0.1..10 us), followed by absolute
vector/control costs. These may be poor predictions; they are neither measured nor hidden.
The stress endpoints are not physical/error bounds. Deterministic checks establish only
that the implementation follows the chosen laws.

No additional scope or target decision is needed. Keep TPU v5e and all 52 approved units.
Actual XLA/event/materialization/retention correspondence has no demonstrated bound yet;
these are later observation/input-reconciliation obligations, not missing nominal model
parameters. Exact proposed coefficient bytes and page indices are now supplied; binding them into
the new mapped inputs remains part of implementation. Human L1 workings remain human work.

Once this interface is approved, proceed with the single substantive implementation and
integrated independent verification described in IMPLEMENTATION, rather than a sequence of
small A/B handoffs. The patch specifies semantics; generated executable carriers/schemas
are still implementation work under normal human protection. No new approval framework.

Ordinary installed execution/basic provenance, B laws, historical /2 restrictions and U0024
remain intact. No device access/spend, measurements, held-out tuning, dependency installation,
protected installation, CI polling, performance qualification or G3a/U4 closure is claimed.
