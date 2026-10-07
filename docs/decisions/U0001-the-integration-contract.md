# U0001 — The integration contract

**Status: ACCEPTED by Javid (@jjaffari), 2026-10-06 (America/Los_Angeles).**
Javid accepted the complete reviewed proposal, including its defaults, concrete schema
choices and the narrow stub-source exception, while acting as human owner/approver for
both U1 lanes. No Reza approval is claimed. See the
[acceptance and adoption record](../reviews/U1-acceptance-and-adoption.md) for the exact
approved proposal hash and session authorization. Commit, push, hosted CI, Linux-box
cold-clone validation and G1/U1 closure remain separate, pending steps.

**Historical wording:** the body preserves the proposal and individual-approval history.
Statements that complete U0001 acceptance or the stub-source exception is still pending
are superseded by this full acceptance; they do not reopen the accepted choices. Explicit
future-sprint obligations, upstream ADR statuses and implementation limitations remain.
The original pre-acceptance file is preserved in the publication proposal identified in
the acceptance record.

**Reference:** rk-sim `1e5706e0ebfcc67c1a7333079a35b75f693e9963`, read only from
`../rk-sim-u1-pin`, verified clean. This supersedes the historical U0 assumptions;
execution-plan STATUS already records the approved pin advance. Lane A uses
`u1/contract` in `../rk-uarch-u1-a`, based on
`af3b1bc3df3171d196394a58f62202ad50845dfa`. Javid explicitly approved retaining that
pin-documentation commit; its parent is `fa16aeb5671f0f0fbfc372d7d57487fddaf65933`.

## Context and authority

The shared vocabulary must exist before engines, mappings, evidence fixtures and the
rk-sim table reader can agree. U-P1 authorizes complete uncommitted proposals in
human-owned contract/ and docs/decisions/. Every choice below marked proposed is
implemented for review, not accepted by its presence in code. G1 also requires Lane B's
independent parity and CI work and human acceptance; this proposal does not satisfy G1.

Read against build-spec §§2.3, 2.4, 2.6, 6.1 and 7; the pinned provenance, execution,
workload, channel and fidelity schemas; IterationCost/IterationCounts/iteration_cost;
operating_point; ADRs 0011, 0016, 0021, 0026 and 0027; and P16's baseline. P16 is
future work at this pin and supplies conceptual names, not implemented operator IDs.
ADR 0027 itself still says proposed/awaiting confirmation; this document does not
upgrade its status. ADR 0016 distinguishes admissibility from implementation: these
schemas admitting a fidelity level do not claim an engine exists.

## Preparation ownership — accepted direction in U0019

[U0019 — Standalone preparation and prepared-input replay](U0019-standalone-preparation-and-prepared-input-replay.md)
records Javid's **accepted architectural direction**, committed by the coordinator as
`89313ee` (`89313eef20e6b252d235b40a680a1464c52c636a`) on 2026-10-06. The coordinator's
amended U-P1 prompt requires this ownership record. U0019 and that prompt were read
from `../rk-uarch`; this reference is a later coordination milestone, **not a replacement**
for Lane A's historical `af3b1bc` implementation base or its `fa16aeb` parent above.
The canonical U0019 link resolves in the combined repository; no ADR is copied into this
worktree by this documentation-only follow-up.

- Preserve standalone model-to-workload and policy-to-mapping preparation. An external
  producer, live rk-sim service or compiler must not become a prerequisite for running
  or testing rk-uarch. Local preparation and validated prepared-file inputs reach the
  same engine boundary, reusing OpSpec and TaskGraph rather than introducing a new IR.
- Engines consume resolved inputs. Imported rank-local shapes and supplied mappings
  are authoritative within validated, supported scope (initially balanced TP and a
  representative rank). Engines must not silently re-shard, divide counts by tp again,
  choose replacement fusion or overwrite an imported mapping. Unsupported scope is
  refused. Operator-only imports may explicitly select a local mapper; that is local
  preparation, not replay of a supplied mapping.
- Preparation owns resolved placement, tiles, transfers, dependencies and scheduling
  policies; simulation determines timing, contention and stalls. The fork's pinned
  internal mapping remains an explicit, provenance-recorded delegation and must refuse
  exact imported mappings it cannot honor. Equal policy names alone do not establish
  mapping equivalence. Analytic inputs need an explicit analytic scope, not invented
  detailed placement.
- **U0003 owns the concrete prepared-input schemas and public contract revisions**:
  exact fields, versions, content identity/canonicalization, validation and fixtures
  must be settled before U2 implementation. Imported work's authority does not bypass
  compatibility or HardwareSpec/detail checks: a producer must never omit shared_sram
  from fidelity_detail when HardwareSpec declares that resource; use "unrepresented"
  when unsupported. Omission continues to mean physically absent hardware.
- **U1 records ownership only.** No future payload fields, exporters, replay machinery
  or U2 implementation land here. rk-sim continues consuming table files at runtime;
  future upstream exporters require their own integration decision.

U0019's direction is accepted, not a new open choice in U0001. It does not accept the
complete U0001 proposal, settle U0003's future fields, raise fidelity or evidence grades,
or close G1/U1. The optional-SRAM rules, explicit DRAM timing modes, approved name-only
Channel mapping and all other existing proposal content remain in force. Reza's approval
is not claimed.

## The nine seam rules

1. **One row is one chip's shard, one iteration, all layers, excluding collectives.**
   Standalone preparation constructs one rank of the requested tp split; imported rank
   shapes follow U0019's supported-scope authority above. The rk-sim table cost must use
   a **tp divisor of 1**, even when the surrounding plan's tp is 8. Divide again and
   the same parallelism is counted twice. rk-sim adds its own collective cost once.
