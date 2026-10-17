# Production hotspots: consultation and protected proposals

No production or protected edits are installed by this work. Consultation was requested
through the coordinator for A; no duplicate checks were requested. A's response, if any,
will be recorded in the final handoff. These proposals do not block B-owned improvements.

The focused cProfile run at `6208968` selected exactly the three nodes in `profile.time`.
It took 59.67 s with profiling overhead; cumulative values overlap and must not be added.

| Location / owner | Profile observation | Bounded future proposal and required safeguards |
| --- | --- | --- |
| `src/rkuarch/table/artifacts.py::_load_verified`, A | 12 calls, 24.289 s cumulative | A to inspect repeated immutable parsing within one public operation. Keep independent public input/source/currentness verification and reject changed bytes. No cache of acceptance across calls or identities. |
| `src/rkuarch/workload/prepared.py::validate_execution_bundle`, A | 618 calls, 17.690 s cumulative | Review repeated preparation only where the caller already owns identical immutable inputs. Do not remove boundary validation or change model semantics. B's installed optimization stays in the report harness and still invokes the real factory on first use. |
| `contract/uarch_contract/hardware.py::hardware_unit_rule`, both humans | 246,470 calls, 19.614 s cumulative; `re.escape` 6,735,331 calls, 10.388 s | Separate protected proposal could compile ordered static rule expressions once. Must preserve matching order, all accepted/rejected paths, unknown-unit refusal, strict schema behavior and currentness identities. No implementation or claimed speedup here. |
| `contract/uarch_contract/hashing.py::canonical_json`, both humans | 80,492 calls, 15.158 s cumulative; recursive normalization 11.955 s | Do not shortcut canonicalization. Any future serialization optimization needs exact-byte equivalence, non-finite/boolean/order/Unicode controls and separate protected review. |

No proposed production change touches component-owned installation identities, transient
accumulators, installed contracts, historical reports or the sealed native runtime. New
pytest workers/dependencies, hosted artifact-upload actions, or normative cadence changes
also require separate proposals. Current worker default and all release/replay counts remain.
