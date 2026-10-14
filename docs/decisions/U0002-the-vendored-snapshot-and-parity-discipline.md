# U0002 — The vendored snapshot and parity discipline

Status: **accepted by Javid (@jjaffari), 2026-10-06 (America/Los_Angeles)**,
acting as human owner/approver for both U1 lanes. Full acceptance includes all policies
below and the narrow stub-source exception. No Reza approval is claimed.

The reviewed complete 20-file replacement is adopted into the coordinator working tree
under Javid's explicit authorization. Its manifest is
`b3a575d0e3f27a4057678a2298609a580fd5a5e1dd858b0f4af086f2dc9e0e1d`.
See the [acceptance and adoption record](../reviews/U1-acceptance-and-adoption.md) for
approved proposal identity, prior manifests, rationale and preservation evidence.
Commit, push, hosted CI, Linux-box cold-clone validation and G1/U1 closure remain pending.

The Stage 2 approvals below record how the policies were settled; full ADR acceptance
is now recorded above. Explicit U2 obligations and implementation limitations remain.
Implementation/validation evidence belongs in [the author response](../reviews/U1-lane-B-response.md)
and [the handoff](../reviews/U1-U-P2-handoff.md).

## Boundary and pin

The upstream pin is `1e5706e0ebfcc67c1a7333079a35b75f693e9963`. U0001's dedicated
`**Reference:** rk-sim \`<full SHA>\`` line must name that pin exactly once; unrelated
rk-uarch baseline/history hashes are not upstream references. Strict integration and
CI require both that ADR and Lane A's `RK_SCHEMA_SNAPSHOT` constant to match. Missing,
renamed, malformed or conflicting references fail. Explicit `--pre-contract` preparation
permits absence, but never a conflicting pin; pytest forbids combining that mode with
`--require-vendor`. This preserves the execution plan's permission to prepare U-P2
before U0001 without making integrated validation fail open.

[Accepted U0019](U0019-standalone-preparation-and-prepared-input-replay.md), recorded by
coordinator commit `89313ee`, governs standalone preparation and replay ownership.
U0003 owns the later prepared-input schemas; U-P3 owns workload production/adapters.
This ADR adds neither a workload generator nor a replacement production contract.

## Oracle ownership, inputs and coverage

Only a human runs `make vendor-rk`; its script refuses generation without the human
flag. Agents prepare tooling and synthetic tests, never actual oracle snapshots.
The clean pinned upstream supplies its actual `iteration_cost()`, count methods and
duration methods through a subprocess. No copied workload formula supplies expected
values. The pinned loader and private accelerator adapter are intentionally version-bound.
Placeholder inputs are STUB arithmetic fixtures, not hardware accuracy claims.

Generation checks HEAD, status including untracked files/submodules, all index flags,
and ignored files before and after execution. A pristine checkout and an external
oracle environment are required; ignored files that could shadow imports are refused.
The interpreter uses isolated mode and a fresh bytecode-cache prefix with writes disabled.
Copied sources, component bytes, lock and environment identity are rechecked after execution.

The **approved precision matrix** remains:

| Component | Compute / KV cache | Models × tp × queries | Records |
| --- | --- | --- | ---: |
| asic_placeholder.yaml | FP16/FP16, FP16/FP8 | 3 × 2 × 24 | 288 |
| nvidia_h100_sxm.yaml | FP16/FP16, FP16/FP8 | 3 × 2 × 24 | 288 |
| nvidia_h100_sxm.yaml | BF16/BF16, FP8/FP8 | 3 × 2 × 24 | 288 |

Each model uses tp 1/8 and 24 queries: decode B={1,8,32}, context per sequence
{128,512,4096,16384}; prefill n={1,4,16}, prompt length {128,512,2048,4096}.
The six specified decode points B={1,8,32} × context={512,4096} are included.
The 864 records retain compute and kv_cache separately. Two real
`UnsupportedPrecision` refusals cover placeholder BF16/BF16 and FP8/FP8. Never
substitute a compute peak, synthesize a duration or silently skip a query.