2. Decode uses B equal-length sequences, each T/B tokens. Prefill uses n equal-length
   prompts of L tokens, with n=T²/Q and L=Q/T for Q=ΣSᵢ². Unequal compositions are
   an approximation, not secretly exact. Surface measured interpolation, composition
   and layer-reuse errors as run warnings; never use these errors as corrections.
3. The reader checks the reachable workload envelope against the table at build time.
   It refuses extrapolation. A system default can degrade with a region-naming warning;
   an explicit per-component override raises. Request validation checks axis maxima;
   the future reader must also check lower bounds and actual reachable regions.
4. DVFS selects/interpolates on the table's frequency axis. It cannot divide a duration
   by frequency and pretend memory scales identically. Missing frequency support is a
   hard error. operating_point integration belongs to the later rk-sim boundary.
5. Preserve rk-sim activity meanings. Matrix/vector counts use matrix_ops/vector_ops;
   the table's byte fields map explicitly to memory_read/memory_write channels, as
   detailed below. SRAM and flit-hop extensions do not become supported rk-sim
   channels: carry them as unmodelled until a separately approved reader supports them.
6. There is one set of hardware facts per chip. Verify the referenced hardware hash
   and compare every derived parameter with the component's parameter value. Table
   provenance.params is the output of derive_rk_params for that spec. U-P1 defines
   its carrier; U-P3 implements derivation and U-P19 implements reader comparison.
7. R1's back-to-back iteration model consumes **steady** tables. A cold table is a
   build-time InitialStateMismatch, never silently accepted or warmed by the reader.
8. The table's kv_layout.block_size_tokens must equal the plan's block size at build
   time. A mismatch is KvLayoutMismatch; the reader cannot reinterpret KV traffic.
9. The table's **tp must equal the component plan's tp** at build time. A table built
   for another tp raises TpMismatch and is never rescaled. This check coexists with
   rule 1's divisor of 1: one validates the workload split, the other avoids dividing
   already-sharded work a second time.

## Accepted defaults

Javid accepted all defaults below with the complete ADR. Alternative/recommendation
wording is retained to document the decision rationale.

| Topic | Proposed default implemented/documented for review | Alternative and consequence |
|---|---|---|
| Applicability bins | Operational intensity / chip ridge: low <0.5, middle 0.5–2 inclusive, high >2; cross with array underfill. NoC/DRAM load: low <0.30, middle 0.30–0.70 inclusive, high >0.70. | Different boundaries require new evidence bins; continuous matching needs an evidence-distance rule. Recommend the build-spec bins. |
| Array fill for rectangular arrays | Underfilled if M<array.rows or N<array.cols; full otherwise. Classify the operator using the array and mapping that actually execute it. | min(M,N)<min(rows,cols) can hide one-axis underfill. Recommend the per-axis test; it agrees with the proposed square-array shorthand. |
| BLOCKFP8 | BLOCKFP8 evidence does not cover fp8 by name or byte width. PrecisionFormat retains exactly rk-sim's eight members. | A separately justified cross-format equivalence could expand applicability. Recommend no equivalence in 0.1. |
| Shared SRAM | Optional in contract 0.1. Engines list it as unrepresented until support after U8; such a table cannot be C2. | Defer the schema itself and require a later minor bump. Recommend inclusion now. |
| Initial state | Request default steady. Prime once at the same point and report the second iteration; measure two-primes vs one. Cold means empty SRAM, closed DRAM rows, no in-flight DMA. Tables carry the state explicitly. | Require every request to spell it out. Recommend steady default plus explicit serialized value. |
| Omissions | Host/runtime outside-device time, translation, coherence, mixed prefill/decode; MoE additionally routing, imbalance and all-to-all. | Add unsupported modelling rather than warnings: out of U-P1 scope. Recommend declared omissions. |
| Shard | One Megatron-style tp per table: split attention heads; split KV heads when at least tp, otherwise replicate evenly; split FFN up/gate columns and down rows; vocabulary-parallel embedding/lm_head. No collectives in the shard. | Whole-model tables with a reader divisor give wrong nonlinear costs. Recommend explicit shards. |
| Applicability location | Per row. Every operator must be covered for class, precision and shape regime; NoC/DRAM also need load-regime coverage. Family and mapping-match must agree. Unknown is not covered. | Table-wide optimistic union could badge uncovered rows. Recommend per-row intersection. |
| Clock domains | cores→core; nocs/sync/shared_sram/controller credits→noc; DRAM timings→dram. Scale core and domains with scales_with_core=true. Resolve each frequency once with round(freq_hz×ratio), or round(freq_hz), to integer Hz; every engine and U-C0 uses that integer. Never store a rounded period. | Independently rounded clocks can violate the common roofline floor. Recommend the build-spec assignment. No clock executor is added here. |
| Fidelity | compute 0/1/2; noc and dram 0/1/1+ts/2; shared_sram absent or 0/1/1+ts/unrepresented; sync exact or approx(Q=<positive integer ps>); layer_reuse boolean. Same model in requests, tables and model identity. | Separate vocabularies drift. Recommend one model. No synchronization implementation is added. |
| Row keys | Decode phase/batch/total_context_tokens/frequency_ratio; prefill phase/n_prompts/prompt_tokens/frequency_ratio, where prompt_tokens is per prompt L. | Using total prefill tokens loses the canonical shape. Recommend the specified keys. |
| Embedded model card | Embed hash, badge, ledger IDs, validated band with full scope, and energy verification. Full ModelCard separately contains model identity and L0/L0m/L1/L2 report hashes. | A bare file reference cannot convey the badge without another artifact. Recommend the specified embedded summary. |
| Attention | attention_fused is QK score → softmax → AV over KV tiles; count the sum of all three, with Q/K/V/O only in DRAM. Keep the three unfused names available for explicitly materializing policies. | Unconditionally materialized scores charge quadratic DRAM traffic. Recommend fusion. |

