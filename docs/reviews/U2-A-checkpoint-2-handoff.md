# A2 bounded interface checkpoint — coordinator reconciliation

Status: **PARTIAL A2; interface handoff, not full runtime completion or U-REVIEW.**
Javid authorized this bounded handoff once consumer seams had focused passing tests.
All changes remain uncommitted on `u2/analytic`, HEAD
`1e9e794a84c5173812c23a1cf2fc04b85e6f6831`. No stage/commit/push/tag, vendor generation/adoption,
new dependency, human flag, agent, B/integration/main edit, or snapshot modification.
The coordinator transfers reviewed files; this author has not copied them to B.

## Received authority and identity

The 203-entry shared manifest verified relative to A before editing:
`e16f509285ad804c4765995f8e9e0cc1bc1099aded90b9e79d5db9f35924b420`.
The [received baseline](U2-A-checkpoint-2/received-baseline.json) records branch, HEAD,
complete status and 569 tracked/untracked file identities before A2 edits. The integration
and worker transfer receipts were read; 102 shared implementation and 99 historical JSON
support files were exact copies. H1/H2 were received B-owned inputs, not A-authored hardware.

Accepted U0003, S, D1–D12/R1–R2 and U0004/exact H1/H2 remain unchanged. Historical pending
labels in preserved proposal/hardware comments are not reopened. Original proposal116,
common baseline262, B1 addition45 and corrected A1 snapshot262 are verified by their
identified manifests. Earlier reports/logs/manifests remain historical bytes; the old live
A1 manifest is not regenerated to claim A2 tests existed at A1. Verify its old payloads in
the preserved corrected A1 root. See final verification and the A2 delta for changed live paths.
References remain draft-only, excluded from physical reference runs and L3 claims.

## Delivered consumer interfaces

Exact signatures, return fields and comparison against all 31 reconciled A1 callables are
in [api-inventory.json](U2-A-checkpoint-2/api-inventory.json). Existing A1 signatures and all
133 production contract/protocol schema bytes are unchanged. These are concrete A2 Python
interfaces over accepted carriers, not new shared fields or alternate wire schemas.

| Interface | Return and behavior |
| --- | --- |
| `hw.derive.derive_rk_params(spec)` | `Derivation`, whose `parameters` contain sourced values, formula IDs, sorted consumed/conditional paths and independent worst-claim summary. Decimal units; only declared formats; no efficiency fitting. This concretizes the earlier prose “params” return as the accepted Derivation carrier. |
| `hw.derive.resolve_hardware(spec, precision, *, frequency_ratio=1.0)` | Shared `ResolvedHardware`; integer-Hz ties-to-even, selected compute/storage checks, explicit DRAM scaling/block-geometry refusals. No execution-model efficiency in physical hardware. |
| `hw.export.export_component(spec, execution_model, *, component_id)` | `(ComponentExport, Derivation)`. Preserves complete original sourced truth and explicit model identity. |
| `hw.export.project_for_oracle(spec, truth, derivation, execution_model, *, upstream_sha)` | `(bytes, ExportBinding)`. Deterministic JSON plus one LF, also valid YAML; exact pinned five-field projection, all parameter/model losses, dual descriptor hashes and supported KV storage. Recomputes source derivation and refuses substituted/rehashed truth. No file writes or oracle calls in this function. |
| `engines.analytic.core.run_analytic(job)` | `EngineResult`. Physical resolved shapes/accesses, serialized matrix/vector time, aggregate/per-op rooflines, finite fractional ps, captured counts and scope. This low-level function accepts isolated validated jobs; full bundle/spec/assumption joins belong to the following boundary. |
| `workload.prepared.execute_prepared_point(bundle, point_hash, *, assumptions)` | `(EngineJob, EngineResult)` through the same reusable analytic function intended for table production. Validates captured bundle, model/shape/rank/operator inventory and capability joins, with no producer import/call. Preserves captured producer and mappings. |
| `workload.prepared.load_prepared_input(path)` | `PreparedBundle`, strict duplicate-key JSON, hashes, coverage and execution-shape checks. No remapping or preparation fallback. |
| `table.artifacts.load_verified_report_inputs(table_path, *, artifact_dir=None)` | Public `VerifiedReportInputs` NamedTuple of accepted carriers (listed below). Read-only, offline hash-name closure. Does not execute preparation or an engine. |
| `contract.tests.nominal_candidate.evaluate_nominal(value)` | Test-only `NominalOutput` from accepted `NominalInput`. Pure nominal algebra; own source-bound model identity, no expected fixture access or production selector. `candidate_identity()` supplies the identity required in the input. |
| `contract.tests.u2_prepared_adapter.evaluate_captured(bundle, *, model, model_shape, query, precision, tp, component_id, assumptions, frequency_ratio=1.0)` | `(EngineJob, EngineResult)`. Exact selection, A-F12 pre-call guard, then the same captured analytic boundary. No frozen-count echo or nominal substitution. |

