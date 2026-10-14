# Concrete file/import/read boundary

The current exact delta is the Git diff in `protected.patch`; schema/fixture bytes are part
of that patch, not a separate copied tree. No root initializer, existing generator,
`hashing.SELF_FIELDS`, analytic dispatch, hardware exporter or legacy carrier is edited.

| Added path | Imports / reads / role |
| --- | --- |
| `contract/uarch_contract/mapped.py` | stdlib `fractions`, `typing`; Pydantic; relative `common`, `hardware`, `hashing`, `prepared`, `rotary_v2`, `table`; local stdlib `math` in ratio validation. Reached legacy validators have their existing conditional imports. No TYPE_CHECKING edge, dynamic import, file, environment or network read. Admission receives registry/profile/hardware/bundle as explicit objects. |
| `contract/uarch_contract/generate_mapped.py` | stdlib argparse/json/pathlib; `.mapped.SCHEMA_ROOTS`. Reads exact `contract/schema/mapped/*.json`; writes only in generation mode, check is read-only. |
| `contract/schema/mapped/*.json` | Eleven generated roots: MappedBundle, MappedPoint, TaskGraph, MappedEngineJob, MappedEngineResult, NativeTestProfile, NativeTestRegistry, ResolvedMappedHardware, WorkCounts, TrafficCounts, Observations. |
| `contract/fixtures/mapped/{component,kernel,kernel-job,profile,registry}.json` | Explicit source-free component and fixed-delay input examples; full baseline HardwareSpec inline. Registry currently has no synthetic variants; baseline is not test-only. Profile binds exact graph/point/clock/seed. No native results. |
| `contract/tests/mapped/test_admission.py` | pytest; explicit mapped and hash imports; local imports of old protocol roots for negative routing and the mapped generator for freshness. Reads only named fixture files plus generated mirrors for checks. No production expected timing/count helper. |

Python loads `uarch_contract/__init__.py` before the submodule. Its existing re-exports and
transitive imports remain byte-identical and are not ignored by the audit. Existing reached
`prepared.validate_prepared_op` imports `.comparison` locally. No mapped re-export is added.
The package remains a leaf with respect to `rkuarch` (the tests import old engine protocols).
The test environment uses the existing `uv.lock`; no Python dependency is added.

Unchanged oracle path: `scripts/vendor_rk.py::ORACLE_PROGRAM` and its pinned upstream
subprocess. Nominal staging remains `scripts/u2_inputs.py` → `uarch_contract.exports` /
`rkuarch.hw.export` → `hw.derive` → `engines.protocol.ResolvedHardware`, including parent
initializers. Under live U0002 all new contract Python is bound even without a reverse edge.
Under prospective D2, B must confirm actual reachability/data rather than inherit a count.
No future support-file count is predicted.

After protected acceptance, the planned M boundary uses direct imports only:

| Planned consumer | API / reads |
| --- | --- |
| `src/rkuarch/workload/mapped.py` | `strict_json_loads`, `MappedBundle`, `admit`; caller-selected saved JSON, explicit registry and profile bytes and pinned loader trust identity. No ambient registry search, producer fallback or implicit hardware selection. |
| `src/rkuarch/mapping/component.py` and `mapping/policies/ws_rowsplit.py` | existing PreparedOp/HardwareSpec → mapped TaskGraph; explicit supplied hardware only, complete inputs/transfers/coverage; first consumer B. |
| `src/rkuarch/engines/protocol_mapped.py` | direct re-export of exact MappedEngineJob/Result and validation; engine schema mirror generation explicit, no changes to old dispatch. |
| `src/rkuarch/engines/native/` | K2 writer/runner/parser; loader-selected bundle/profile/registry and accepted build identity; Rust executable/lock and receipt reads require their own actual audit. |
| B report/provenance and later A table/capture | deny verification_only and registered test-spec hashes; component results cannot become model rows. B owns its consumer changes. |

Any later common helper, root re-export, schema registration, dispatch edit, registry file,
hardware fixture or environment read must update this inventory and B's audit before use.
The future test-spec path is B-owned `hw/designs/test-fixtures/`; none is installed here.
Registry/profile expectations are proposal input identity, not proof of human approval.
