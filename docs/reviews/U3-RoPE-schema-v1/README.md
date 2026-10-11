# U0022 additive schema and implementation proposal — Lane A

**For coordinator review, not implementation permission.** Based on main
`f62eb7025dd5a48f03a81e92bc334f58bfb2a202`, fetched/integrated and verified as an ancestor.
Javid is the acting human decision-maker for both lanes; no Reza approval is claimed.
[U0022](../../decisions/U0022-explicit-rope-semantics.md) and
[U0006](../../decisions/U0006-what-verification-can-and-cannot-establish.md) are accepted. Their
semantics are not questions in this proposal. The
[acceptance package](../U3-RoPE-and-verification-v1/README.md) authorizes this review-only step.

This package specifies additive carrier shapes, admission obligations, ownership and the
human source-currentness lifecycle. `schema_prototype.py` is an executable **documentation
prototype** using current Pydantic/carrier primitives. It neither prepares nor executes a
workload. `small-inputs.json` contains complete synthetic coefficient/profile/Q/K-node inputs;
it is not a capture, a named-model table, a job/result or an adopted oracle. The proposed
prose patch is also inert. No production or protected file is changed.

## 1. Exact additive carrier delta

The field definitions in [schema_prototype.py](schema_prototype.py) are the reviewable schema
prototype; unchanged fields retain their existing types, required/default status and extra-field
refusal. Overrides are new classes, never mutations of old classes/enums. Print all complete
proposed root schemas with:

```sh
uv run --no-sync python docs/reviews/U3-RoPE-schema-v1/schema_prototype.py --schemas
uv run --no-sync python docs/reviews/U3-RoPE-schema-v1/schema_prototype.py
```

These commands do not write generated schemas. JSON Schema carries syntax; coefficient
finite-bit/hash checks and the graph/identity guards below require semantic validation too.
The prototype implements only coefficient shape/finite-bit/hash checks and inherited carrier
checks. It deliberately does **not** claim that a schema-valid graph/job/result is admissible.

Proposed protected module: `contract/uarch_contract/rotary_v2.py`; new dedicated generator
`contract/uarch_contract/generate_rotary_v2.py`, output `contract/schema/rotary-v2/`.
Human reviews/installs these separately; nothing is installed by this package. Export exactly:

| New root | Base or fields added/overridden |
| --- | --- |
| RotaryCoefficients | FrozenModel; format, coefficients_hash, position_count, rotary_dim, dtype, cos_bits, sin_bits, Producer as U0022 |
| RotaryEncoding | Required intent/cache profile: kind, R (`rotary_dim`), pairing, coefficients_hash, position_policy, cache_key_state, numeric_policy |
| RotaryBinding | target, coefficients_hash, pairing, numeric_policy, position_ids, input_op_id |
| RotaryOpSpec | OpSpec shape with operator fixed to `rotary_embedding`; existing Operand primitives |
| PreparedOpV2 | PreparedOp fields; spec = old OpSpec OR RotaryOpSpec; **required** rotary = RotaryBinding OR null |
| OpGroupV2 | OpGroup fields; ops = nonempty PreparedOpV2 tuple |
| PreparedGraphV2 | PreparedGraph fields; groups = nonempty OpGroupV2 tuple; required kv_key_encoding = RotaryEncoding |
| PreparedPointV2 | PreparedPoint fields; graph = PreparedGraphV2 |
| RequestIntentV3 | RequestIntent fields; contract `uarch-contract/0.3`, accounting `resolved-ops/2`, mapping_policy `analytic-ops@2`, required position_encoding |
| CharacterizationRequestV3 | RequestIntentV3 plus required prepared_input_hash |
| PreparedBundleV2 | PreparedBundle fields; format `uarch-prepared/2`, intent/points use new roots, required coefficients = RotaryCoefficients |

Proposed A module `src/rkuarch/engines/protocol_v2.py` exports four roots in
`src/rkuarch/engines/schema/v2/`: ModelIdentityV2 (physical-resolved, version `2`),
EngineIdentityV2 (analytic, version `resolved-ops/2`, ModelIdentityV2), EngineJobV2
(old job fields, protocol `uarch-engine/2`, accounting `resolved-ops/2`, new point/engine,
required coefficients), EngineResultV2 (old result fields, protocol `uarch-engine/2`,
new engine). Counts, OpResult, scopes, diagnostics and fidelity use existing primitives;
OpResult.scope.op_class already accepts nonempty strings, including rotary_embedding.
No simulator metrics or traces become available; null requirements stay in force.