Supporting `physical_assumptions()` and `engine_identity()` construct current identities;
`validate_execution_bundle()` is callable independently. `metric_contributors(job, bundle)`
returns selectors captured from physical operator/formula inputs. The candidate fingerprints
its own source at module load; evaluation itself performs no filesystem/network access.
It uses shared Query/ModelSpec/precision carriers, not an alternate operator model. B remains
responsible for external component binding/reference selection, vocabulary A-F12 and guarded
process orchestration before nominal evaluation. Candidate input cannot carry expected values
or a fixture ID, and its implementation does not import the producer, oracle or production code.

`VerifiedReportInputs` fields are:
`table, bundle, request, hardware, derivation, assumptions, model_card, jobs, results,
context, registry, dependencies, comparisons, evidence, sources, reviews, orderings,
verifications, artifacts, terminal_contributors`.
Each domain value uses the accepted shared type. `artifacts` is the verified identity index;
`dependencies.source_recipes` retains original purpose, granularity, dimensions and independent
model identity. B must retain these alongside terminal unions; neither is display permission.

The loader uses only `<64 lowercase hex>.json` within the chosen artifact directory, default
`table_path.parent/artifacts`. Raw source/export/oracle-manifest bytes use that same hash-name
layout and are verified as bytes when the declaring carrier identifies a raw dependency.
Hardware comes from the bundle, request is reconstructed from captured intent; an explicit
request companion, if present, must also agree. No path/URL/mtime lookup or directory globbing.
It checks jobs as well as results, source derivation, all-spec stipulated conditions, card
summary/model identity, context/comparison joins, reviewed closure, actual reference/export
files and raw source blobs. Source eligibility, physical truth/authenticity, ordering policy,
model badges, error bands and numeric display remain B-owned decisions.

## Source coverage and physical scope

For each row, loader computation coverage requires the exact actual result source for all
four counts, duration and U-C0 duration. For every OpResult it covers four counts, instances,
compute/memory/duration ps, intensity, achieved rate, ridge and matrix/vector/DRAM rates.
Required captured input selectors include the actual point/operator contents, repeat/access/
embedding-hit data, accepted algorithms, and timing rate leaves/frequency. They are derived
from the selected job's captured graph, never supplied as arbitrary caller selectors.
Per-op contributors stay scoped to that operator; timing conservatively retains the declared
physical rate inputs. Recursive validation keeps distinct source model/purpose/scope. Rehashing
or reviewing an omitted source does not bypass these checks. A1 ratio actual/reference and
adjustment checks remain unchanged and refuse the saved coordinator counterexamples.

This is computation-input/identity validation, not proof that an external producer actually
executed a capture. The loader does not rerun the model to authenticate captured arithmetic.
Input magnitudes, all other report surfaces and attribution presentation still need B's
explicit recipe/display coverage; this handoff does not claim that a renderer exists.
The physical core has no measured errors/energy/residency prediction: busy times, diagnostics,
trace and simulator metrics stay null. No inference of silicon accuracy follows from tests.

## Actual H1 export

[Export files](U2-A-checkpoint-2/export/) contain actual accepted npu-l4 truth, derivation,
nominal execution-model input, five-field descriptor, binding and `PIN`.
The accepted new nominal factor is explicitly 1.0/STUB/unvalidated. Retained upstream .55
inputs remain untouched, and a separate .55 test proves it is consumed, not silently replaced.

- Descriptor bytes SHA256: `2ea53cfd0b039908f35e67cc21d658f634e714605cdbc8446e9708736bf738ea`.
- Descriptor content identity: `sha256:72d507def6f3939cf3073aacf004258bdf63258af60a2fde48977e7f3a60468e`.
- Truth identity: `sha256:9fdbe8d7f9d1b05cd8f44ef5d893da73742ae3b5b2acc9bde4584f14a2771d23`.
- Upstream pin: `1e5706e0ebfcc67c1a7333079a35b75f693e9963`.

The guarded [loader probe](U2-A-checkpoint-2/export-loader-probe.json) accepted actual H1
BF16 selection at this pin, badge STUB, zero oracle calls. All oracle count/duration entry
points were replaced by traps. This is local deterministic export/selection, not vendor
artifact generation, B's matrix tooling, expected-duration generation or adoption.

H1 bytes remain `41731f6ac7fe99aaf221edaf917ffdd03cd0fcdd8149ee5f5110bfe42a5911c0`;
H2 remains `e12d08d40e7b3c0e7ab1443141745a6c082ee544ecfc43c5609c8cd289a35d9e`.

## Tests-first and executed evidence

Each runtime body followed independent failing tests: nominal candidate, derivation/export,
analytic, captured adapter and loader. `*-tests-first.py.txt` and `*-before*.txt` preserve
those stages. Early loader attempts had fixture filename errors; `loader-tests-red.txt`
is the corrected pre-body run (10 missing-module failures), not those earlier path failures.
Nominal negative inputs initially hashed omitted defaults; the fixture was normalized before
hashing so unit/rate cases reached their intended checks. No oracle expectations were computed.

