# Proposed exact interfaces and semantic rules

Status: PROPOSED. Normative structural types are in `proposed.schema.json` under `$defs`.
All objects forbid unknown fields, all required nullable fields serialize explicitly as null,
all floats are finite, bool/string values are refused for numeric fields, and all identities
use `sha256:<64 lowercase hex>` unless a legacy carrier explicitly uses raw 64-hex.
I means positive JSON integer; Z nonnegative integer; N nonnegative finite number; P positive
finite number; S nonblank string. Lists retain order. No path is identity.

## Hardware, derivation and export

HardwareSpec and SourcedValue retain their accepted U1 vocabulary and unit/path rules.
No spec field is added. B authors npu-l4, npu-m256, tpu-v5e and blackhole-p100a and all source,
stub and stipulation inventory. Unknown reference values remain stub claims with null sources;
reference stipulations fail. Direct/preset DRAM timing remains explicit, pinned, no fallback.
A timing origin does not imply U-C0 models timings. SRAM size/coefficient consistency remains
mandatory for variants even while analytic energy is unmodelled.

Let C=grid.rows×grid.cols and F=round(core.freq_hz) at base ratio 1. Resolve each domain once
using accepted round-to-integer-Hz semantics (ties-to-even); refuse a result below 1 Hz.
Do not store rounded periods, multiply bandwidth by channels again, or apply refresh derating.
The DRAM bw leaf is total chip bandwidth, not per-channel bandwidth.

| Derived parameter | Formula | Export unit / supported names |
| --- | --- | --- |
| per-format compute peak | 2×C×macs_per_cycle[format]×F / 10^12 | fp32_tflops, tf32_tflops, bf16_tflops, fp16_tflops, fp8_tflops, fp4_tflops: TFLOPS; int8_tops, int4_tops: TOPS |
| hbm_bw | memory.dram.bw_bytes_per_s / 10^12 | TB/s, decimal |
| hbm_capacity | memory.dram.capacity_bytes / 10^9 | GB, decimal |
| tdp | tdp_w | W |

Emit only declared compute formats that also exist in spec.formats; mismatched map entries
fail consumption, never manufacture a substitute. Format widths must equal fp32/tf32=4,
fp16/bf16=2, fp8/int8=1, fp4/int4=0.5 byte. For nonzero block_scale_bytes U2 lacks block
geometry: refuse that format before execution, retain its contract representation for later
support. Packed half-byte operand transfers round each operand byte extent up to whole bytes.
KV dtype needs a declared storage format, not its own compute peak. Matrix compute does.

`Derivation` carries format, hardware_spec_hash, parameters and derivation_hash. Each
DerivedParameter has name, full SourcedValue value, formula_id, contributor_paths,
claim_badge and conditional_paths. Paths are sorted unique accepted HardwareSpec paths;
formula IDs are `matrix-peak/1`, `decimal-bandwidth/1`, `decimal-capacity/1`, `identity/1`.
Matrix inputs are rows, cols, the specific format's MAC rate and core frequency only.
Never taint a peak with unrelated TDP, nor drop a contributing stub frequency.

All claims: value.kind=claim; provenance=worst claim contributor, source is
`uarch-derive:<spec_hash>:<formula_id>` unless worst is stub, then source=null; date=null.
Any stipulation: value.kind=stipulation, provenance/source/date=null, rationale is the stable
formula ID plus sorted conditional paths. claim_badge still retains the worst contributing
claims (empty set=null; no claim contributor), preventing a mixed result from concealing stub evidence. Conditions
are exact original leaves, not invented citations. B badges metrics using those contributors
plus model evidence, excludes stipulations from worst-of claims and applies proposed ceiling.

Example: 2×2 cores, 128 MAC/cycle, 1 GHz gives 1.024 TFLOPS; 10^12 byte/s gives 1 TB/s;
32×10^9 bytes gives 32 GB. If clock is stipulated and MAC rate a stub claim, derived peak is
stipulated AND claim_badge=stub. If all inputs are claims at measured/spec_derived, the worst
is spec_derived. Reference output remains claim. Hardware payload values are never tuned.

The authoritative ComponentExport and separately bound test projection are fully specified in
[comparison-evidence-export.md](comparison-evidence-export.md), including required metadata,
explicit execution-model input, loss records, retained upstream-only bindings and actual
loader/error boundaries. Primary extended truth is not loader-compatible library YAML.