The two existing generators compare flat `*.json` inventories and reject unexpected roots.
Keep them and their old output bytes unchanged. Dedicated new generators check the exact
new subdirectory inventories; future CI/schema tests invoke **both** families. Do not add
v2 roots to old `SCHEMA_ROOTS`, `Operator`, version constants or generic old artifact dispatch.
The proposed new roots are concrete schema choices for review; U0022's version values are
already accepted. No protected table/report schema expansion is included.

## 2. Authenticated closure and required semantic admission

**Concrete closure choice:** inline exactly one complete `coefficients` object in each
PreparedBundleV2 and EngineJobV2. Job coefficients must equal bundle coefficients. This costs
serialized duplication but leaves each engine job self-contained; no ambient resolver, URI,
producer execution or hidden table cache is needed. A result authenticates that closure through
job_hash. Coefficients are shared allocation, not charged twice merely because two carriers
serialize them. No new image/container identity is appropriate to this analytic-only boundary.

Use existing canonical JSON/content_hash/verify_identity rules after parsing the new roots:

1. Hash coefficients excluding only coefficients_hash. Check array rows/width, even R>=2,
   strict integer extents, exactly eight lowercase hex digits per finite IEEE binary32 scalar.
   Signed-zero bit strings remain distinct. No sin/cos generation or unit-circle inference.
2. intent_hash = content_hash(intent), including full position_encoding. Each point
   payload_hash excludes only itself and includes every graph edge/binding/position/omission.
   bundle_hash excludes only itself and includes coefficients, rank, hardware and all points.
3. CharacterizationRequestV3 is the exact intent plus prepared_input_hash=bundle_hash;
   hash the whole request. Validate hardware hash, model/shape parity, rank, precision,
   grid coverage, frequency/state, omissions and all existing nonrotary constraints.
4. Job hash excludes only job_hash. Require exact point membership (including full equality),
   point_hash=point.payload_hash, request/bundle hashes, coefficients equality, producer/rank,
   hardware hash, assumptions, fidelity, mode, precision, state and seed duplication. Validate
   resolved hardware leaves/rates against the sourced hardware using A's derivation checks.
5. Result hash excludes only result_hash. Require exact admitted job/engine/fidelity identities,
   one unambiguous scope per expected op/group with repetitions, no missing/extra rotary result,
   exact count/traffic conservation and the existing aggregate/per-op roofline/attribution rules.
   Replay must independently recompute the declared work; self-consistent invented totals do
   not pass. Require the active v2 implementation and its assumptions, not merely version `2`.

The current request_hash/intent_hash/point_hash/bundle_hash helpers parse old roots; add
version-specific helpers in rotary_v2 instead of widening these functions. Canonical primitives
are reusable. Current artifact_identity/closure dispatch stays v1. Inline closure is validated
by the explicit v2 loader. AssumptionSet retains `uarch-assumptions/1`; its model must equal
EngineIdentityV2.model. Retain existing algorithm entries and add exactly
`"rotary": "rope-3e-plus-explicit-casts/1"`; append U0022's conversion, coefficient-read,
precomputed-input, unsupported-format and unknown-total-peak limitations. Hash this new set;
never reuse the v1 assumptions hash or claim coefficient identity proves model equivalence.

**Graph guards (future executable tests, not implemented by this prototype):**

- Every decoder group contains exactly one node ID rope_q and one rope_k, with matching
  targets; head/tail contain none. IDs remain group-local under existing group rules.
  Rotary binding is nonnull iff spec.operator=rotary_embedding. No rotated V, aliases,
  unknown operators, hidden fusion or extra work_repeat/weight_copies. Both equal 1.
- Dimensions are exactly B,H,S,D,R,P with P=R/2, even 2<=R<=D; reductions empty; operands
  exactly X/Y[B,H,S,D], Cos/Sin[B,S,P]. X/Cos/Sin read, Y write; contiguous, null block sizes,
  fusion none, kv_access null, embedding_local_tokens null, padding empty. Coefficients are
  FP32; X/Y share the declared supported activation/KV format. Existing hardware/rate
  admission still applies. FP32 coefficient storage is not an FP32 matrix operation and
  must not accidentally demand a separate FP32 matrix peak from a BF16-only design.