Component inventory must equal covered component inputs; sidecar ids must equal
covered models. Every row binds the exact component digest and sidecar model, shape
and source attribution. U1 additional PARAMS use FP16/FP16 and FP16/FP8. U2's BF16
npu-l4 case requires an explicit component precision declaration in U0003/U-P3;
that future interface is not implemented here. B-F16 stays deferred to U2: Lane B's
vendor/parity maintainer owns matrix support, Lane A's U-P3 owner owns the prepared-bundle
adapter, and U0003 owns the precision interface. Acceptance requires a BF16-only PARAMS
fixture checked against its declared compute peak and actual prepared/imported-bundle
adapter coverage under U0019. No substitute peak or future implementation is added in U1.

## Scopes and the approved naming seam

The exact mapping approved by Javid is recorded canonically in U0001:

| Row.counts | rk-sim diagnostic Channel |
| --- | --- |
| matrix_ops | matrix_ops |
| vector_ops | vector_ops |
| memory_read_bytes | memory_read |
| memory_write_bytes | memory_write |

It changes names only: no scaling, tp division or null conversion. Destinations are
unique valid Channel literals; unknown fields fail. U1 implements the seam only in tests.

Oracle `IterationCounts` are replica-wide (`counts_scope: replica`); duration is one
representative tp rank without collectives (`duration_scope: one_tp_rank_no_collectives`).
**A-F12 interim scope policy approved by Javid:** uniform division by tp is eligible
only for the declared unreplicated, unpadded shard scope. Known KV replication or
nondivisible vocabulary/head/FFN shard dimensions produce `unsupported_projection`
before the candidate is called or numerical agreement is considered. Missing required
scope dimensions also fail closed. This guard neither rejects all tp>1 nor certifies
physical correctness; A's broader legitimate request shapes remain valid contracts.
A component-aware projection remains future reviewed work for U-P3.

The frozen oracle is evidence of rk-sim's aggregate calculation. No existing workload
result is relabelled aggregate compatibility, and no new physical-correctness certification
is introduced. `rank_counts` is diagnostic arithmetic only, not an eligibility check.
The harness implements no diagnostic bypass that can satisfy the workload-parity gate.

`run_parity` retains every requested fixture in `coverage`, with `passed`, `failed`, or
`unsupported_projection` and explicit reasons. Any nonpassing entry raises `ParityFailure`
carrying the complete report; later fixtures are still evaluated. Supported numerical or
candidate implementation failures remain `failed`, never relabelled unsupported. Reports
retain available actual/reference values and all four adjustment quantities even for an
over-budget numerical failure. No partial run can enter A's successful FlopParity carrier:
B's adapter requires complete passing coverage and preserves the caller's explicit kind.
Default oracle echoes remain harness self-tests. All 864 baseline fixtures are eligible;
no frozen value, nominal input, fixture or approved tolerance changes.

**Embedding accounting is separately pending.** The approximately 6.54% nominal 8B
embedding parameter share is not an observed operation/duration offset. Preserve nominal
U1 inputs and report actual discrepancies explicitly under the approved budget. An ordinary
above-budget numerical error remains a visible failure. Only a documented scope incompatibility
can justify unsupported status; the replication/padding decision is not an embedding exception.

Decode writes remain null. Vector operations are not supplied by this oracle and are
not silently invented or converted to zero.

## Approved deviation policy (Stage 2, Javid)

For each fixture/channel with positive reference count R, let A be the actual count:

- raw error `e = (A - R) / R`;
- signed adjustment `s = sum(d_i)`;
- total absolute adjustment `a = sum(abs(d_i))`;
- residual `r = e - s`.

All four are dimensionless ratios, using **the positive projected reference R** as the
percentage denominator; 0.05 means 5%, not five operations. Positive means more actual
work than reference. Named, reasoned adjustments must satisfy **a ≤ 0.05** and
**abs(r) ≤ 0.005**. Without adjustments, abs(e) ≤ 0.005 is required. Reject adjustments
when raw error is already within 0.005, or when reference is zero/null. The 5% bound is
per fixture/channel, not per declaration; splitting terms cannot increase the budget.
Opposing physical terms can cancel in s but both consume a; cancellation never refunds
budget. Unknown fixture/channel, duplicate ids, nonfinite/negative counts and invented
zero for null all fail.

Zero reference requires actual zero, with no adjustments. Null reference requires actual
null, with no adjustments. Raw/residual relative errors are null in both cases because
no positive denominator exists; signed/absolute adjustment are zero because no adjustments
were made. That known zero adjustment is not a zero count or an accuracy estimate.
The report preserves all four quantities separately plus declarations and fixture/channel
scope. `max_rel` remains the maximum absolute raw error over positive-reference channels;
it is not a residual, accuracy claim, or a replacement for per-channel records.

