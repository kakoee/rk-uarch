# How rk-uarch works

U2 implements a standalone stateless analytic estimate of one chip's LLM workload,
plus reproducible tables and provenance-aware reports. The [public workflow](u2-workflow.md)
starts with a sourced hardware spec and model shape, prepares explicit operators and
mapping, executes the analytic engine, and packages the results with reviewed source
declarations. The [accepted design](u2-design.md) defines the scope and limitations.

## From an NPU specification to an iteration estimate

Hardware values declare units and either a claim with its source or a stipulation
with its rationale. H1 and H2 are proposed designs, not measured products. Validation
checks those declarations; it does not establish that a physical chip achieves them.

Preparation resolves the model's operator counts, tensor-parallel shard, KV reads and
writes, precision and selected-rank work. A row covers one chip's shard, one iteration
and all model layers, excluding inter-chip collectives. For example, decode batch 8,
context 512 means the rank's work to generate one token for each of eight sequences
with that context. Prefill has separate prompt-count and prompt-length coordinates.
The saved prepared bundle is authoritative on replay; loading it never silently
rebuilds the mapping or changes the shard.

The U2 analytic engine uses declared compute throughput and memory bandwidth to form
compute and memory time bounds. Its aggregate U-C0 bound is the maximum of aggregate
resource times; its per-operator estimate sums each operator's limiting time. These
are stateless roofline estimates. They do not model detailed queueing, cache histories,
inter-chip communication, compiler scheduling or measured chip efficiency. Per-op
and aggregate durations are checked for consistency. An internally consistent result
still has unknown hardware error.

`capture` saves one authenticated job/result per prepared point. `companions draft`
writes a STUB model card and UNREVIEWED source recipes. An independent reviewer must
check the exact final declarations, hardware-family registry and intake completeness.
`companions assemble` consumes those actual review records and refuses missing,
rejected, non-independent or mismatched subjects. It cannot prove that an author did
not withhold an attempt from every input; that is part of the external intake review.

`table` binds the hardware, prepared workload, assumptions, engine results and report
context into a self-contained package. Saved-capture replay reuses validated results
without executing producers. Canonical identities and deterministic condition ordering
make equivalent saved inputs reproduce the same bytes. U2 does not claim later
multi-worker or native-engine determinism.

## What the report says about trust

The current [0.2 contract](../contract/uarch_contract/) carries results and explicit
provenance. Structural schema validity, content identity, source applicability and
performance validation are separate checks. Hashes establish content identity; they
do not turn a synthetic record into a measurement.

The public loaders check the complete contributor closure and reject unsupported
positive model-card assertions. The actual analytic model has known-empty consumed
energy scope; that means it models no energy, not zero energy or verified consumption.
Error bands remain unknown. A reviewed source declaration does not promote a badge.

Default HTML and Markdown reports show `conditional · N stipulations` and readable
model/operation identities while hiding unvalidated computed predictions. Declared
inputs retain their sources. Explicit `--show-unvalidated-predictions` exposes labelled
STUB predictions without promoting them. [U0004](decisions/U0004-stipulated-values-and-the-estimated-ceiling.md)
and the [assembly rules](companion-assembly.md) govern these distinctions.

## Why rk-sim also estimates runtime

rk-uarch's production estimate describes the resolved physical operator graph on one
chip. rk-sim also has an existing coarse aggregate iteration-cost model. U2 retains
pinned outputs from that separate model as compatibility evidence. rk-uarch does not
call rk-sim in production or force physical work to match its aggregate conventions.

Accepted U0003 direction S separates two checks. The physical track checks resolved
work, analytic arithmetic and replay, and retains physical-versus-reference gaps.
A separate test-only nominal model reproduces the aggregate model's conventions and
checks the existing numerical compatibility limits. Passing the nominal track is not
validation of the physical workload's duration or of silicon accuracy.

The last independently rerun full adopted matrix, on `769a1fe`, retained 1,008 nominal
cases with zero duration error. The physical track retained 96 executed discrepancies,
48 capacity failures and 864 not-run cases. Those outcomes are not 1,008 successful
physical predictions. They are historical runtime evidence, not a rerun of the later
software-response tree or newly current artifact evidence.

## Current checkpoint and remaining exits

Both original reviewers accepted the scoped software responses on Git tree
`53f9f21b7cc3f84c0cbdb5f3f1e74e6e4aeca522`. B independently ran the full suite there:
1,392 passed and two strict-support gates failed, with no errors or skips. A and B
also checked CI-form lint/type commands on clean exports. This describes a reviewed
uncommitted tree, not a publication commit or hosted-CI result.

The adopted v2 reference manifest remains
`f8220c9457226562040e5646835c3073acd2f58cd7631a5eb9e74632e60cc96e`.
Source changes made its input-support binding stale. Strict current verification must
continue refusing until the combined freeze, human generation and separately approved
adoption. Historical-integrity mode cannot substitute for that gate.

The eight-point [public demonstration](reviews/U2-public-demo-v1/completion/README.md)
now uses actual accepted independent declaration reviews. Two fresh runs and a saved
replay with producers disabled reproduced all 61 package/report files byte for byte.
This completes that standalone demonstration; it does not replace the full matrix.
Documentation publication and final runtime/currentness checks remain separate from
local commits, pushing main, tagging and sprint closure.

[U0021](decisions/U0021-u2-cold-clone-validation-exception.md) requires a fresh GitHub
clone on ElfinKidsLaptop's Ubuntu/WSL2 environment plus hosted Ubuntu CI on the identical
published commit. Record actual commands and distinguish executed checks from CI jobs
that do nothing because their inputs are absent. This exception does not authorize
WSL2 simulator-performance benchmarking or waive U3's Linux self-hosted runner and
later hardware-validation requirements. No U1 CI result satisfies the U2 gate.