- `rotary.input_op_id` names the corresponding unique same-group q_projection or k_projection;
  depends_on is exactly that single ID. Projection Y[M,N] corresponds to X[B,H,S,D] with
  M=B*S and N=H*D: logical element Y[b*S+s,h*D+d] feeds X[b,h,s,d]. This is an
  explicit logical correspondence, not a claim that flattened contiguous buffers have the
  same byte order or that a physical transpose is free. The analytic profile retains U0022
  operand accounting; it supplies no executed layout/transfer evidence. Shapes alone are
  insufficient.
- K append's `K` input comes from rope_k.Y; V append's `V` from v_projection.Y. There is one
  kv_write, with dependency set {rope_k, v_projection ID}. Its existing K_cache/V_cache
  outputs, page capacity and valid-token policy remain unchanged.
- Fused attention Q comes from rope_q.Y, K from the appended rotated K_cache and V from
  V_cache. For the existing example IDs q/k/v/kv/attn, the exact changed lists are
  `rope_q:[q]`, `rope_k:[k]`, `kv:[rope_k,v]`, `attn:[rope_q,rope_k,v,kv]`.
  These are fixed operator-role correspondences checked against operand names, not a new
  tensor-reference language. Preserve acyclicity and existing unique producer rules.
  For unfused work, QK's Q/K use the same rotated/cache sources, QK→softmax→AV stays explicit,
  and AV's V comes from V_cache; reject bypasses even when shapes and hashes agree.
- Graph.kv_key_encoding equals intent.position_encoding in every field. Both bindings equal
  its table hash/pairing/numeric policy and R. Decode C=total_context_tokens/B must be integral;
  S=1, each position row=[C-1], table covers that row. Incoming K positions 0..C-2 are declared
  rotated under this same profile; unseen cache values are not authenticated by counts.
  Prefill S=prompt_tokens, positions=0..S-1 per sequence, no prior cache. No offsets/ragged/
  sliding positions, cold-context reset, table swap for old keys or second append.
- H is resolved Hq or Hkv respectively, never an extra tp division or GQA replication over Hq.
  Preserve the existing K projection's required Replication records on rope_k; validate them
  against global KV heads, local heads and tp. Selected-rank and representative-rank proofs,
  conserved embedding hits and group.repeat rules remain. No new rotary padding.

## 3. Old/new admission and unchanged legacy identity

Routing inspects explicit version tags **once**, selects one strict parser, and never retries
another family after rejection. Unknown/missing tags fail; parse failure cannot trigger upgrade.

| Submitted closure | Required future outcome |
| --- | --- |
| Exact v1 intent/bundle/job/result + matching v1 assumptions/identity | Existing v1 admission/replay; byte-identical interpreted inputs/results |
| Complete valid v2 closure, Q/K/coefficients/rank and v2 assumptions/identity | Explicit v2 admission only, both analytic modes |
| v2 request through v1 API; v1 request through v2 API | Refuse version/extra fields; no inferred position method |
| v1 operator enum given rotary_embedding, or v1 PreparedOp given rotary (even null) | Refuse; old vocabulary unchanged |
| v2 point in protocol/1, protocol/2 with old point or model/version/assumptions | Refuse nested schema or identity mismatch |
| protocol/1 body relabelled with v2 engine identity | Refuse at semantic engine-identity check; old EngineIdentity alone has permissive version strings |
| v1 result joined to v2 job, or v2 result joined to v1 job | Refuse before arithmetic/evidence eligibility |
| New request retaining old prepared_input_hash or result rehashed after dropping/duplicating a node | Refuse closure/graph/work check, even if individual hashes are valid |
| Coefficient missing/tampered, cache/profile mismatch, unsupported precision/rank/padding | Refuse; no fallback or placeholder completion |
| Old captured evidence under changed support bytes | Strict current acceptance refuses stale receipt; historical reproduction uses its recorded Git version |

**Concrete implementation choice:** keep `engines/analytic/core.py`, its entry point
`engines/analytic/__main__.py`, protocol.py and the v1 workload/capture path byte-for-byte
unchanged. At this base core.py hashes to
`sha256:fa3938f8c009c7b80700d35feba7504e4b4da06e628d2e387480c358963974ea`.
It continues to self-identify its own bytes. Add `engines/analytic/dispatch.py` for explicit
protocol selection and `engines/analytic/rotary_v2.py` for the new analytic implementation.
Dispatch sends v1 unchanged to the old entry point; v2 uses only the new path. Existing CLI
v1 table/report commands need not change to add this boundary. Dispatch itself is source-bound;
old core identity does not claim to identify the new dispatcher or the whole environment.