Shape/load bins are semantic proposals here, not an applicability implementation.
The scope carrier records named regimes; U-P4 must implement the accepted classifier
and reject unknown regime names as evidence, rather than treating arbitrary strings as
coverage. There is no BLOCKFP8 enum member or fallback conversion.

## Channel mapping — approved by Javid

Javid (@jjaffari), acting human approver for both U1 lanes, approved preserving
Row.counts fields matrix_ops, vector_ops, memory_read_bytes and memory_write_bytes.
This is the canonical record referenced by U0002's naming-translation decision:

| Row.counts field | rk-sim diagnostic Channel |
|---|---|
| matrix_ops | matrix_ops |
| vector_ops | vector_ops |
| memory_read_bytes | memory_read |
| memory_write_bytes | memory_write |

This is only a naming translation: **no scaling, no tp division and no null
conversion**. Numeric values are unchanged; null remains null, including decode
memory_write_bytes. Every field must have exactly one mapping; destinations must be
unique and valid vendored Channel literals. Unknown fields fail. The MAC=two-operations
counting convention applies when counts are produced, not as a conversion in this map.
Replica-to-rank projection in B's parity harness is separate from this name-only mapping.
U1 implements a test-only translation, not the later rk-sim integration.

This choice is settled, not an option still awaiting review. Approval of this mapping
does not accept U0001 as a whole or any other proposed decision below. Coordination
sources read from Lane B, without edits: U0002 §4 and U1-U-P2-handoff's exact text for
Lane A. The coordinator reports that the integrated Channel mapping check passes.

## Accepted resolutions and alternatives

### Carrier parity versus the pinned stub-source loophole

The five rk-sim fields keep their names and types (provenance is nullable only to
permit stipulations). Claims need provenance; non-stub claims need a nonblank source;
claims forbid rationale. Stipulations require null provenance/source/date and a
nonblank rationale. Non-finite values and blank units are refused.

Pinned rk-sim accepts source="" or whitespace on a stub because it tests has_source;
the prompt explicitly requires source=None. **Accepted: enforce the
prompt's stronger rule**, as implemented, and record a narrow negative-input parity
exception in U0002. Alternative: reproduce the loophole exactly; that contradicts the
prompt's stated invariant and would require Javid to amend it. Ordinary five-field
claims round-trip by comparing the five-field projection, not by feeding kind and
rationale back into rk-sim's extra-forbid carrier. No normalization silently converts
blank source to null.

### Parameter identity formula and MoE

ModelSpec's field names, defaults, head_dim property and both validators are copied
from the exact pin. ModelShape defines the missing dimensions; check_parity compares
both global counts before sharding, within 1% of ModelSpec's respective count. The
message prints both implied and declared total/active values.

**Proposed/recommended bias-free decoder formula:** let D=d_model, Hkv=kv_heads,
Dh=D/n_heads, L=n_layers, V=vocab_size and P=3 if gated, otherwise 2. Per-layer
attention weights are 2D²+2D·Hkv·Dh. Add 2D norm weights per layer, D final norm weights,
and V·D embedding weights once if tied or twice otherwise. Dense FFN adds L·P·D·d_ff.
MoE replaces that FFN by L·P·D·expert_d_ff times n_experts for total, or experts_per_token
for active, plus L·D·n_experts router weights in both counts. No shared expert or biases
are silently inferred. expert_d_ff is required exactly for MoE; mha requires all heads
be KV heads and gqa requires fewer KV heads.

Alternative: omit norms/router as negligible, or add architecture-specific formulas.
Recommend the explicit formula above for 0.1; bias/shared-expert variants need a later
contract amendment rather than identity errors being ignored.
**F5 decision approved by Javid during Stage 2:** for MoE, d_ff and expert_d_ff are
redundant compatibility fields for **one expert's FFN intermediate width**, and must
be equal at the model/shape validation boundary. Total expert parameters use n_experts;
active expert parameters/work use experts_per_token, each exactly once, with shared
and non-expert terms separately accounted for. Dense d_ff is unchanged. This preserves
B's Mixtral sidecar (both widths 14336); it does not accept the entire parameter formula
or the complete ADR. The formerly ambiguous "dense-equivalent width" wording is withdrawn.
The coordinator reports that all three actual sidecars, including MoE, pass
check_parity. That compatibility evidence does not accept this parameter-accounting
proposal. The inline 70B-shaped test counts 70,553,706,496 parameters; this is synthetic shape-accounting
acceptance, not a new sourced model card or Lane B model-shape fixture.

### KV replication and vocabulary divisibility

**Proposed/recommended:** when kv_heads<tp require tp divisible by kv_heads, so replication
is balanced. When kv_heads>=tp require kv_heads divisible by tp. Reject head/FFN/expert
width indivisibility with ShardIndivisible and the dimension name. Vocabulary need not
divide tp: propose padding to ceil(V/tp) slots per rank, masked outside V, keeping original
V for global identity. Alternative: reject nondivisible vocabulary or support unequal
ranks. Padding best preserves a single canonical-rank table. This schema does not create
padded tensors; U-P3 must implement the accepted rule and name its count deviation.

### Hardware and preset details

All numeric leaves are SourcedValue, except coordinates, list structure, clock scaling
booleans and a format's byte width. Counts must be positive and integral; an unpublished
reference count uses stub, never a stipulation. Unknown is provenance, not an invented
published count. HardwareSpec recursively rejects reference stipulations with the full
parameter path. Core/array grids, banks, engines, outstanding counts, NoC resources,
DRAM organization and controller queues/credits all use the carrier.

