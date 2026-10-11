# U0022 — Explicit rotary position work, with immutable U2 history

**Status: ACCEPTED by Javid (@jjaffari), 2026-10-11**, acting human decision-maker
for both lanes, under `U3-RoPE-and-verification-v1`. U0022 is reserved for this decision.
Acceptance does not mean implementation or publication is complete. The human-owned
ADR commit precedes the separately reviewed schema and implementation changes.

Accepted text source: `docs/reviews/U3-RoPE-semantics-proposal.md` at
`7d15c5aa73504c38eac3b3dc162d2885cc1f33dc`, between its ADR markers.
See [acceptance and authorization scope](../reviews/U3-RoPE-and-verification-v1/README.md).

### Context

U2 `physical-resolved` model version `1` / `resolved-ops/1` does not model RoPE vector
work or coefficient traffic. Its preparation vocabulary has no corresponding node.
The accepted RMS, softmax, activation and residual formulas do not include it.
The [source trace](../reviews/U3-RoPE-semantics-proposal.md#evidence-trace-no-existing-rope-allowance-found)
records the evidence. Historical inputs/results and U0003/U0019 remain intact.

### Decision: narrowly version the modeled work

Adopt the following semantic profile `rope-precomputed/1`, extending the
existing prepared OpSpec graph family, not introducing another workload IR or an ONNX
frontend. It covers precomputed coefficients, both Q and newly produced K, balanced TP,
and the existing uniform-length decode/prefill scope. It is an abstract analytic work
convention, not a numerical simulator, measured vector throughput or physical instruction
count. It does not establish any candidate's feasibility.

1. Use new request `contract="uarch-contract/0.3"`, prepared `format="uarch-prepared/2"`,
   analytic `mapping_policy="analytic-ops@2"`, `accounting="resolved-ops/2"`, engine
   `version="resolved-ops/2"` and `physical-resolved` model `version="2"`. Retain
   `preparation_policy="balanced-tp/1"`, `mapping_scope="analytic_ops"`, and existing
   fidelity/rank rules. A corresponding `uarch-engine/2` carries the new point type;
   it is an analytic version change for this semantic addition, not a generic fork interface.
   V1 request/prepared/job validators must reject new fields/operators/versions, not
   reinterpret them. New roots coexist with the existing roots; no default upgrade.
2. Require `position_encoding` in the new intent: `kind="rope-precomputed/1"`,
   `rotary_dim=R`, `pairing="adjacent"|"split_halves"`, `coefficients_hash`,
   `position_policy="zero-origin-contiguous/1"`, `cache_key_state="rotated-before-store"`,
   and `numeric_policy="fp32-separate-round-rne/1"`. No model-name, theta-base, scaling,
   precision or pairing defaults. For this first new profile, missing/none/other
   positional methods are refused; old non-RoPE inputs stay in their old version.
3. The authenticated closure supplies one `RotaryCoefficients` value with
   `format="uarch-rotary-coefficients/1"`, its content `coefficients_hash`,
   `position_count`, `rotary_dim`, `dtype="fp32"`, `cos_bits`, `sin_bits`, and a
   `producer` using the existing name/version/implementation-hash carrier. Each array
   is exactly `[position_count,R/2]`, row p meaning absolute position p. Each scalar
   is exactly eight lowercase hexadecimal digits encoding IEEE binary32, independent
   of host endianness; NaN/Infinity encodings are refused. Hash canonical content using
   existing hashing rules, excluding only its own hash. Missing/tampered closure fails.
   Arrays define the supplied transformation; producer identity is provenance, not proof
   that they match a named model. These values are workload inputs, not an oracle.
4. Imported coefficient bytes are authoritative. No engine or replay loader generates
   sin/cos, substitutes a library's defaults, or infers a table from a model name. A
   future convenience producer may supply a reviewed table, but cannot claim Llama 3.1
   scaling or any named-model equivalence without source evidence and matching inputs.
   Generating coefficients on the simulated device is outside this profile and refused.
   Host-side creation/loading of the precomputed table is outside device timing; its
   counted device reads are not omitted. Known full coefficient storage is
   `8*position_count*(R/2)` bytes, shared across Q/K/layers, with no parameters added.
5. Add `rotary_embedding` to the **v2** OpSpec variant. Every decoder group has exactly
   two instances, `rope_q` and `rope_k`; never in head/tail. Each has dimensions
   `B,H,S,D,R,P`, with `P=R/2`, even `2<=R<=D`, and no reduction axes. Operands are
   read `X[B,H,S,D]`, read `Cos[B,S,P]`, read `Sin[B,S,P]`, write `Y[B,H,S,D]`.
   All are contiguous, `fusion="none"`, `kv_access=null`, `weight_copies=1`,
   `work_repeat=1`. X/Y use the declared activation format; Cos/Sin are FP32.
   The coefficient operands denote row gathers from the authenticated table, not a
   separately generated/materialized intermediate whose writes can be hidden.
6. Each v2 PreparedOp has a `rotary` binding. For rotary nodes it records `target="q"|"k"`, `coefficients_hash`,
   `pairing`, `numeric_policy`, `position_ids[B,S]`, and
   `input_op_id` naming the same-group Q or K projection. This binding is null for
   other op kinds. R agrees with the intent/table and each group's corresponding node.
   IDs, positions and all bindings participate in point/bundle/job identities and metric
   contributors. `PreparedGraphV2.kv_key_encoding` repeats the intent
   `position_encoding` object exactly; disagreement is refused. This states the required
   incoming cache representation, not evidence about unseen cache values. A future adapter
   cannot label delegation as preserved rotary semantics.

### Position, graph and rank rules

For decode, let C be the valid attended context per sequence, **including this iteration's
append**, and S=1. `position_ids[b]=[C-1]`; the incoming cache contains positions
0 through C−2 with K already rotated using this same table/profile. For prefill of
length S, `position_ids[b]=[0,1,...,S-1]` and there is no prior cache in this profile.
Every required row must exist in the table. Position arrays are captured explicitly and
validated, not silently rebuilt on replay. They are command metadata in this profile,
not a device position-ID tensor with hidden reads/writes. Cold/steady still describe the existing
microarchitectural state semantics; cold does not erase the declared decode context.
Offsets, sliding windows, packed/ragged sequences and changed tables for existing cache
keys are refused by this bounded profile. It declares the input cache's rotary state;
count-only execution does not authenticate unseen tensor values.

Required dependency/operand correspondence is
`q_projection → rope_q → attention Q`,
`k_projection → rope_k → kv_write K → attention K`, and
`v_projection → kv_write V → attention V`. V is not rotated. For unfused attention,
QK consumes rotated Q/K and AV consumes unchanged V through the existing explicit
intermediates. Preserve the existing KV-read policy, append count and page capacity;
no rotating all C cached keys on every decode and no second append. No page-rounded
RoPE tokens: it touches only this iteration's B×S new tokens. The two rotary nodes
are separate from QK-softmax-AV fusion; no implicit projection/rotation fusion or SRAM
retention is authorized. Shape-compatible edges are insufficient: validators require
these named producers/dependencies and the same table/profile for Q, K and cache state.

Use resolved rank-local Hq for Q and Hkv for K. GQA rotates each local KV head once,
not once per query head. Replicated KV heads on different ranks execute their respective
local rotation; never divide these counts by tp again. Preserve replication metadata
(global heads, physical local heads, replicas) on rope_k. Group.repeat applies once,
including each decoder layer; no expert multiplier applies to attention/RoPE. Partial
rotation changes only the first R coordinates per head. All D input/output coordinates
are transferred; tail copying incurs no arithmetic count. The initial profile admits no
additional rotary head/token/head-dimension padding beyond the resolved balanced shapes;
unsupported imported padding is refused, not truncated. Existing FFN/vocabulary padding
continues unchanged. Unequal embedding hit counts do not eliminate RoPE on any rank.

### Scalar semantics, precision and traffic

For each pair (a,b) and supplied coefficients (c,s), define
`a_out=a*c-b*s`, `b_out=a*s+b*c`. Adjacent pairs use `(2j,2j+1)`; split-halves pairs use
`(j,j+R/2)` within the first R coordinates. This rotation is based on
[RoFormer §3.2 and §3.4.2](https://arxiv.org/html/2104.09864v5#S3), which applies rotary
position transformations to queries and keys. The following accounting and supported
precision choices are this ADR's proposal, not claims from that paper.

X/Y and KV storage must share one format in {FP32, BF16, FP16} in this first profile;
refuse mixed activation/KV formats, FP8, quantized/block formats and unsupported hardware
format/rate combinations. This keeps a KV-format conversion outside RoPE from silently
becoming free. Promoting BF16/FP16 input scalars to FP32 is exact; rotation's four
multiplies and two add/subtract operations per pair round separately in FP32,
round-to-nearest ties-to-even, with no contracted FMA. Round the rotated result back
to X/Y dtype with that same rounding rule; copy the unrotated tail unchanged. Coefficients
are already FP32. No transcendental, table-generation, index-address arithmetic or
implicit scale computation is included in these six rotation operations.

Define M=B*S and E=M*H*R rotated scalars per node. Proposed abstract counts:

- `matrix_ops=0`; rotation arithmetic = `3E` (four multiplies plus two add/subtracts
  per pair). No separate negation operation is added to a subtraction.
- Conversions = `2E` for BF16/FP16, zero for FP32; `vector_ops=3E+conversions`.
  Counting each scalar conversion as one abstract vector op is a **new explicit
  assumption**, not a claim of one instruction/cycle. Use algorithm identity
  `rope-3e-plus-explicit-casts/1`; old unrelated conversion limitations remain.
  Position zero or identity coefficients still incur the declared work: no assumed
  constant folding. Future executed work, eliminated work and issued padding must
  be distinguished, never manufactured from this formula.
- With X/Y width w bytes, reads are `w*M*H*D + 4*M*R`; writes are `w*M*H*D`.
  Each Cos/Sin selected row is charged once per token per node, broadcast over H.
  Repeated positions across sequences still incur each declared operand access.
  Q and K each pay their coefficient reads, and each decoder repeat pays again.
  No cross-node/layer cache benefit is assumed; no repeated coefficient reads per
  head are invented. Physical bus transactions can differ from these payload counts.
- Multiply these values by group.repeat exactly once. Across Q/K per layer the
  added reads are `w*M*(Hq+Hkv)*D + 8*M*R`, writes `w*M*(Hq+Hkv)*D`, and vectors
  `(3+cast_factor)*M*(Hq+Hkv)*R`, with cast_factor 0 or 2.

Projection output writes and downstream attention/KV input reads remain counted as
before; the rotary reads/writes above are additional intermediate accesses. This is
U2's explicit per-op DRAM convention extended to named rotary operands, not an assertion
about a fused kernel. Keep aggregate/per-op roofline arithmetic and matrix/vector
serialization unchanged. Supply new assumption identity with the RoPE/count/traffic
policy and precision limitations; no error band, accuracy badge or measured throughput
follows. Coefficient capacity is a known input allocation, not complete activation peak
residency; total peak remains unknown under the existing limitation.

### Independent literal examples (proposed tests, not runtime evidence)

For one rank, one layer, Hq=2, Hkv=1, D=4:

| Case | M | R | Format | Q vectors | K vectors | Added reads | Added writes |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| Decode, C=17, positions=[16] | 1 | 4 | BF16 | 40 | 20 | 56 bytes | 24 bytes |
| Same, FP32 | 1 | 4 | FP32 | 24 | 12 | 80 bytes | 48 bytes |
| Same, partial rotation | 1 | 2 | BF16 | 20 | 10 | 40 bytes | 24 bytes |
| Prefill B=2,S=3, positions=[0,1,2] per sequence | 6 | 4 | BF16 | 240 | 120 | 336 bytes | 144 bytes |

All matrix deltas are zero. For the first row, Q reads 16+16=32 bytes and writes 16;
K reads 8+16=24 and writes 8. Rotation is 36 arithmetic ops plus 24 scalar conversions.
Two decoder repeats give 120 vector ops, 112 read bytes, 48 write bytes; head/tail do
not repeat these. With a 16-token KV page, C=17 uses two allocated pages, but RoPE
still processes one new token. C=33 changes position/table coverage and KV traffic,
not this RoPE count. At global Hq=4,Hkv=1,tp=2, each rank has the first row's local
heads; both execute K's 20 vector ops. Halving that local K count is a replication bug.

A pair-value discriminator uses X=[1,2,3,4], Cos=[0,1], Sin=[1,0], FP32:
adjacent yields [-2,1,3,4]; split-halves yields [-3,2,1,4]. Both cost 12 arithmetic
ops for one head, independent of coefficient values. R=2, Cos=[0], Sin=[1] rotates
only the first pair and leaves [3,4] unchanged, costing 6 ops. These are synthetic
coefficients for exact arithmetic tests, not a named model's coefficient source.
FP16 has the same count/byte examples as BF16; numerical rounding need not match.

### Migration, limitations and tests before runtime changes

Publish this exact limitation without modifying historical payloads:

> U2 physical-resolved/1 accounts for its captured operator graph. It excludes RoPE
> rotation/conversion work and coefficient traffic; its vector/byte counts and timing
> are not complete RoPE-equipped decoder work. This does not change historical numbers,
> nominal compatibility outcomes, parameter counts or the matrix-count convention.

Apply this clarification to current explanatory docs and future report presentation
only after acceptance and ownership coordination. Do not edit the accepted U0003
package, U0019, historical U2 payload/assumption bytes, frozen results or adopted
oracle rows to append a new omission. Historical missing reference channels remain
absent/unknown, never a RoPE zero or fresh `modelled_absence` proof. Old independent
correctness claims cover the modeled graph; they do not certify complete decoder
coverage. The existing STUB/unknown-error/unverified-energy rules remain.

Before any implementation:

1. Human accepts exact semantics, reserves the number and commits the ADR; review the
   additive contract/schema diff separately. New version roots must not widen v1
   validators or silently convert imported v1 graphs. No automatic migration: users
   supply explicit coefficients/profile, then new preparation produces new identities.
2. Write discriminating tests with literal expectations above, no production count
   imports for expected values: omitted/doubled Q or K; rotate V; rotate C cached tokens;
   Hkv→Hq substitution; extra tp division; repeated head/tail; omitted conversions;
   per-head coefficient rereads; page-rounded RoPE; dropped tail transfers; adjacent/
   split-halves confusion; causal versus full-square prefill must leave RoPE counts
   unchanged. Exact dependency/cache-state/table-version refusals must bite.
3. Add paired version tests: legacy bytes retain the same interpretation and old
   authenticated result identity; v1 rejects rotary additions; v2 refuses missing Q/K,
   odd/out-of-range R, mismatched positions/pairing/table hashes, short/nonfinite table,
   unsupported dtype/mixed KV format, padding, stale assumptions or cross-version jobs.
   Add input-hash tamper and coefficient-closure tests. Replay with the preparation
   producer disabled must preserve all rotary content. Do not synthesize old identities
   with a changed engine implementation hash.
4. Preserve legacy execution in its supported historical version rather than changing
   `core.py` and relabeling its changed hash as the old engine. Decide the concrete
   additive dispatch/legacy compatibility implementation in the later code review;
   retain byte-for-byte old capture/table/report replay as acceptance tests. New captures
   must carry new model/assumption/request/point/job/result identities and cannot reuse
   old comparison evidence as exact same-work evidence. Historical-version replay does
   not make a stale support receipt current: refuse it in current acceptance checks,
   and retain the original pinned Git version for historical reproduction when needed.
5. Even additive modules affect `scripts/u2_inputs.py::support_files()`, which enumerates
   Python under src/contract/scripts. Bound-source changes require U0002 human generation/
   adoption with current support identity before the integrated acceptance checkpoint.
   Never exclude new files, disable `check_support`, regenerate actual oracle artifacts
   as an agent, relax currentness or rewrite U2 history. Coordinate this lifecycle before
   merging implementation; a temporarily failing strict check is not permission to ship.
6. After the human lifecycle, run both current mypy commands, ruff, import contracts,
   schema freshness, strict vendor/contract checks, focused rotary/replay/report tests,
   then one full integrated suite. B's standalone analytic source-report work remains
   independently scoped; update B's future relation corpus/model bindings when v2 is
   actually admitted, not by attaching pending evidence now. No extra full suite for prose.

### Consequences and exclusions

Vector counts and traffic increase for new inputs; matrix and model-parameter counts do
not. Rotation has no learned parameters. Historical numeric results remain reproducible
under their recorded identities with an explicit scope limitation. Precomputed-table
provenance is required, so the accepted U2 model-shape fixtures alone cannot construct
a named-model RoPE run. This is intentional refusal, not permission to guess coefficients.
The table's value correctness and real hardware throughput remain unvalidated.

This decision does not select or repair a fork, implement an adapter/engine, assert a
G2 verdict, approve 200 seconds, alter G2 coverage, authorize device coefficient
generation, create a general mapping interface, grant licences/resources, enable a
runner, perform independent review, close U3 or modify any adopted artifact. Reported
Podman availability does not cure source semantics; runner/manual-nightly prerequisites
remain separate. Any subsequent viable route or amended fallback is Javid's decision.

### Addendum — accepted additive schema design

Javid accepted the exact four-file design/prose proposal at
`e622673577017a50f3e436205809f76fdf7ffae7`, recorded in
[U3-RoPE-schema-v1 acceptance](../reviews/U3-RoPE-schema-v1-acceptance.md) at
`531d9c923c30dd465cf56c8a5865cd9ce62cdd84`. The [protected schema review patch](../reviews/U3-RoPE-protected-patch-v1/README.md)
specifies the installable carrier/generator/mirror/test delta; its reviewed author revision
and the human installation commit are recorded by the coordinator at installation.

Use eleven additive contract roots in `rotary_v2.py`, with their dedicated generator and
`contract/schema/rotary-v2/` mirrors. Inline the authenticated RotaryCoefficients object in
each new bundle and, when implemented, each new engine job. Preserve the accepted version
routing and refuse cross-version reinterpretation; do not widen v1 roots, generated schemas,
artifact dispatch or acceptance. Carrier parsing alone is not execution admission: full graph,
closure, rank/hardware, assumptions, job/result and replay validators remain separately required.

Keep legacy analytic core/entry-point/protocol and the v1 public path bytes unchanged.
The future v2 implementation identity binds its reviewed local execution dependency closure;
its exact set awaits implementation. New capture stops before unapproved table/report
integration. No changed implementation may reuse an old identity or evidence. Historical
Git reproduction does not make stale support current. Even these additive Python modules
require the U0002 human freeze/generation/adoption lifecycle before public source-bound
integration; schema installation is no waiver. This addendum changes none of U0022's
counting, precision, position, coefficient, cache, rank or historical-separation semantics.
