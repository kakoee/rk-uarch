# U0022 protected schema patch — ready for coordinator review

**Unapplied protected patch; no runtime implementation or installation approval claimed.**
Javid approved the design/prose at `e622673577017a50f3e436205809f76fdf7ffae7`, recorded in
[acceptance](../U3-RoPE-schema-v1-acceptance.md) at
`531d9c923c30dd465cf56c8a5865cd9ce62cdd84`. That is this patch's exact base. Javid acts for
both lanes; no Reza approval or independent review is inferred. This package completes only
the acceptance record's immediate Lane A task.

The four approved current-prose clarifications are published in
`c3e7788614406fb9926fd70de6b1a5e0d22c320d`. Their targets
were byte-identical to the approved base before application: `docs/how-it-works.md`,
`docs/u2-workflow.md`, `src/rkuarch/workload/README.md`, and
`docs/reviews/U3-G2-physical-expectations.md`. The accepted wording and all historic payloads,
counts, assumptions and normative snapshots remain intact. The original proposal is unchanged.

## Patch contents and safe reproduction

[protected.patch](protected.patch) contains exactly the proposed human-owned installation:

- `contract/uarch_contract/rotary_v2.py`: eleven additive, statically typed carrier roots.
- `contract/uarch_contract/generate_rotary_v2.py`: dedicated deterministic generator/checker.
- Eleven generated mirrors under `contract/schema/rotary-v2/`.
- `contract/tests/rotary_v2_cases.py`, `test_rotary_v2.py`, and
  `test_rotary_v2_runtime_pending.py`: complete synthetic examples, positive/refusal controls,
  schema freshness and explicitly pending admission tests.
- An additive paragraph section in `docs/decisions/U0022-explicit-rope-semantics.md`, binding
  the exact accepted design/acceptance revisions and the reviewed installation handoff.

No old root, generator, schema, engine, dispatcher, loader, CLI or public table/report path is
changed. The four future A-owned engine roots remain in the accepted design, **not this
protected installation patch**. The new contract module's docstring explicitly forbids using
`model_validate` as execution admission. Its only new semantic validation is coefficient
shape/finite bits/content identity, as in the approved prototype; inherited request/operand
checks are preserved. It exports no runnable execution-admission API.

Run from the existing lane clone/environment:

```sh
uv run --no-sync python docs/reviews/U3-RoPE-protected-patch-v1/exercise.py
```

[exercise.py](exercise.py) exports the recorded Git base into a disposable temporary directory,
applies the patch **only there**, compares all eleven schemas to the accepted prototype,
executes the checks below and removes that export. It does not install dependencies, create
a branch/worktree/checkpoint collection, run an engine, fetch a simulator or generate/adopt
oracle artifacts. Existing literal data is referenced, not copied into another checkpoint tree.
The review patch uses zero-context hunks; the script checks/applies with `--unidiff-zero` against
the exact exported base. A read-only applicability check against current main is:

```sh
git apply --check --unidiff-zero docs/reviews/U3-RoPE-protected-patch-v1/protected.patch
```

Do not apply the protected patch to the live clone as an agent. A future human installation
must reconcile intervening changes and complete U0002 before publishing a source-bound main.
The temporary export's strict refusal is intentional evidence of that requirement, not a waiver.

## Complete positive examples and actual test scope

`rotary_v2_cases.examples()` constructs complete bundle/request/assumptions carrier closures,
using `contract/tests/fixtures/u2/independent-bundle.json` **by reference**. It explicitly authors
new versions, coefficients, Q/K nodes, dependencies, cache profile and identities. This test
fixture is not an automatic upgrade service or production producer. It imports no preparation,
counting, engine or transcendental function. To inspect every field in an applied temporary
export, run with that export's root/src/contract on PYTHONPATH:

```python
import json
from contract.tests.rotary_v2_cases import examples
print(json.dumps(examples(), indent=2, sort_keys=True))
```

Each example contains both decode C=17 and prefill length=1, tp=1, two decoder layers, BF16,
local Hq=2/Hkv=1,D=2,R=2 and a complete 17-row supplied FP32 table. The synthetic-d4 model
remains 372 parameters. Identity coefficients do not imply eliminated rotary work. Test
parameterization covers both analytic modes and both pairings; inputs are complete carriers,
not submitted jobs or executed results. The assumption model's hash explicitly denotes a
test-only unimplemented engine. No result or timing is manufactured from this stand-in, and no
named-model coefficient equivalence is claimed.

Executed positive controls verify round-trip bytes, coefficient identity, point/intent/bundle/
request/assumption joins, exact positions, Q/K dimensions, and expected projection/KV/attention
edges. These are assertions about authored examples, **not a new general closure validator**.
Finite coefficient controls include both zeros, positive subnormals, the smallest normal and
positive/negative maximum finite values. Independently rehashed infinity/NaN encodings still
refuse, so stale hashes cannot mask missing finite-bit checks. Other executed refusals cover
bit syntax, odd/small R, table dimensions, booleans, dtype, finite tampering, required fields,
explicit null binding, v1/v2 request/bundle/operator separation and duplicate-key JSON parsing.