**Revised proposal; direction approved by Javid on 2026-10-06.** Add one required
field alongside the existing timing fields:

```python
timing_source: Literal["direct", "preset"]  # required; no inferred/default mode
timing_preset: TimingPreset | None = None   # existing {file, sha} carrier
timing: DramTiming                        # existing explicit values
```

This is the smallest clear representation: one typed discriminator, no new wrapper or
per-leaf origin model. Direct mode requires timing_preset to be null or omitted. Its
values carry their own claims or stipulations; no preset fallback is allowed. All
legitimate citation strings remain valid regardless of `@`, `.yaml`, `.yml`, `.cfg`,
or any other punctuation/extension. The parser never infers origin from a citation.

Preset mode requires exactly one named timing_preset with a nonblank file and full
40-hex pinned SHA. Every non-stub timing claim must cite exactly file@sha; any different
file, SHA or datasheet citation is refused. A missing/null/unpinned preset is invalid,
even when all timing leaves are stubs. Direct mode with a preset is also invalid, so
there is no ambiguous dormant fallback. Mixed preset/datasheet claims remain unsupported
in 0.1. Generated JSON Schema includes direct/null and preset/required-object conditions;
Pydantic additionally checks exact claim citation equality.

Both modes preserve existing provenance treatment: stub claims have source=None;
stipulations have null provenance/source/date and a nonblank rationale. Stipulations
remain legal only for proposed designs; references reject them with the parameter path.
In preset mode a stub or stipulated leaf is explicitly supplied as such, not filled from
the preset or silently converted to a claim. **A declaration cannot independently prove
that a citation is truthful** or that a user selected the right mode. No documents or
presets are opened here. This replaces, rather than supplements, the old source-string
heuristic.

Both examples below are **synthetic timing fragments under memory.dram**, not hardware
facts. The other required DRAM fields are supplied by the containing spec. Complete
standalone Dram examples, accepted and round-tripped in tests, are in
`contract/tests/fixtures/dram_timing_modes.json`.

Direct timing (the `@` and `.yaml` citation is deliberately ordinary):

```yaml
timing_source: direct
timing_preset: null
timing:
  t_rcd_cycles: &stub {value: 1, unit: cycle, provenance: stub, source: null}
  t_rp_cycles: *stub
  t_cl_cycles: {value: 1, unit: cycle, provenance: estimated,
                source: "synthetic://direct@lab/timing.yaml"}
  t_rfc_cycles: *stub
  t_refi_cycles: *stub
```

Preset timing (the repeating SHA is a synthetic full-length pin, not an oracle source):

```yaml
timing_source: preset
timing_preset: {file: synthetic/preset.cfg, sha: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa}
timing:
  t_rcd_cycles: &stub {value: 1, unit: cycle, provenance: stub, source: null}
  t_rp_cycles: *stub
  t_cl_cycles: {value: 1, unit: cycle, provenance: estimated,
                source: "synthetic/preset.cfg@aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}
  t_rfc_cycles: *stub
  t_refi_cycles: *stub
```

This required field changes the unfrozen 0.1 proposal; callers must set the mode
explicitly and regenerate schema/fixtures. No already-accepted 0.1 contract is claimed.

SRAM capacity requires energy.pj_per_byte.sram. Cross-version re-stipulation when a
study changes SRAM belongs to the later study comparison, not single-spec validation.
Categorical proposals: dataflows weight_stationary/output_stationary; direction
positive/negative/bidirectional; interleave channel_hash/round_robin; controller
fr_fcfs/fcfs, open/closed; sync noc_semaphore/hardware_barrier. Alternative: broaden
these sets when a supported engine needs more. Recommend this finite initial set,
with unsupported engine fields always reported as unrepresented.

### Errors, fidelity and evidence

Each §7.4 raising case has a distinct exception and default user sentence. Minor-version
mismatch is a UserWarning. ErrorRecord {code,message} transports either without engine
imports. Pydantic wraps ValueError subclasses; its error context preserves the concrete
exception, tested for all four U-P1 raising cases. Future reader/mapping failures have
schema round-trip tests, not fabricated engine implementations.

**Revised composite proposal; direction approved by Javid on 2026-10-06.** Evaluate
these branches explicitly:

1. C0 when compute=noc=dram=0 and shared SRAM is absent, unrepresented or at level 0.
   All represented hardware is then at level 0. Sync may be exact or approximate;
   neither approximate sync nor an unrepresented resource contributes hardware detail.
2. C2 only when compute=2, noc and dram are 2 or "1+ts", sync is exact, and shared
   SRAM is "1+ts" **when hardware has it**. Omission means physically absent; no
   shared-SRAM prerequisite then applies. For an existing resource, "unrepresented",
   0 or 1 is insufficient for C2.
3. C1 for every remaining configuration with higher hardware detail that fails any
   C2 prerequisite, including mixed 2/0/0 and insufficient shared-SRAM detail.

**Optional-resource clarification, 2026-10-06:** this restores the original meaning
of omission after the coordinator clarified the ambiguous "missing shared SRAM" wording.
Omission is not unknown or unmodelled. The earlier interpretation requiring an explicit
shared-SRAM level for every C2 vector is superseded; synchronization rules stay corrected.

For compute=2, noc="1+ts", dram=2, sync="exact":

| shared_sram | Composite |
|---|---|
| omitted (hardware has none) | C2 |
| "unrepresented" | C1 |
| 0 | C1 |
| 1 | C1 |
| "1+ts" | C2 |