Examples: +3% and +2% explain +5.5% at the exact residual boundary. +5% and −5%
consume 10% and fail. Twenty +5% entries consume 100% and fail. +3% and −2% can
explain +1% while spending the full 5% budget; exact-match phantom adjustments fail.
The roughly 6.54% 8B embedding parameter share cannot be split to evade this cap.
Its actual operation-count effect is query/accounting dependent and needs a scope
decision, not a widened tolerance or automatic parameter-count subtraction.

The default result kind is `harness self-test (not workload parity)`. An explicit
workload classification is a caller assertion, not proof of an arbitrary callable's
authenticity. U-P3 must provide implementation identity and independent review evidence.
No current self-test establishes actual U2 workload parity.

**Carrier scope approved by Javid:** revise Lane A's flop_parity carrier before G1 so
classification, attribution and these four quantities survive serialization. The precise
[interface handoff](../reviews/U1-lane-B-flop-parity-interface.md) is a proposal for A;
A has supplied the accepted carrier; B added its adapter and cross-lane round-trip tests
against a captured A proposal. No A contract is edited by B. The integrated carrier
has received review and full ADR acceptance; passing self-test round trips are not workload parity.

## Approved fingerprint and environment policy (Stage 2, Javid)

Three separate checks answer different questions:

1. **Manifest integrity:** exact file inventory/digests and upstream pin, safe paths,
   no symlink root/ancestors/entries. Passing detects no content change relative to the
   manifest; it does not prove approval, provenance authenticity or publication.
2. **Recorded identity:** GENERATOR.json has the expected keys, pin/scopes and valid
   recorded script/oracle digests. Historical artifacts may lack the new environment
   record; historical verification explicitly says current compatibility was not checked.
3. **Current compatibility:** strict integration/CI require exact equality of the full
   `scripts/vendor_rk.py` SHA256 and `ORACLE_PROGRAM` SHA256 with recorded fingerprints,
   plus complete required environment metadata. Missing/mismatched metadata fails.
   A historically intact artifact can be incompatible with current implementation.

The revised generator copies the pinned upstream `uv.lock`. Its expected digest is
bound in the reviewed generator, so CI does not need rk-sim credentials or a checkout.
`GENERATOR.json.environment` records CPython's exact version, implementation name,
all installed distributions' normalized names/versions, and the lock SHA256. Before
and after oracle execution, `uv sync --locked --check --offline --no-default-groups`
verifies the existing external environment against the pinned project's base selection
(no optional extras/default dependency groups), without syncing it. The inventory is
captured from that interpreter before/after, must be unchanged, and must agree with
versions present in the lock. Duplicate distributions fail. This records software
identity, not physical machine identity or a claim that package files cannot be tampered
with; human review remains necessary. No paths/timestamps enter generated records.

CI verifies required metadata shape, Python/implementation validity, package-version
membership, and the pinned lock digest. It does **not** equate CI's independently locked
test environment with the oracle-generation environment, nor rerun the oracle. Generation
performs the full environment synchronization check; CI checks the recorded evidence.

`--check` is strict by default. `--check --historical` is an explicitly limited integrity/
identity audit and is never used instead of strict CI. Any script edit, including verifier
or message-only edits, changes the full script fingerprint and requires reviewed human
regeneration. Oracle-program identity is separate: the Stage 2 fixes change the script,
but do not change the `iteration_cost()` bridge program or any stored oracle value.

## Nominal parameter inputs (Stage 2, approved by Javid)

Keep the existing rounded parameter counts as **nominal U1 oracle inputs**, distinct
from exact architecture-derived counts. [The parameter record](../reviews/U1-U-P2-nominal-parameters.json)
contains, for each total and active parameter value, nominal, shape-implied, signed
`nominal - implied` and `(nominal - implied) / implied`. The formula reference is A's
`model_shape.implied_params` and the U0001 formula proposal. The original 1% parameter
consistency rule is unchanged; no new threshold, correction or automatic deviation is added.

U2 must report shape-based count differences and evaluate them under the approved parity
policy. Parameter offsets are not automatically operation-count or duration offsets.
This nominal-input approval does not settle embedding accounting. The separate approved
A-F12 policy above refuses unsupported replication/padding projections. Replacement
candidates for generator fixes retain the existing sidecar/nominal bytes and attribution.