## Request, prepared envelope and coverage

RequestIntent has all existing request fields, contract=0.2, plus assumptions_hash and analytic_mode
(aggregate|per_op), accounting=`resolved-ops/1`, preparation_policy=`balanced-tp/1`.
CharacterizationRequest adds required prepared_input_hash. The high-level CLI first builds
an Intent, then resolves/prepares and forms the bound request. Neither a path nor local/import
entry route is serialized. The bundle stores the Intent, avoiding a circular request hash.
High-level model/shape checks remain; their nominal params are identity checks, never a
replacement for execution dimensions. Supported imports need not equal the local producer's
preferred graph. Validate physical dimensions and invariants, not a regenerated graph.

PreparedBundle fields: format=`uarch-prepared/1`, bundle_hash, intent_hash, intent,
hardware_spec, producer {name,version,implementation_hash}, rank, mapping_scope=`analytic_ops`,
points. Rank fields: kind=balanced_tp_representative|balanced_tp_selected_rank, tp,
rank_index, equivalent_ranks, collectives=excluded. Proposed selected-rank support is an
explicit U0019 amendment, not currently accepted scope. Each point's embedding_hits has tp
integers summing to M, and hit_source identifies supplied counts, tp1 trivial, or explicitly
requested synthetic balanced assignment. embedding_local_tokens equals selected rank's hit
count. Representative mode requires equal hits/extents; equivalent_ranks is exactly the ranks
with equal physical work across every point. No all-token-per-rank inference. PP/EP/CP,
heterogeneous non-embedding splits and detailed mappings fail. Imports are never re-sharded.
Hardware binding equals Intent.hardware_spec_hash and table binding. See two-track-amendment.md
for conservation examples and the precise scope decision.

A point has query, initial_state, frequency_ratio, graph, embedding_hits, hit_source and payload_hash. Decode query is
phase, batch, total_context_tokens with T%B=0. Prefill query is phase, n_prompts,
prompt_tokens; derive total=n×L and Q=n×L² for the test adapter only. Query/state/frequency
keys must exactly equal the Cartesian product of the Intent grids for its state: no gaps,
duplicates or extra cases. Input grid list order remains identity-significant as accepted in
U1. Output points use declared decode axes in nested B,context,frequency order, then prefill
n,L,frequency order. No interpolation; exact lookup only, interpolation declarations are
`none`, outside_grid=`refuse`. Error experiment points require a later explicit extension.
`--prepared-input` cannot be mixed with model/spec/tp/precision/policy/grid/state overrides.
Engine selection must agree with analytic scope; output destination is operational only.

## Resolved operator graph

Graph fields: groups, omissions, attention_mask (full_square|causal), lm_head_tokens.
Each group: id, kind (head|decoder|tail), repeat, depends_on, ops. Group dependencies form
a DAG. A group completes all repeats before its successors; repeats are sequential decoder
layers with distinct layer weights, not reuse of the same weight tensor. Head/tail repeat=1;
decoder repeats sum to model.n_layers. layer_reuse=true permits one decoder template with
repeat=n_layers; false requires n_layers explicit repeat=1 groups. No invented overlap.

Each op wraps unchanged OpSpec: id, depends_on (same-group op IDs), spec, fusion,
padding, replication, kv_access, work_repeat, weight_copies, operand_access and
embedding_local_tokens. IDs are unique within a group; the public resolved identifier is
`group_id/op_id`, with numeric repeat index only when expanded for tests. IDs and array order
are content, never local paths. No dangling/self/cyclic edge; dependencies must appear before
the op in the serialized order. Group completion dependencies cover cross-layer boundaries.
Each operand has an exact access mode read|write|read_write; keys equal OpSpec.operands.
All dimensions are resolved positive integer physical extents; reduction_axes are valid
names, unique. Required per-operator dimension and operand names are fixed below.

For projection/lm_head: M,K,N, operands X[M,K], W[K,N], Y[M,N], reduction K. Inputs X/W read,
Y write; MAC count 2MKN. q,k,v,out,ffn_up/gate/down use these same names. A transposed layout
is not guessed. For normalization: M,D, X/Y[M,D], W[D], reduction D, reads X/W and writes Y;
6MD vector ops (RMS multiply/reduce/scale convention, not transcendental latency).
Residual: M,D, X/R/Y[M,D], reads X/R and writes Y, MD vector ops. Gated activation:
M,D, X/G/Y[M,D], 6MD vector ops for SiLU(gate)×up. Ungated activation uses X/Y and 5MD.
These explicit scalar-operation conventions require D6 acceptance and stay versioned.