A later producer must enforce HardwareSpec/detail consistency: emit a shared_sram level
whenever HardwareSpec declares the resource, using "unrepresented" when unsupported.
Never omit the key for existing hardware; omit it when the hardware has none. FidelityDetail
alone has no HardwareSpec to compare, so this cross-artifact check belongs to producer
integration. An omitted key is a declaration of physical absence, not an inference by
this parser. A dedicated no-shared-SRAM C2 table test accepts a row at its own roofline
and asserts the roofline-specific refusal below it, proving that validator still runs.

The detail vector is not rewritten: approximate sync and unrepresented resources remain
visible. Switching exact to approximate sync can leave C0/C1 unchanged or lower C2 to C1,
never increase the composite. Tests enumerate all 240 legal hardware-level combinations,
both layer_reuse values, exact sync and two approximate quanta (1 and 1,000,000 ps).
Layer reuse does not add hardware detail. Contract 0.1 requires exact sync for C2;
measured approximate-sync support needs later explicit contract admission, not just a
citation to a curve. This adds no parallel simulation or evidence machinery.

Error statistics carry n_samples. Zero samples require null errors, never a fabricated
zero. Composition includes decode and prefill sub-sample counts and their sum at the
parent; interpolation carries a nullable weighted median; cold-vs-steady carries the
same-sample priming deviation. Alternative: omit empty statistics entirely. Recommend
required blocks with null values, so the toy and consumers can display "unknown".

ModelCard has no numeric defaults. Badges exclude spec_derived for models; above-stub
requires evidence IDs. Carrier validation cannot prove ledger IDs exist or are in scope.
Energy reports are keyed by mac/sram/noc_hop/dram/static coefficient family; null family
reports and null overall energy_verification mean unverified. All *used* families must
have their own L2 support before a product can label energy verified. Duration evidence
never establishes energy accuracy. U-P4 owns evidence loading, scope and badge ceilings.

### Wire representations and hashes

**Proposed/recommended:** provenance.params is a sequence of {name,value:SourcedValue};
conditional_on is a sequence of {path,value:stipulation}. No derived values are fabricated
by U-P1. VisitWeights is {decode:[{batch,total_context_tokens,weight_ratio}],
prefill:[{n_prompts,prompt_tokens,weight_ratio}]} with positive relative weights, normalized
by the consumer. It is frequency-independent, as the spec's (B,T)/(n,L) description is.
Alternative: a keyed density map or future timeline export carrier. Recommend named
records to avoid opaque tuple keys; a future timeline adapter must reconcile the shape.

Canonical JSON is UTF-8, sorted object keys, compact separators, unescaped Unicode,
Python finite-float repr round-trips (normalizing signed floating zero to 0.0) and
preserved array order. spec_hash/request_hash
first validate and serialize defaults; table_hash does the same but excludes only its
own top-level table_hash, keeping all other identities. SHA strings have sha256: prefix.
Integer/float distinction follows the model's declared type; list order is meaningful.
F13 does not make axes strictly increasing: [1.0, 0.6] remains a legal, documented
frequency axis. Different list orders intentionally have different identities. U-P7 must
order interpolation coordinates for evaluation without mutating the request's identity.
Numeric voltage_ratio keys that coincide after parsing (e.g. "0.6" and "0.60" together)
are rejected instead of silently losing one coefficient.
Alternative: full RFC 8785 normalization would change float/integer spelling. Recommend
the prompt's repr convention, with cross-language vectors added before another producer.
Hash functions compute expected digests; parsing alone does not authenticate a supplied
digest. The future table reader must compare it with table_hash(table).

Pydantic's frozen=True prevents field reassignment, not mutation inside dict fields;
callers must treat carriers as values and revalidate changed JSON rather than mutate
nested mappings or use model_construct/model_copy(update=...) as validation. Alternative:
custom immutable mappings would complicate the file carrier and schema tooling.

## Coordination update — 2026-10-04

The coordinator combined this proposal with B's actual snapshot and tests and reports
that all three sidecars pass check_parity; ModelSpec/PrecisionFormat identity, claim
round-trip, stipulation refusal and the exact Channel mapping checks also pass. These
are coordinator-reported integration results, not a new Lane A test run or acceptance
of the remaining decisions. They supersede B's earlier pending-A descriptions for those
checks. The only reported integration failure is B's overly broad ADR pin parser;
B is fixing it. The exact rk-sim pin and useful implementation-base/parent references
above remain unchanged. No Lane B worktree file was edited.

## Policy revision direction — 2026-10-06

Javid approved correcting the composite branches and replacing timing-source heuristics
with explicit typed direct/preset metadata before final acceptance. The revised policies,
schema conditions, both synthetic mode examples and regressions implement that direction.
The full revised ADR remains **PROPOSED** for final human review. Strict stub source=None,
parameter accounting, KV replication/vocabulary padding and other outstanding choices
are not inferred accepted. The already-approved Channel decision and baseline/pin history
above remain unchanged. Build-spec §§2.3.2/2.4 and its U-P1 copy are reconciled with this
revision; future approximate-sync discussion is explicitly conditional on contract admission.


## Stage 2 approved hardware-unit policy (F6)

Javid explicitly approved contract-level unit validation without implicit conversion.
Every populated sourced HardwareSpec numeric leaf, including stubs and stipulations,
is checked against the full-path map below. This tightens input compatibility: inputs
previously accepted with scaled/incompatible labels now fail, naming the exact path,
supplied unit and allowed labels. The only byte-label aliases are `byte` and `B`;
no compound aliases such as B/s are added. Values and accepted labels remain unchanged.
Generic SourcedValue, vendored schemas, provenance rules, citations, and explicit direct/
preset DRAM modes are unchanged. Unit truth and citation truth are not independently
proved by declarations. Schema `x-hardware-unit-rules` documents this map; it is a
semantic validator extension, not a claim that ordinary JSON Schema checks these units.