## Snapshot lifecycle and enforcement (read-only interpretation approved by Javid)

Generated files receive chmod 0444 as a **local precaution**. Git normally restores mode
0644; that alone must not invalidate an otherwise valid snapshot. Manifests detect content
changes, strict compatibility binds identity/environment metadata, human review controls
adoption of complete artifact revisions, and Git history preserves published predecessors.
Neither chmod nor manifests alone prevent edits or prove human approval. Ordinary generator
reruns continue refusing differing output at an occupied destination.

1. Freeze reviewed generator/supporting code, upstream pin, sidecars and the complete
   intended PARAMS set. Stage separately, retaining input identities and verified environment.
2. A human generates twice from the same inputs. Save distinct `created` and
   `verified-identical` outputs; the second run verifies byte identity. Input drift requires
   a fresh candidate and two runs, not relabeling different-input runs as determinism.
3. Verify manifest, inventory, required coverage, attribution, refusals, strict generator
   compatibility and integrated contract checks. Generator fixes/policies must settle first.
4. Compare metadata; upstream sources/schema/lock; component inputs/sidecars; added/removed
   fixtures; and changed existing values. Compare semantic query identities, not order alone.
5. Explicitly review any changed existing count, duration, null or refusal outcome and reason.
   Renames do not exempt changes. Never hand-edit generated files, hide differences with
   deviations, drop inconvenient fixtures, or widen tolerances.
6. After explicit human approval, adopt the complete candidate as one reviewed artifact
   revision. Record old/new manifest hashes, reason, reviewed inputs, approval reference/date
   and publication commit. Keep an uncommitted predecessor in the review archive; preserve
   already published revisions in Git history without rewriting earlier commits.
7. CI consumes only the committed revision and uses strict checks. It never fetches upstream,
   generates/adopts candidates or needs rk-sim credentials. Ordinary reruns only create a
   missing destination or verify byte-identical output; success messages make the two distinct.

First publication selects an approved artifact for its first commit; it is not a refresh
of a published artifact. A later refresh records the prior publication commit and produces
a new one. Upstream SHA alone is not artifact identity: use upstream SHA + manifest SHA256
+ publication commit. U2 may add PARAMS at the same upstream SHA by staging all retained
and new components and reviewing a complete revision. Precision selection and prepared-input
parity adapters belong to U0003/U-P3; U1's current additional-component matrix is not a promise
that all future components support FP16.

## Isolation and accepted compatibility exception

Tests alone load vendored modules by path with a private namespace; no installed `rk`
package or sys.path mutation. Import-linter forbids rk, contract/test/vendor helpers,
private vendor modules and scripts from production roots. A conservative AST source guard
also detects dynamic imports/path execution; A's exact local schema-discovery call is the
only reviewed dynamic-import exception. This guard is not a proof against arbitrary code
obfuscation. CI type-checks src, contract and scripts; schema freshness uses A's generator.

Pinned rk-sim accepts blank/whitespace source on a stub and retains it; uarch requires
source=None. Three explicit vendored regressions document this **accepted narrow carrier
exception**, not exact validator parity. Javid explicitly accepted it with this ADR.

The two earlier human snapshots remain preserved and unadopted. The reviewed replacement
is adopted locally as recorded above; first publication and G1/U1 closure remain pending.

## U0003 accepted validation-scope addendum

Accepted by Javid under U2-U0003-acceptance-v1; see
[the exact acceptance record](../reviews/U2-U0003-acceptance-record.md).

Historical acceptance above is preserved; this prospective amendment now governs the new
0.2 comparison artifacts, retain zero equality and positive count ratios/budgets. Null/absent
reference is unassessed, with actual retained and no adjustment; matching omission is not
numerical validation. The nominal test-only candidate is the compatibility subject. Physical
work instead has independent correctness tests and complete discrepancies; an aggregate
compatibility pass is not physical parity. Preserve all fixtures/refusals and A-F12 before
calls. Actual npu-l4 refresh follows the existing human generation/adoption lifecycle.


## U3 prospective dependency-policy decision — implementation pending