The module preserves exactly the accepted prototype's JSON Schema for all eleven roots.
It intentionally preserves existing carrier primitives/defaults, rather than making an
unreviewed schema tightening. The new dedicated generator checks the entire flat inventory
of its own subdirectory. Check mode is read-only; missing/changed/extra mirrors are stale.
Generation refuses unexpected JSON files rather than deleting them. No new files are added
to the old generator's root inventory.

## Every section 2 obligation: enforcement and test disposition

The following maps [accepted proposal section 2](../U3-RoPE-schema-v1/README.md) to precise
future admission work. **PENDING** means no executed runtime test or admission guarantee.
A's proposed `workload/prepared_v2.validate_execution_bundle(value)` must complete all graph/
closure/support guards before returning an execution-admitted bundle. It must parse strict
JSON at the input boundary, select v2 explicitly and never strip a whole graph to validate it
as v1. For nonrotary nodes only, after proving rotary is null, it may reuse existing
`validate_prepared_op` on a separately parsed old PreparedOp to check unchanged local rules;
that does not validate or downgrade the v2 graph. These future interfaces require the next
runtime authorization; this patch implements none of them.

| Obligation | Enforcement point and discriminator | Status in this patch |
| --- | --- | --- |
| §2.1 coefficient format/hash, finite binary32, rows/width, even R>=2, preserved signed-zero bits | RotaryCoefficients validator; valid rehash before nonfinite refusals, finite tamper without rehash, signed-zero hash difference | **Executed** carrier tests |
| §2.1 supplied bytes authoritative; no generation/defaults/ambient lookup | Explicit inline closure, then producer-disabled loader replay; missing coefficients is already a required-field refusal | Required-field refusal executed; disabled-producer replay **PENDING** |
| §2.2 intent/point/bundle identities bind all nested fields | New loader verifies each self hash and intent_hash with existing canonical primitives after new-root parsing; change an edge/position/binding and rehash enclosing objects independently | Positive authored joins executed; general tamper admission **PENDING** |
| §2.3 exact reconstructed request and prepared_input_hash | Future new request join compares full intent (excluding prepared_input_hash) to bundle intent, then exact bundle identity; no v1 hash-helper widening | Positive join and cross-version parser refusals executed; malicious cross-joins **PENDING** |
| §2.3 hardware hash, supported format/rates and resolved hardware leaves | New loader joins hardware and checks supported compute/KV, rates, frequency and sourced derivation; coefficient FP32 storage must not require FP32 matrix support on BF16 hardware | Mismatched hash/FP8/mixed KV counterexamples supplied; actual refusals **PENDING** |
| §2.3 model/shape, rank, embedding hits, repeats, grid/state/frequency, omissions, all nonrotary rules | Preserve `_RequestFields` parity/shard/envelope checks; new loader also checks exact grid multiplicity, global/local dimensions, rank equivalence, replication, layer/group counts, conserved hits, omissions and unchanged node invariants | Inherited request parsing executed; graph-wide guards **PENDING** |
| §2.4 job duplication and full closure | Future protocol_v2.validate_engine_job joins request/bundle/point equality (not hash alone), coefficients, rank/producer, hardware, assumptions, mode/fidelity/precision/state/seed; new job hash excludes only itself | **PENDING**; four A-owned engine roots not installed here |
| §2.5 result/job identity, scopes, repeated work, counts/timing/attribution | Future protocol_v2 result validator uses strict new roots; checks every expected op/group once, instances, count sums, roofline bounds and attribution. Replay recomputes original work, so conserving invented totals is insufficient | **PENDING**; no result, count or timing execution |
| §2 assumptions and active implementation | Future prepare_engine_job validates complete algorithm map plus rotary entry and exact model/implementation closure, then binds the new assumptions identity. Same version string never permits changed code or v1 evidence | Synthetic positive assumption binding only; current-implementation refusal **PENDING** |
| Graph: exactly Q/K in decoder, nowhere else; rotary iff node kind; repeat/copies/fusion | New loader checks group-local IDs, node cardinality, target, null/non-null binding, weight_copies/work_repeat=1, no hidden rotary fusion; sum decoder repeats equals layers, head/tail once | Missing Q, doubled K, misplaced Q, repeated K and layer-repeat fixtures supplied; refusals **PENDING** |
| Graph: exact B,H,S,D,R,P, operand axes/dtypes/access/reductions/layout | New loader checks exact dimension/key sets, P=R/2, even 2<=R<=D, contiguous/null block sizes, no rotary padding, embedding metadata or KV access, X/Y same supported activation/KV format, Cos/Sin FP32 | Structural named-dimension/Operand checks execute; rotary-specific full guard **PENDING** |
| Graph: projection→rotation→Q / K append, unchanged V; unfused QK→softmax→AV | New loader requires same-group named producer roles and exact permitted dependencies as well as dimensions; validates logical index correspondence without asserting byte-layout equivalence or free physical transposes | Exact positive fused edges asserted; wrong projection/rotate-V/bypass fixtures supplied. Fused refusals and unfused positive/refusals **PENDING** |
| Graph/cache: exact encoding/table/pairing/numeric policy, position shape/content, valid rows | New loader joins intent/table/R, both bindings and graph.kv_key_encoding; decode rows=[C-1], S=1, prefill rows=0..S-1. Require table bounds after query binding, not just array shape | Rehashed short-table-for-C17, position/profile/hash/pairing mutants supplied; refusals **PENDING** |
| Graph/cache: append count/page policy, old K already rotated, no rotating all cached tokens | New loader checks one append, valid-token policies/capacity, new-token B*S extent, no offsets/ragged/sliding positions or cold-context reset. Cache declaration is not authentication of unseen values | Cached-token rotation mutant supplied; all execution checks **PENDING** |
| Graph/rank: local Hq/Hkv, replicated K, no extra tp division, partial tail, no padding | New loader checks resolved local heads and normalized K replication metadata; future independent literal count tests detect Hkv→Hq, tp division, coefficient rereads, dropped tail bytes and double repeat | Hkv-as-Hq/padding fixtures supplied; rank/count/traffic tests **PENDING** |