`[]` denotes an array element and `*` a mapping key (format or frequency ratio).

| HardwareSpec path | Allowed unit labels |
|---|---|
| `clock_domains.core.freq_hz` | `Hz` |
| `clock_domains.noc.freq_hz` | `Hz` |
| `clock_domains.dram.freq_hz` | `Hz` |
| `cores.grid.rows` | `count` |
| `cores.grid.cols` | `count` |
| `cores.core_type.matrix_engine.array.rows` | `count` |
| `cores.core_type.matrix_engine.array.cols` | `count` |
| `cores.core_type.matrix_engine.macs_per_cycle.*` | `MAC/cycle` |
| `cores.core_type.matrix_engine.accumulator_bytes` | `byte`, `B` |
| `cores.core_type.matrix_engine.operand_buffer_bytes` | `byte`, `B` |
| `cores.core_type.matrix_engine.operand_bytes_per_cycle` | `byte/cycle` |
| `cores.core_type.vector_engine.ops_per_cycle` | `op/cycle` |
| `cores.core_type.sram.bytes` | `byte`, `B` |
| `cores.core_type.sram.banks` | `count` |
| `cores.core_type.sram.bytes_per_cycle_per_bank` | `byte/cycle` |
| `cores.core_type.dma.engines` | `count` |
| `cores.core_type.dma.bytes_per_cycle` | `byte/cycle` |
| `cores.core_type.dma.max_outstanding` | `count` |
| `cores.core_type.dma.request_bytes` | `byte`, `B` |
| `cores.core_type.job_overhead_cycles` | `cycle` |
| `sync.barrier_latency_cycles` | `cycle` |
| `shared_sram.bytes` | `byte`, `B` |
| `shared_sram.banks` | `count` |
| `shared_sram.bytes_per_cycle_per_bank` | `byte/cycle` |
| `shared_sram.latency_cycles` | `cycle` |
| `nocs[].link_bytes_per_cycle` | `byte/cycle` |
| `nocs[].router_latency_cycles` | `cycle` |
| `nocs[].virtual_channels` | `count` |
| `nocs[].buffer_flits` | `count` |
| `memory.interleave.granularity_bytes` | `byte`, `B` |
| `memory.controllers[].read_queue_depth` | `count` |
| `memory.controllers[].write_queue_depth` | `count` |
| `memory.controllers[].noc_credits` | `count` |
| `memory.dram.channels` | `count` |
| `memory.dram.bw_bytes_per_s` | `byte/s` |
| `memory.dram.capacity_bytes` | `byte`, `B` |
| `memory.dram.organization.ranks` | `count` |
| `memory.dram.organization.bank_groups` | `count` |
| `memory.dram.organization.banks_per_group` | `count` |
| `memory.dram.organization.row_bytes` | `byte`, `B` |
| `memory.dram.timing.t_rcd_cycles` | `cycle` |
| `memory.dram.timing.t_rp_cycles` | `cycle` |
| `memory.dram.timing.t_cl_cycles` | `cycle` |
| `memory.dram.timing.t_rfc_cycles` | `cycle` |
| `memory.dram.timing.t_refi_cycles` | `cycle` |
| `formats.*.accumulate_bytes` | `byte`, `B` |
| `formats.*.block_scale_bytes` | `byte`, `B` |
| `energy.pj_per_mac.*` | `pJ/MAC` |
| `energy.pj_per_byte.sram` | `pJ/byte` |
| `energy.pj_per_byte.noc_hop` | `pJ/byte` |
| `energy.pj_per_byte.dram` | `pJ/byte` |
| `energy.voltage_ratio.*` | `ratio` |
| `static_power_w` | `W` |
| `tdp_w` | `W` |

Non-sourced numeric leaves retain their implicit units: memory.controllers[].attach and
shared_sram.attach[] coordinates are nonnegative count indices; formats.*.bytes is a
positive byte width; energy.voltage_ratio keys are positive dimensionless frequency
ratios. No unit string is invented for these scalars. Clock scaling flags are booleans,
not hardware quantities. CoreClockDomain fixes scales_with_core=true (also its default);
NoC/DRAM flags remain explicit. No clock or unit-conversion engine is implemented.

F6 is specifically approved; final U0001 acceptance remains pending.

## Stage 2 carrier corrections and still-pending decisions

F3 adds negative-input evidence for badges, declared omissions, stipulation-only
conditions, named errors and the surviving arithmetic/scope guards. Request cycle
scanning was redundant: requests have no unit-bearing fields and forbid extra keys;
it is removed. Table output cycle checking retains only the approved A-F1 hardware-input echo exception below.
The schema unit walk now follows local references and recognizes the explicit unit in
SourcedValue rather than silently skipping foreign definitions.

F4: the schema now forbids shared_sram=null while allowing omission, matching the
corrected optional-resource rule. Omission still means physically absent hardware;
later producers must cross-check HardwareSpec and never omit an existing resource.
Request/table-owned numeric fields reject boolean/string coercion, retaining integral
JSON numbers such as tp=8.0. **F4 decision approved by Javid during Stage 2:** copied ModelSpec and generic
SourcedValue preserve pinned upstream numeric coercions, both standalone and embedded
in requests/tables, except separately decided deviations (the stricter stub source rule
is still proposed). A-owned numeric fields reject boolean/string coercion; this includes
ModelShape, operator dimensions, cards, row deviations, hardware coordinates and format
byte widths, without narrowing the generic carriers or weakening hardware unit checks.
Hashes use validated, normalized values: accepted carrier strings and their numeric
equivalents share identity. JSON Schema still rejects those numeric strings while the
copied Pydantic carriers accept them. We explicitly do not claim identical acceptance
between Python/Pydantic and JSON Schema. No global strict-mode switch is made.