Accepted by Javid (@jjaffari), 2026-10-13, **for U3 closeout only**; see the
[approval record](../reviews/U3-reviewed-design-and-policy-v1/acceptance.md).
This prospective choice does not replace currently installed enforcement or reinterpret
historical acceptance. The complete existing enumerator and adopted source/artifact pair
remain required until a separately authorized, tested transition is installed and adopted.
No U4 work, installation, generation or adoption is authorized here.

The exact selected repair is the [reviewed proposal](../reviews/U3-B-artifact-dependency-audit-v1/repair.patch)
at `7afba9b16d954fd46684711764cb3718170e53aa`, SHA256
`c238574b284ebecb6f0f1253922ce01af87259f0187aad38bcda628757e8fe6b`.
Its [O1/O2 follow-up](../reviews/U3-B-U0002-bootstrap-followup-v1/README.md) discloses
removal of pre-guard future imports, equivalent resolved type hints with changed raw
annotation storage, root-write test defence, bootstrap limits and migration consequences.
The current proposed inventory is 97→56; actual M imports/initializers/data must be audited
before protected M installation. Neither count is a future exclusion quota.

The selected prospective policy is:

Keep immutable generation provenance, artifact integrity and current compatibility as
distinct obligations. Preserve all published oracle artifacts and their recorded complete
support inventories without rewriting their metadata or interpreting historical integrity
as currentness. An unversioned support inventory continues to use the existing complete
enumerator and full current-script/environment checks.

For separately human-generated and adopted input sets carrying the exact
`uarch-input-support/2` / `generator-imports-and-data/1` tooling policy, current support
comprises the conservative local import closure of the reviewed staging/generator/verifier
roots, including package initializers and function-local imports, the policy implementation
itself, all Python files below scripts/, explicitly reserved top-level module files and
existing reserved-namespace initializers, and reviewed non-import inputs. Under the actual
ROOT, scripts/, src/ and contract/ search roots, refuse any new importable top-level module
or namespace name outside the explicit reviewed local names/types. This covers names used
by transitive imports as well as direct ones; it is not a direct-import-only guarantee.
Adding a new top-level local name requires policy/source review. Nested unrelated consumer
files and non-importable prose may remain unbound, unless reached or explicitly included.
Run the name guard before non-bootstrap imports in direct staging/vendor entry points and
package initialization, and again during strict support inventory verification. Its proposed
bootstrap requires normal CPython >=3.12 with builtin sys and frozen os; other bootstraps
refuse. Trusted startup/environment and no concurrent source race remain premises, not a
sandbox against malicious interpreter hooks or arbitrary reflection. Bind existing reserved
namespace initializers so adding/changing one cannot evade the inventory.
Compare exact inventory and file bytes;
reject unknown policy, unresolved/dynamic dependency forms outside the reviewed mechanism,
ambiguous or shadowed imports, symlinks, missing/extra dependencies and content drift.
Introducing dependencies requires their inclusion and review, not unchanged output values.

Retain the complete vendor_rk script fingerprint, embedded oracle-program fingerprint,
clean upstream pin and source capture, locks and recorded environment policy, explicit
precision/PARAMS/model/source attribution, exact frozen-input/outer-copy joins, coverage,
real refusals and current adoption identity. No exclusions based on whether a file is
named report, CLI, schema or native. Imported files remain relevant regardless of label.
Consumer code that does not contribute to generation or verification may change without
regenerating a nominal oracle under the reviewed policy; its tests, implementation/result
bindings and review obligations still apply. Oracle equality is not physical correctness.

Only Javid's separately reviewed human lifecycle may create/adopt a new-policy artifact.
Freeze the exact approved code, policy, upstream and full input set; generate twice in
separate processes, check created then verified-identical, audit complete before/after
semantics and provenance, and adopt the complete candidate in a separate human decision.
CI consumes only committed adopted artifacts; it never generates, adopts, fabricates
environment records or substitutes historical checks for current compatibility.

The [exact migration sequence](../reviews/U3-B-artifact-dependency-audit-v1/migration.md)
remains future work requiring separate releases. Preserve full nominal coverage and refusals,
legacy dispatch and immutable artifacts. Changed generator fingerprints must bind the real
future human generation; passing synthetic tests cannot replace it. A documentation-only
U3 closeout uses the current valid source/artifact pair and requires no regeneration.
No runtime currentness waiver, new policy-marked artifact or completed migration is claimed.