The fixture helper provides 28 independently named, schema-valid counterexamples. Their syntax
checks execute specifically to show that Pydantic is insufficient. The corresponding tests
first admit the complete valid control, then expect the future A validator to refuse each
counterexample. Those **28 tests are explicitly skipped** while that validator is absent. This
is not an unsupported-input waiver, and no skip contributes passing runtime evidence. Removing
the skip is a later authorized test-first step, with real positive controls required.

Further runtime test designs are pending and are **not collected** by this patch: mutate each
job duplication field independently, swap old/new request/job/result families in both directions,
rehash a dropped/duplicated rotary result, conserve wrong counts, tamper durations/attribution,
change implementation with the same version, and replay with both preparation and coefficient
creation disabled. The future positive control must be a real v2 capture under its exact engine
identity, not a relabelled old result. Separate tests retain v1 core/entry-point/protocol bytes,
old captured results and public table/report replay after dispatch is added. Full scalar-pair,
precision-conversion, literal count/traffic, TP replication, unfused attention and three-repeat
checks in accepted proposal §4 remain required before their corresponding runtime changes.
No changed implementation is labelled with the old core hash.

## Executed checks and remaining gates

The test file was authored first in the temporary export; collection initially failed because
the proposed generator/module did not exist. After adding the proposed files and fixing local
format/type issues, final patch exercise reported:

- **138 passed, 28 skipped**: 74 new carrier/fixture/generator checks plus 64 existing v1 schema
  checks. The 28 skips are solely the explicitly pending future graph-admission tests above.
- All eleven new root schemas equal the approved prototype exactly; old generated contract and
  four engine schema bytes stay fresh. Mirror regeneration is deterministic/read-only in check
  mode, with missing and unexpected-file controls.
- Ruff, both current CI mypy commands (70 source files / 31 contract-test files), and both import
  contracts passed in the export. This checks the actual proposed code, not just the patch text.
- Patched-export strict vendor check **refused** with `input support inventory changed`.
  The exercise requires that refusal. It is not reported as integrated acceptance.

Live clone: ruff, both current mypy commands (68 source files / 28 contract-test files),
both import contracts, 70 prompt/third-party/v1-schema tests and strict vendor currentness
passed. Exact approved prose delta, links, reverse applicability of the prose patch and
read-only applicability of the protected patch were checked. No live protected file changed.
The patch publication commit is supplied in the lane response; a commit cannot embed its own ID.
No full suite is appropriate for the live prose/unapplied patch: no runtime code changed. No candidate,
simulator, image, oracle generation/adoption, report evidence attachment or nightly was run.
B's accepted standalone v1 reporting task and all U0006 evidence/eligibility rules are unchanged.

**Next dependency:** coordinator review of this exact executable protected patch, then the
human installation/commit decision. The new contract module and generator would change
`scripts/u2_inputs.py::support_files()` inventory; all accepted U0002 freeze/generation/adoption
steps remain required before a changed source-bound main can be published. Ordinary commits
stay in the existing clones: no new integration branch, copied checkpoint system or final
merge procedure is introduced. Neither approving this patch nor installing its carrier tests
makes future runtime admission implemented or stale support current.

The prior 40–64h A implementation estimate still covers future tests/admission/producer/engine/
dispatch/integrated verification, not permission to start them. Human schema installation,
U0002 active work, independent review and their calendar waits remain separate. Runner
registration/manual nightly remains pending with Reza. U0005/200 seconds, candidate selection,
fallback, instrumentation and G2 verdict remain pending; no host waiver is granted.