F10: a present validated error band requires high_rel>0 (unknown is null); positive
point bands remain legal. Present energy-verification rung maps must name at least
one family. Partial maps/null hashes remain evidence of incomplete verification;
consumers must require every used family's L2 evidence, not just a non-null object.
Evidence applicability/promotion stays with U-P4.

F14: optional-resource omission now uses the Pydantic 2 model serializer API instead
of Field(exclude_if). No dependency floor or lockfile changes are proposed or applied;
the compatibility regression isolates the absent newer keyword, not a full lowest-version CI claim.

## Approved Stage 2 follow-up — A-F1, A-F2, A-F12 and cross-lane B-F8

Javid specifically approved these directions in the Stage 2 continuation. These are
accepted decisions within a **still PROPOSED complete U0001**. They preserve the earlier
F4/F5/F6 approvals, optional-SRAM rule, explicit DRAM modes, approved Channel mapping and
accepted U0019 preparation ownership. No Reza approval or final G1/U1 closure is claimed.
B-F8 is the parity carrier finding, **not A-F8** (the request example correction).

### A-F1 — hardware stipulation input echoes

The only cycle-valued table inputs allowed are provenance.conditional_on[*].value,
carried unchanged as a complete SourcedValue. Condition remains stipulation-only and
checks the explicit HardwareSpec field-path/unit map. Rows, diagnostics, counts, error
metrics, provenance.params and all other table fields retain cycle refusal. This is an
input echo exception, never permission to express execution results in cycles. Requests
still carry no cycle quantities. This specific approval refines the older blanket wording
in the standing cycle invariant; it does not authorize any time/cycle converter in U1.

**U-P3 owns artifact-aware validation:** resolve every condition path in the referenced
proposed HardwareSpec; require exact value/unit/kind/provenance/source/date/rationale
agreement and reject absent or mismatched paths/values. U1 knows the vocabulary/unit but
receives no HardwareSpec artifact with the table. It therefore cannot prove a given NoC
index exists, a design is proposed, or an echo matches the actual spec. The carrier does
not open files, validate sources' truth or execute a producer.

### A-F2 — required table hardware identity

UarchCostTable now requires hardware_spec_hash: Hash, the same `sha256:` plus 64 lowercase
hex format and canonical `spec_hash(HardwareSpec)` semantics as CharacterizationRequest.
The field survives round-trip and contributes to table_hash; only the table's own top-level
table_hash is excluded. No `spec_hash` table alias is introduced. The reader compares
**table.hardware_spec_hash** with **component.characterization.spec_hash**. U-P3 must
require table.hardware_spec_hash == request.hardware_spec_hash == spec_hash(spec), and
U-P19 must verify table digest/component identity. Where the actual spec is unavailable,
parsing the identity string is not verifying its contents. No cross-artifact producer or
reader implementation is claimed in U1.

The toy uses the request helper's explicitly synthetic hardware identity and a recomputed
table digest. Old unfrozen table payloads lacking this field are invalid. This is a
pre-G1 revision, not a backward-compatible change to an accepted released contract.

### B-F8 — exact parity-carrier interface for Lane B

Read B's precise proposal and representative payloads from
`../rk-uarch-u1-b/docs/reviews/U1-lane-B-flop-parity-interface.md` and
`U1-lane-B-flop-parity-payloads.json` **before implementation**. The implemented names and
semantics follow that proposal. The source digests are recorded in the Stage 2 response;
B's files were not edited or adopted as vendor artifacts. Types are in
`uarch_contract.table`, with generated schemas of the same class names.

All fields below are **required**, including nullable fields; no kind is inferred or
silently defaulted. Every model is frozen/extra-forbid and numeric fields reject boolean/
string coercion under the approved A-owned-field rules. Copied carrier behavior remains
unchanged.

| FlopParity field | Wire type and meaning |
|---|---|
| kind | `not_run`, `harness_self_test`, or `workload_parity` |
| reference_basis | Literal `rk_sim_aggregate_divided_by_tp`; an approximation, not a physical rank-local correctness claim |
| fixture_set_id | Nonblank string when run; null when not_run |
| oracle_manifest_sha256 | Raw 64 lowercase hex digits, **without sha256: prefix**; required/non-null for workload_parity, optional/null for self-tests, null when not_run |
| candidate_identity | Nonblank implementation/revision identity when run; null when not_run; caller supplied, not authenticated |
| n_fixtures | Integer count of distinct fixture ids; positive when run, zero when not_run |
| max_rel | Maximum absolute **raw** ratio over positive-reference comparisons; null for not_run or no positive denominator |
| comparisons | Sequence of ParityChannelComparison; empty exactly when not_run |

| ParityChannelComparison field | Wire type and meaning |
|---|---|
| fixture_id | Nonblank string; fixture_id/channel pairs unique within the report |
| channel | One Row.counts field: matrix_ops, vector_ops, memory_read_bytes, memory_write_bytes |
| unit | `op` for matrix/vector counts, `byte` for memory counts; MAC=2 operations, no scaling at serialization |
| actual, reference | Nonnegative finite numbers or null, in the explicit unit |
| reference_state | `positive`, `zero`, `unmodelled`, consistent with reference |
| raw_rel | Signed `(actual-reference)/reference` for positive reference; otherwise null |
| signed_adjustment_rel | Sum of signed declared ratios; positive means more actual work than reference |
| absolute_adjustment_rel | Sum of absolute declared ratios; <=0.05 per fixture/channel |
| residual_rel | raw_rel minus signed_adjustment_rel; absolute value <=0.005; null without a positive denominator |
| declared_deviations | Sequence of FlopDeviation{id, deviation_rel, reason}; unique nonblank ids and nonblank physical reasons **within this comparison** |