The later per-op omission test demonstrably failed with DID NOT RAISE before coverage was
added, then passed with its unchanged valid control. That long-running pre-fix trace displays
subsequently formatted source lines; its observed failure and executed test semantics are
preserved, and it is not represented as a byte-pinned source snapshot. The card energy-edge
counterexample similarly failed before its typed-join correction. Initial and corrected logs
remain separate; `check-results-v2.json` identifies final checks, while `check-results.json`
and unsuffixed logs identify the earlier 598-pass run.

Final run: **599 passed, zero skipped**, in 167.39 seconds. Mypy (42 source files), ruff,
contract/protocol freshness and whitespace checks all passed; exact results are recorded in
`check-results-v2.json` and `regression-final-v2.txt`. Three nominal schema roots and four
accepted nominal literals also passed independent system-jsonschema checks.
The suite includes all contract tests, prompt-sync, third-party, preserved A1 source-binding
counterexamples, and A2 derivation/analytic/prepared/loader tests. The four A1 nominal carrier
skips are replaced by actual carrier parsing plus independent nominal execution, perturbation
and file/network/import-trap tests. Production schema freshness and isolated nominal schema
freshness remain separate; no production nominal engine is introduced.

Environment: existing Python 3.12.14 at
`/home/jjaff/AI-infra-simulation/rk-uarch/.venv/bin/python`, `PYTHONPATH=contract:src`, local
WSL2 Linux. Tests use `-B -m pytest -p no:cacheprovider`; mypy uses `--no-incremental`, ruff
uses `--no-cache`. Exact argv/cwd/environment/return codes/timings are in the check records.
All 133 existing production schema bytes remain unchanged. New three schema mirrors live
only under `contract/tests/fixtures/u2/` and match the accepted nominal fields/required sets.

[Captured replay](U2-A-checkpoint-2/captured-replay-results.json) executed independent captured
work with producer/oracle imports trapped during execution. The new run's input explicitly
rebinds only assumptions/model identity from the historical proposed fixture; captured graph
and producer stay unchanged. At supported single-worker execution, thread environment settings
1 and 4 and different PYTHONHASHSEED produce identical job/result bytes:
`sha256:3446e1f04b59efbe481101d71b482ca5dd7e3ca4c7ee672fc15425b3916bbd32`.
The input and both outputs are retained, not confused with old hand-authored expected results.
Independent tests pin 1 ps and fractional ps, compute tie precedence, packed per-operand byte
rounding, tiny decoder counts/timing, aggregate/per_op conservation and D7 selected-rank [1,0]
gather reads. Invalid [1,1], wrong dimensions/precision and A-F12 fail before core execution.

## Remaining A2 work — not delivered by this interface checkpoint

- Standalone `ModelSpec`/`ModelShape` producer, high-level shape library/convenience path,
  explicit synthetic assignment opt-in, identity/characterize/deviation workflows.
- Table builder/serialization and CLI/subprocess transport, sole table seconds conversion,
  complete portable table package production and same-byte standalone→disabled-producer replay.
  The current demonstration is captured job/result execution, **not standalone table production**.
- Known weight/KV capacity orchestration, total-peak-null warnings and complete residency
  refusal matrix. No completed residency proof is claimed by the current captured boundary.
- Broader physical acceptance matrix: causal/full-square and all/last-token head combinations,
  materialized unfused attention, MoE/router/tied-weight residency, padding/replication/extents,
  H2 fp8 characterization and full capability/frequency/property tests. Code paths alone are
  not completed acceptance evidence. Full hardware unrepresented/report contribution audit
  remains with table/characterize integration.
- B-produced comparison inventories, all adopted nominal fixtures, B2 eligibility/renderer
  integration, exact matrix/refusal tooling and B-F16. No B report code is present/runs here.
- Human two-run generation/adoption, independent fresh review loops, published same-commit
  U0021 host/CI checks and sprint closure remain separate.

No accepted threshold, matrix, model ownership or hardware decision changes. No new field or
policy disposition is requested. The interfaces above are ready for bounded coordinator/B
consumer review; full A2 completion is not asserted. The remaining list is execution work,
not a request to reopen accepted U0003/U0004. Loader checks are conservative and costly on
large synthetic recipe inventories; observed suite timings are recorded, not extrapolated
into a performance claim. No substantiated person-hour re-estimate: A140–222/B100–154 plus
fresh reviewer16–24 planning ranges remain unchanged.

## Exact checkpoint and proposed commit

`U2-A-checkpoint-2/SHA256SUMS` is the full uncommitted changed-path payload manifest relative
to HEAD, including received/prior A1 payloads and new A2 work; it excludes only itself.
`checkpoint-paths.txt` lists this checkpoint's exact added/modified paths versus the received
baseline, including its manifest. `changes-from-received-baseline.json` supplies explicit
old/new byte hashes and categories. Its self/hash-manifest exclusions avoid recursive hashes;
the full manifest binds that delta. `changed-paths.json` identifies the complete payload list.
These identify uncommitted bytes, not branch protection or publication.

Proposed message, **not committed**:
`feat(u2): add A2 export, captured analytic, nominal and offline consumer seams`

Stop here for coordinator reconciliation. Continue remaining A2 work in the existing author
session after that handoff; this is not the fresh independent U-REVIEW loop.