Embedding: M,V,D, W[V,D], Y[M,D], no reduction, matrix/vector ops=0; gather reads
embedding_local_tokens×D elements and writes M×D output (including masked zeros); the full
V×D weight allocation is residency, not per-iteration reads. embedding_local_tokens is
required integer in [0,M] only for embedding, otherwise null. Standalone D7 assumption is
explicit. lm_head M equals graph.lm_head_tokens (decode B; default prefill n×L). A declared
import selecting final token per sequence uses M=n and is not silently expanded. Shared tied
embedding/lm_head weights count once for residency, but their separate accesses still count.

Fused attention: B,Hq,Hkv,S,T,D; Q/O[B,Hq,S,D], K/V[B,Hkv,T,D], reduction T,D; Hq%Hkv=0.
Fusion=`qk_softmax_av`, operands exactly Q,K,V,O, no stored score operand. Reads Q/K/V and
writes O. Decode S=1, T=context per sequence (including this iteration's appended token).
Prefill S=T=L. Full-square score pairs=B×Hq×S×T; causal prefill pairs=B×Hq×L(L+1)/2.
Matrix work=4×pairs×D; vector work=5×pairs for softmax convention. This logical temporary
score domain is not an L×L DRAM tensor. Unfused qk_score/softmax/av_application remain legal
OpSpec vocabulary but U2 execution admits them only with explicit intermediate operands:
qk_score Q[B,Hq,S,D],K[B,Hkv,T,D],scores[B,Hq,S,T]; softmax scores/probs same shape;
av_application probs,V[B,Hkv,T,D],O[B,Hq,S,D]. The same pair counts apply; materialized
scores/probs are charged at operand dtype and cannot be re-fused. Dependencies must connect
the producer/consumer triplet. Their fusion is none, reduction D / T / T respectively.

kv_write: B,Hkv,S,D, K/V contiguous inputs and K_cache/V_cache paged outputs, each
[B,Hkv,S,D], zero matrix/vector ops, reads and writes both K/V valid appended data. It occurs
once per layer, before fused attention consuming the updated cache; the attention reads
include the appended token, so do not add a second append elsewhere.

KV layout: block_size_tokens must match Intent and every paged operand. kv_access on
attention fixes context_tokens, pages_per_sequence=ceil(T/block), last_page_valid_tokens=
1+(T-1)%block, read_policy=valid_tokens, write_policy=append_valid_tokens. Pages describe
logical page-granular reads, not fabricated DMA tasks. Full-page capacity is reserved, but
last-page unused tokens do not count as reads. New writes address only valid S tokens.
U2 makes no page-table, address-translation, refresh or detailed timing claim. Example T=17,
block=16 → two pages, last valid=1; paired bf16 K/V with Hkv=1,D=2 read 136 bytes/sequence.

Padding entries: dimension, logical, physical; require physical>=logical and physical equals
OpSpec dimension. No extra hidden padding. Replication entries: dimension, global_extent,
rank_extent, replicas; balanced validation relates rank extent×tp = global extent×replicas.
KV uses rank_extent=max(1,global_heads/tp); replicated case requires tp divisible by KV heads.
Vocabulary uses physical ceil(V/tp), masked slots described explicitly; query heads and FFN
must divide. Execute physical shapes as imported: no extra /tp anywhere in engine or table.
A-F12 oracle projection guard independently refuses replication/padding before adapter call;
legitimate runtime shapes remain supported. No component-aware projection is accepted here.

Expert multipliers: work_repeat=experts_per_token only on MoE FFN/activation terms, else 1;
weight_copies=n_experts only on expert projection weights, else 1. Op dimensions remain one
expert's width d_ff=expert_d_ff. Activity counts use work_repeat once, group repeat once.
Resident expert weight allocation uses weight_copies once, group repeat once, never both
multipliers. Shared projections/norms/head/tail do not get either expert multiplier. Router
parameters remain in global identity/residency, while routing operations/imbalance/all-to-all
are omitted and MOE_OMISSION must occur in graph and table. Mixed/MoE graphs need the same
checks on import; a missing warning is a refusal, not an opportunity to silently repair input.

Memory convention: each declared read/write operand crosses DRAM once per op invocation,
except embedding gather and fused internal scores as above. No hidden inter-op activation
retention. Thus intermediate activations legitimately differ from the frozen oracle, which
omits them. Weight reads use active work_repeat, not all stored experts. Counts are summed
in deterministic group/op order using math.fsum after exact integer arithmetic. Peak resident
HBM includes unique model weights (tie sharing), total experts/router and page-rounded KV;
activation peak residency is not claimed without lifetimes. Report peak_resident_bytes.hbm
and sram as null until a complete peak policy is approved/implemented; known weight/KV
capacity checks still refuse weight overflow and warn on KV overflow. Do not label a partial
weight sum as peak total residency.

## Protocol, timing and report fields

`EngineJob`/`EngineResult` have one authority: A's engines/protocol.py, exporting schemas into
engines/schema/ and referencing human-owned prepared/operator/count types. No duplicate
protocol models in contract/. Table/CLI invokes one JSON request per subprocess; stdout is
one canonical result plus LF, stderr contains diagnostics, nonzero exit is failure. Pure
core functions behind this transport support unit tests. Production engines never import
workload builder, mapping policies, vendor modules, scripts or rk.

Job fields are exact in schema: protocol/job_hash/request_hash/bundle_hash/point_hash,
producer/engine identities, ResolvedHardware, point, rank, precision, fidelity_detail, mode,
accounting, initial_state, state_model and seed. ResolvedHardware is the explicit U2 numeric
projection (three integer clocks, matrix/vector peaks, DRAM rate/capacity, array rows/cols,
spec hash), not a second hardware authoring surface. Reject any mismatch with supplied spec
before launching. Point covers frequency/state; job duplicates must equal them. Core peak
at point uses that point's resolved core Hz. DRAM peak stays its explicit spec rate in U2;
a scalable DRAM frequency with ratio !=1 is refused until a rate-vs-clock rule is approved.
NoC rate has no timing effect in stateless U-C0, and is listed unrepresented.

Compute time per op = matrix_ops/matrix_peak + vector_ops/vector_peak (serialized compute
work convention); memory time = (reads+writes)/DRAM peak. Multiply invocation counts once
before aggregate arithmetic. Aggregate=max(sum compute, sum memory); per_op=sum(max for
each op), hence per_op>=aggregate. No invented occupancy, busy time, NoC or barrier latency.
Compute wins exact ties. Attribution charges each chosen bound its entire roofline duration;
aggregate charges the winning aggregate bound. Other attribution keys are known excluded
contributions=0, not claims of measured zero stall. `busy_time_ps`, diagnostics, simulator
metrics and trace are null in analytic results; unrepresented lists unsupported hardware
paths in sorted order. Energy and all measured errors remain unmodelled/unknown.

Analytic ps are nonnegative binary64 including fractions. No ceil/floor to integral ps.
Compute via seconds then multiply by 10^12 inside engine; table's sole named conversion
`ps_to_seconds(x)=x/10^12` supplies Row fields. Do not round for display before hashing.
Use stable fsum; attribution conservation has the existing tolerance 1e-9 relative/1e-15 s.
Physical conversion regressions use independent hand algebra and fractional-ps cases.
Nominal candidate duration comparisons use each stored upstream expectation within ±0.1%
only if the two-track gate replacement is accepted. Physical workload duration is not claimed
to meet that nominal gate. Conversion error is never a count adjustment. The independent
48-op/52-byte case has exact 1ps = 10^-12s under its declared rates.

Each OpResult contains resolved ID/group, instances (group repeat×work_repeat), total Counts,
compute/memory/duration_ps (all represented instances), selected bound, operational intensity,
achieved ops/s, ridge ops/byte, matrix/vector peaks, DRAM peak and ReportScope. Roofline plot
uses matrix_ops/(read+write bytes), achieved matrix_ops/(per-op duration seconds), ridge=
matrix peak/DRAM peak; zero denominators produce null, not infinity. Vector-only points are
identified by op_class; zero matrix throughput is a modelled zero, not an unknown.
The display is an isolated per-op estimate even on aggregate rows: per-op durations must NOT
be summed to explain aggregate duration. Aggregate Row attribution uses aggregate result.

ReportScope fields: op_class (Operator spelling), precision_roles {compute, kv_cache,
operands: name->dtype}, intensity_regime, array_fill, noc_load_regime, dram_load_regime,
mapping_match. Unknowns are null. U1 intensity bins relative to ridge remain low<0.5,
middle 0.5–2 inclusive, high>2; fill compares GEMM M and N against actual rectangular array.
Non-GEMM fill is null without a physical projection. NoC/DRAM load and mapping remain unknown
without evidence. Family is resolved only through the hash-bound report-context registry,
never an engine field. Purpose/granularity/dimension matching and independent scope cases
are fully specified in comparison-evidence-export.md; no widening of U1 bins.

0.2 Table adds intent_hash, execution_hash, preparation Producer, ArtifactBindings,
report_context_version; rows add point_hash, result_hash, op_results, analytic_mode,
state_model. Existing null errors, Counts, conditional_on and badge carriers stay intact.
Counts include known vector and write values, even where oracle evidence is absent.
Every attempted comparison, including failure/unassessed/refusal, is bound through
ArtifactBindings and ReportContext/2. comparison_state is attempted, never erased as not_run.
0.2 Table removes flop_parity in favor of these complete artifacts. Legacy successful carrier
semantics remain operative until this explicit amendment is accepted. B receives full ModelCard companion and checks
H(card)==embedded.hash, embedded summary exact equality, model ID (engine/version/detail/
policy) against request/result, and evidence references/scope before badge application.

`uarch report TABLE [--artifact-dir DIR]` resolves only hash filenames `<hex>.json`, default
TABLE.parent/artifacts/, and never fetches URLs or invokes preparation/engines. It verifies
bundle, extracts spec, reconstructs request, verifies derivation and card, and cross-checks
all row point/result/job identities. A supplies a read-only `load_verified_report_inputs`
callable in table/artifacts.py for artifact/derivation/job checks; it never launches engines
or preparation. B consumes its verified context and does not duplicate hardware derivation
or roofline formulas. Generated tables place a captured bundle, full ModelCard, derivation, EngineJobs, EngineResults,
AssumptionSet, report context, comparison inventory/artifacts and the transitive evidence/
source/review/ordering/verification/registry/recipe closure in artifacts/. Result hashes are discovered from
rows; each result names its job_hash, selecting the job companion by hash.
Bindings' hardware hash selects the spec inside the bundle, not a second mutable copy.
The whole table digest and every nested hash must match. Missing/bad artifacts refuse before
rendering; an explicit legacy inspector may show unverified data but is not U-P4 report.
File relocation of TABLE plus artifacts, or --artifact-dir, never changes HTML/Markdown bytes.
No filenames, absolute paths or timestamp comments enter canonical output.

Every conditional_on path must resolve to an actual stipulated leaf in the bound proposed
spec, with equality of ALL SourcedValue fields (including rationale, unit, null metadata).
Every hardware stipulation used by a displayed metric is included; conservative union across
all spec stipulations is permitted only when labelled all-spec conditions. Recommended table
scope is all spec stipulations in sorted unique path order, so count/list cannot omit any.
Claims are not conditions. Use grammar of sourced_leaves, including numeric list indices;
reject missing/index-out-of-range/ambiguous paths. No eval or suffix-only matching.
Require table.hardware_spec_hash=request.hardware_spec_hash=spec_hash(spec), params exactly
match derivation, and hardware/detail agreement: present shared SRAM requires explicit
unrepresented in U2, absent hardware forbids a detail entry. Preserve the narrow cycle echo
only under conditional_on[].value. A serialized source spec belongs in bundle companion,
never in Row, request, params or report metrics.

## Canonical identities and refusal order

Reuse U1 canonical JSON: validate and serialize defaults, sorted object keys, UTF-8,
ensure_ascii=false, compact separators, repr-round-trip floats, -0.0→0.0, no NaN/Inf.
List order preserved. JSON duplicate object keys refuse before validation. JSON files use
canonical bytes plus exactly one LF for captured output, while hashes exclude that LF.
The review fixtures may be pretty-printed: identity is validated canonical content.

* intent_hash = H(RequestIntent), preserving versioned preparation choices.
* point payload_hash = H(point minus its own payload_hash), including exact graph/state/f.
* bundle_hash = H(bundle minus its own bundle_hash), including producer and all nested hashes.
* request_hash = H(Intent plus prepared_input_hash=bundle_hash).
* derivation_hash/result_hash/job_hash = H(the object minus only its own hash).
* execution_hash = H({request_hash, ordered job_hashes, engine identity, uarch_version}).
* card_hash = H(full ModelCard); table_hash excludes only its own top-level table_hash.

Import recomputes from inside out, never trusts syntax as authentication. A changed producer
version changes bundle/request/execution/table, even for identical numeric graphs; changed
engine version changes job/execution/result/table. A graph changes point and all ancestors.
Moving bytes changes none. Captured local producer identity survives replay verbatim; do not
replace it with a label 'imported'. Local generation and captured replay must use identical
run/card/derivation/version inputs for byte equality. Render version belongs to report
identity/output; it does not alter engine physics. Cache key is execution_hash, additionally
binding card/derivation/table serializer version for cached table/report outputs. Cache hit
still checks requested artifact hashes. No path/mtime-based validity.

Pre-execution validation order: parse/duplicate keys/version → structural/numeric types →
inner/outer hashes → hardware/intent/request equality → precision/format support → rank/
physical shape/padding/replication → fusion/dependencies/multiplicity/omissions → exact
coverage/state/frequency → fidelity/shared SRAM → derivation/model-card/conditions → resolved
job consistency. At any failure, zero engine calls and zero producer calls on import. The
parity adapter additionally runs A-F12 before candidate execution. Exact error codes appear
in negative fixtures; each refusal includes offending path and requested/supported scope.

## D6 subchoices to approve explicitly

These are new analytic conventions, not changes to accepted fusion/MAC/TP ownership.
Each requires Javid's decision with the rest of D6:

| Subchoice and background | Alternatives / tradeoff | Recommendation |
| --- | --- | --- |
| D6a scalar counts: OpSpec has no scalar algorithm field | Count only matrix ops and mark vector unknown; or define reproducible norm/softmax/activation scalar work. Unknown avoids an arbitrary scalar convention but prevents complete workload accounting. | Use the explicitly versioned 6MD RMS, 5×pairs softmax, 5MD ungated / 6MD gated activation formulas; these are abstract ops, not measured transcendental throughput. |
| D6b memory between ops: analytic scope has no placement/lifetime graph | Assume every operand crosses DRAM, or retain intermediate activations implicitly. Retention can reduce traffic but claims a mapping absent from the inputs. | Charge explicit accesses per op, with only declared fused internals exempt. This is a conservative analytic traffic convention and exposes the oracle's activation omission. |
| D6c matrix and vector time: hardware has two peak rates, but no schedule | Sum the two times or assume perfect overlap and take max. Perfect overlap lowers the bound while making an extra execution assumption. | Serialize the two in compute time for resolved-ops/1; record this scope. Neither choice permits adjusting the hardware peaks or pretending the oracle contains vector timing. |
| D6d peak residency: weight/KV sizes are known, activation lifetimes are not | Label partial storage as peak, invent a lifetime model, or return null for total peak while performing known capacity checks. | Return null for peak_resident_bytes in U2, retain known weight/KV checks and warn that total activation peak is unmodelled. Add a future versioned peak policy if needed. |

The graph's padding metadata does not mean an engine is allowed to change its shapes.
Mixed storage/compute precision uses each operand's declared dtype for traffic. Precision
conversion is unmodelled in this version and must be disclosed in unrepresented/warnings
when K/V compute outputs are stored in another dtype; no zero-cost accuracy claim follows.
A later explicit conversion operator would require a vocabulary decision, not hidden work.

## Additional review-only companion roots

Comparison/evidence/export/model-assumption/precision/render roots and their exact semantic
hash rules are defined in comparison-evidence-export.md and proposed.schema.json. ModelIdentity
is separate from EngineIdentity; nominal model has no production engine. AssumptionSet binds
request/job/model conventions. Registry/evidence/recipes bind report context and table, not
engine execution. RenderSpec changes report bytes/hash without changing table/job/result.
Review hashes bind subject bodies excluding self/review fields, not unverified labels.
The old FlopParity definitions are retained solely for historical inspection, not Table 0.2.