FlopDeviation.deviation_rel is a finite signed dimensionless ratio in [-0.05,0.05].
All `_rel` quantities use the **positive projected reference for this exact fixture/channel**
as denominator: 0.05 is 5%, not five operations or bytes. Signed and absolute sums use
`math.fsum`, raw uses binary64 `(actual-reference)/reference`, residual subtracts the signed
sum, matching B's approved harness. Reported values must equal these recomputed values;
serialize full round-trip float precision, with no tolerance widening or rounded percentage
substitution. Schema expresses types/ranges; cross-field arithmetic remains semantic validation.

- Positive reference: actual must be present. Reject declarations when abs(raw_rel)<=0.005.
  Otherwise every term, including opposing terms, spends absolute budget; require total
  absolute<=0.05 and abs(residual)<=0.005. No budget pooling across fixtures/channels/models.
- Zero reference: actual must be zero, declarations empty, raw/residual null and signed/
  absolute adjustments zero. There is no relative-error denominator.
- Unmodelled reference: actual must remain null, declarations empty, raw/residual null,
  signed/absolute adjustments zero. Known zero adjustment never converts an unknown count.
- not_run: empty comparisons, zero n_fixtures and null max_rel/all three identities.
  A rejected comparison must raise or be separately typed failure evidence; it is not a
  successful FlopParity record. A self-test's kind survives JSON round-trip; removing kind
  fails rather than promoting it. Self-test success never establishes workload parity.

The current B oracle compares three channels; vector_ops is a valid vocabulary name but
this carrier does not invent oracle vector counts. Unknown channels and mismatched units
fail. A full oracle manifest digest/candidate name does not authenticate either. B/U-P3
must check actual oracle contents, input inventory/completeness, projection eligibility,
count provenance, physical reasons for adjustments and reviewed candidate implementation.
Changing a caller-asserted kind cannot prove an arbitrary callable authentic. These are
external checks; no new engine, adapter, oracle regeneration or future prepared payload lands
in U1. U0019/U0003 continue to govern preparation.

**B implementation handoff:** construct FlopParity from the same comparison run, flatten
its comparison map preserving fixture/channel ids, collect actual/reference and units,
map its human-readable kind explicitly, attach fixture/manifest/candidate identities,
and preserve all four ratios plus declarations. Do not rerun the candidate to reconstruct
counts. Round-trip real harness output with A's actual models and add boundary/negative
cross-lane tests. The toy now has explicit kind=not_run, not an apparent successful echo.
A's direct validation of B's three synthetic payloads passes. Publication integration update
(Lane B, 2026-10-06): B's adapter and combined round-trip validation are complete and accepted
in both Stage 3 reviews; see docs/reviews/U1-publication-evidence.md. These remain harness
self-tests, not actual U2 workload parity. No temporary substitute carrier was added.

### A-F12 — approved interim projection refusal; implemented and reviewed

Javid approved **refusing** comparisons where uniform division by tp cannot represent
the declared rank-local workload because of KV replication or vocabulary padding, until
an approved component-aware projection exists. B owns the guard and its tests. A retains
legitimate replicated-KV/padded-vocabulary request support. Do not mutate oracle counts,
widen tolerances, silently drop fixtures, or absorb the scope mismatch into deviations.
The reproduced tp16/KV8 memory-read delta is 7.0713%. The rk-sim aggregate approximation
is a compatibility reference, not independent proof of actual rank-local shape correctness;
U-P3 must test the latter separately. Publication integration update (Lane B, 2026-10-06):
the interim guard and regressions are implemented and accepted by both Stage 3 reviews;
see docs/reviews/U1-publication-evidence.md. The eventual component-aware projection remains
future reviewed work. The separate embedding-accounting obligation remains in U2/U-P3;
this interim approval neither settles it nor grants an embedding exception.

F9's MoE omission remains a U-P3 producer obligation based on request.model.n_experts;
its prompt requires a Mixtral regression. No reader-visible MoE indicator is added here.
Javid's acting ownership is already authorized; stale “both founders” wording is not a
request for Reza's approval. Both lane Stage 3 reviews are accepted. Complete U0001 acceptance and G1/U1 remain pending.

## Consequences, validation and boundaries

Generated Draft 2020-12 structural schemas are stored per concrete model plus
PrecisionFormat; names are unique and collisions raise. make gen rewrites them;
make gen-check compares expected bytes including missing/extra files without writing.
Acceptance tests also run the check, so ordinary pytest fails on stale schemas. Worker B
owns CI wiring; B's handoff records the read-only freshness command and toy validation
as wired, with no hosted CI success claimed here. JSON Schema is
structural; cross-field Python rules (sums, parity, provenance conditions, composite level,
preset matching) require contract model validation as well. Do not claim JSON Schema
alone authenticates semantic validity.

The handwritten toy is explicitly synthetic: two decode rows and one prefill, null
unmodelled fields, four unknown-error blocks, embedded stub card, and digest. Its hardware, request
and card hashes are synthetic identifiers, not evidence of computed request/card artifacts.
Attribution zeros mean absent contributions in this illustrative critical path, not
claims that an unmodelled diagnostic is zero. No golden output was changed.

This proposal adds no engine, workload graph, mapper, clock executor, DRAM adapter,
model-shape catalogue, vendor snapshot, parity fixtures, evidence promotion, interpolation
implementation, CI wiring or rk-sim integration. It does not implement U-P3 or U-P2.
See ../reviews/U1-U-P1-handoff.md for tests, exact commands and remaining blockers.