Propose v2 engine/model implementation_hash as content_hash of the **small direct execution
closure**: tagged `analytic-rope-implementation/1`, a sorted path→SHA256 map of
analytic/rotary_v2.py, analytic/dispatch.py, engines/protocol_v2.py, workload/prepared_v2.py,
contract/uarch_contract/rotary_v2.py, and any existing runtime modules actually reused by
those modules. Freeze the exact transitive local dependency set at implementation review;
add/remove a dependency changes this identity. This is a reproducibility binding, not a
second repository manifest. Dependency-set completeness is unresolved until code exists;
no fabricated v2 runtime hash is supplied now. U0002 separately binds the full support set
and lock. V2 must not call v1 core on a graph with RoPE removed and present that as old work.

A new explicit v2 capture API can return bundle/request/jobs/results with their new roots;
no existing CapturedWork return annotation or consumer is widened implicitly. Existing
`table/build.py::CapturedWork`, B's provenance loaders and report/verification interfaces
remain v1. Full v2 public table/report attachment requires a later coordinator-reviewed
contract/ownership change: do not wrap new work in old table carriers to bypass it. Until
then v2 capture is not advertised as an end-to-end public table/report workflow. Preserve
all existing v1 public workflow/replay tests. No old payload is migrated or rewritten.

## 4. Complete small inputs and discriminating tests first

[small-inputs.json](small-inputs.json) has four complete carrier instances. They use a
three-position synthetic R=2 table and B=S=1,D=2,Hq=2,Hkv=1 BF16 nodes at position 2.
No named model is asserted. The producer identifies this documentation prototype, not an
installed coefficient producer. These are positive **carrier** examples; they do not supply
hardware, projections, full graph or assumptions and cannot be submitted as a complete job.
A whole-job positive fixture must supply the complete closure in §2 before runtime admission.
The prototype checks four positive instances, ten syntax/coefficient refusals, and the
15 schema roots. Coefficient finite-bit checks are validation, not tensor arithmetic.

Future tests must be written and observed failing for the intended reason before runtime
changes. Expected numbers are independent literals, with no production count/traffic imports:

| Case (Hq=2,Hkv=1,D=4 unless stated) | Exact expected Q/K vectors; added read/write bytes |
| --- | --- |
| B1 decode C17, R4, BF16; same FP16 | 40 / 20; 56 / 24; matrix delta 0 |
| Same FP32 | 24 / 12; 80 / 48 |
| R2 partial BF16 | 20 / 10; 40 / 24 (full D tail transfers retained) |
| B2 prefill S3, R4 BF16, causal and full-square | 240 / 120; 336 / 144 for either mask |
| Two repeats of first row | total 120 vectors, 112 reads, 48 writes; no head/tail repeat |
| Global Hq4/Hkv1,tp2 selected ranks 0 and 1 | each rank first-row counts, including K=20; no second tp division |
| C33 or 16-token page rounding in first row | same rotary counts; positions/table coverage and KV traffic differ |
| Small-input nodes in this package | Q20/K10 vectors; total 28 reads/12 writes; matrix delta 0 |

Pairing discriminator: X=[1,2,3,4], Cos=[0,1], Sin=[1,0], FP32,R4 gives adjacent
[-2,1,3,4], split-halves [-3,2,1,4], both 12 arithmetic ops. R2 uses [0]/[1] and
leaves [3,4] unchanged, six ops. Test reference must explicitly implement separate FP32
RNE multiply/add steps and BF16/FP16 output rounding, with ties/cancellation witnesses;
no FMA or implicit library default. This tests the declared transform, not numerical execution
by the count-only analytic engine. Identity coefficients do not erase declared work.

Required mutation/refusal tests, including mutations followed by valid rehashing:

- Remove/double Q or K; put either in head/tail; rotate V; bypass rotation in attention or
  kv_write; rotate all cached C tokens; use wrong same-shaped projection; swap Q/K targets.
- Omit casts; multiply coefficient reads by H; omit one node's reads; retain across layers;
  page-round tokens; drop partial-R tail traffic; repeat twice; substitute Hq for Hkv.
  Verify matrix/parameter counts unchanged and known coefficient allocation once per table.
- Mixed compute/KV, FP8/TF32/block formats, unsupported hardware/rates; invalid rank,
  wrong replicated-K metadata, unequal hit counts falsely labelled rank-equivalent, rotary
  padding, odd/oversized R. Reject unsupported forms, not count them as zero.
- Cache encoding, positions, pairing, numeric policy, row coverage and coefficient hash
  tampering; infinity/NaN, malformed bit strings and boolean extents. Change finite table
  bits and rehash only the table (stale links must fail); independently use fully rehashed
  v2 inputs with v1 assumptions (the model/algorithm join must fail). A fully rehashed new
  table with compatible v2 assumptions is a distinct new input, not automatically invalid.
  It cannot reuse old input/result identities or claim unseen old cache values were converted.
- Producer-disabled imported replay: block preparation and coefficient creation, then
  admit exact explicit inputs and get identical jobs/results for three repeats in both modes.
  No stage reconstructs omitted positions or coefficients; missing data refuses.
- Paired v1/v2 request/job/result refusal matrix above, old schema output bytes unchanged,
  legacy core hash unchanged, existing capture/table/report bytes and badges preserved.
  Changed implementation bytes with the same version string refuse stale reports/results.

All six mutation/refusal bullets and the literal runtime expectations are **unimplemented tests**.
This package does not count them as passed or as U0006 executed relation evidence.

## 5. Ownership, order and U0002 integration gate

Proposed ordered work after coordinator schema review and human protected-schema decision:

1. A writes independent literal/graph/replay/version tests in new
   `tests/unit/test_u3_rope_*.py` and `tests/integration/test_u3_rope_replay.py`.
   Human owns corresponding new `contract/tests/test_rotary_v2.py` and protected schema
   installation; A supplies the exact proposal. Do not change golden expected payloads.
2. Human installs reviewed contract roots/generator/schema mirrors. A implements new
   protocol_v2, strict v2 workload loader/hash joins, then explicit producer with required
   coefficient input, then analytic v2 and dispatch. Keep v1 module bytes unchanged.
   Proposed A additions: `workload/prepared_v2.py`, `workload/producer_v2.py`,
   `engines/protocol_v2.py`, `engines/analytic/rotary_v2.py`, `engines/analytic/dispatch.py`,
   `table/capture_v2.py`. Add any imported implementation modules to the reviewed identity
   closure; generator code is support-bound even if not in engine execution closure.
3. Coordinator reconciles with B **before** any shared API or file edit: inline coefficients
   versus future declared artifact closure; v2 assumptions/model identity; future relation
   domains and replay corpus; metric-contributor selectors for rotary binding/positions/
   coefficients; and eventual v2 table/report carriers/limitation presentation. B's currently
   authorized standalone `validation/reporting/` work admits accepted v1 only. No requested
   change to B's current profile, production loaders, card attachment or eligibility.
4. Freeze reviewed implementation and dependencies on an unpublished integration revision.
   Use normal Git staging/commits; do not push a source-bound runtime revision to public main
   while its adopted support receipt is stale. Coordinate the complete human lifecycle below
   before integration. Keep proposal main green and usable throughout.

Concrete source-bound additions are every `.py` listed above under src/contract, including
new contract generator/hash helpers; prospective CLI/table or B provenance/report/CI-script
changes would also need prior ownership coordination and currentness review. The current
`scripts/u2_inputs.py::support_files()` recursively includes all Python in `src/rkuarch`,
`contract/uarch_contract`, and `scripts`, plus its explicit retained inputs/lock/provenance.
Adding a file changes inventory even if all old files are untouched. New engine schema JSON
needs freshness checks in addition to this inventory; no support-file exclusions are proposed.
These review files are outside that enumerator, so this proposal needs no oracle refresh.

**Required human sequence (not executed/authorized by this document):**

1. Coordinator/human freezes one exact reviewed implementation commit, pristine upstream
   `1e5706e0ebfcc67c1a7333079a35b75f693e9963`, lock/environment, PARAMS/precision matrix,
   sidecars, retained attribution and complete support inventory. B owns existing freeze
   tooling under scripts; never reuse an old input manifest for changed source. Record exact
   frozen input-manifest digest. Preserve U2 input coverage and its nominal references.
2. Human uses U0002's guarded vendor generation with that frozen input directory and external
   pristine upstream/oracle environment; agents do not set the human flag or run generation.
   Existing command shape is `python -B -m scripts.vendor_rk --sha <pin> --rk <pristine-checkout>
   --inputs <frozen-inputs> --input-manifest-sha256 <reviewed-digest> --output-root <fresh-candidate>`.
   Human repeats identically in a separate process for determinism. Drift requires a newly
   frozen candidate, never overwriting a receipt to make it appear current.
3. Validate candidate with strict `python -B -m scripts.vendor_rk --check --output-root
   <candidate>` and `check_support=True`, schema freshness, contract coverage and nominal
   compatibility. No `--historical` substitution. Inspect complete old/new artifact diffs,
   support inventory, manifest, input attribution, query IDs, counts/durations/nulls/refusals
   and additions/deletions. Do not populate old missing RoPE channels or change old rows to
   claim full decoder coverage. Explain any unexpectedly changed nominal values before adoption.
4. Javid explicitly approves the exact complete candidate and performs human-owned adoption/
   protected commits, recording old/new manifests, reason, frozen revision, approval and final
   publication commit. Retain historical artifacts through published Git commits, not copied
   checkpoint trees. Neither schema approval nor U0022 acceptance substitutes for adoption.
5. On the resulting exact integrated tree, run current ruff, both mypy commands, lint-imports,
   both schema families, strict vendor/contract checks, new focused rotary/replay and legacy
   public table/report tests, then one full suite. Any support-code edit after freeze requires
   a new human cycle. Only this green integrated revision may be pushed normally to main.
   CI remains read-only. Nightly/runner prerequisites remain independently pending with Reza.

## 6. Current explanatory prose, review decisions and effort

[coverage-prose.patch](coverage-prose.patch) proposes exact additive clarification in
`docs/how-it-works.md`, `docs/u2-workflow.md`, `src/rkuarch/workload/README.md`, and
`docs/reviews/U3-G2-physical-expectations.md`. It contains U0022's exact limitation and
preserves every historical number/payload. The workflow's named-model example needs this
scope clarification especially; the G2 matrix expectation specification is not proof of full
vector/byte coverage. No old U0003/U0019 ADR, U2 assumption, capture, reference or result is
rewritten. Future B report presentation must show the limitation for old model version 1,
without manufacturing a new historic omission field or a zero RoPE reference channel.

Coordinator/Javid review requested on this **schema and integration proposal only**:

1. Exact additive root shapes, inline coefficient closure, semantic joins and separate schema
   directories in §§1–2; protected installation remains a human action after review.
2. Explicit version dispatch with untouched legacy core, proposed v2 execution-closure identity
   rule, and v2 capture stopping before unapproved table/report attachment (§3).
3. A/B ownership, tests-first order, exact prose patch and unpublished freeze/adoption staging
   (§§4–6). B reconciles future interfaces through the coordinator, not by changing its v1 task.

No decision here reopens U0022 counts/precision/positions/rank. Tool selection/scouting,
instrumentation, fallback, U0005's proposed **200-second synthetic one-layer** limit and G2
verdict remain pending; there is no full-8B/24-hour table claim. Runner registration/manual
nightly is pending with Reza; no host waiver or allocation is granted.

Planning estimate after authorization: A 40–64 engineering hours (tests 12–18, new admission/
producer/engine/dispatch 20–32, legacy/integrated checks 8–14); B/coordinator interface
reconciliation 4–8 hours, excluding future production report integration. Human schema review/
installation 3–6 hours and U0002 freeze/generate/diff/adopt 4–8 active hours are separate;
independent review 4–8 active hours is also separate and has not happened. Human/reviewer
calendar waits and Reza runner/manual-nightly wait are unbounded, not implementation hours.
No simulator effort or full v2 product/report work is hidden in these estimates.

Checks performed for this proposal: prototype positives/refusals/schema rendering; ruff;
both current CI mypy invocations (production/contract targets, not static typing of the dynamic
documentation prototype); lint-imports; strict read-only vendor check; 70 tests across prompt
sync, third-party policy and existing U2 schema freshness; and `git apply --check --unidiff-zero` for the inert
prose patch (zero context avoids whitespace-only patch lines; base revision is recorded above).
No full suite or analytic execution was run: no runtime code changed. No candidate,
image, coefficient-generation tool, oracle generation/adoption or nightly was run. These author
checks are not independent review or evidence that future runtime tests pass.

Handoff: this directory is the exact proposed boundary. Publication commit/check receipts are
reported in the lane response (a commit cannot embed its own ID). Next dependency is coordinator
review of this concrete schema/prose/lifecycle diff, then the human protected-schema decision.
Stop before implementation.
