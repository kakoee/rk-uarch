# U2 public demonstration — independent declaration review

Date: 2026-10-10. Decisions: **recipes ACCEPTED**, **registry ACCEPTED**, each with the scope stated
below. This is a bounded declaration review. It does not validate predictions, adopt artifacts, run
assembly or complete the demonstration. Inputs were read only and were not modified.

## Reviewer and independence

- **Reviewer:** Claude (Anthropic model `claude-opus-5-5`), Claude Code session
  `f9f98029-ca8c-4a34-8cfd-b3e02454220a`, relayed by Javid. AI reviewer; not Javid and not a human
  reviewer.
- **Independence:** I authored none of the reviewed inputs: the prepared input, assumptions, capture,
  draft model card, metric dependencies or registry proposal. I also authored none of the production
  implementation (A's CLI/loader/draft, B's assembly, or the engine).
- **Disclosure:** earlier in this session I acted as the lane-B U-REVIEW adversarial reviewer of that
  implementation. I adjudicated its tests and wrote scratch probes using clearly synthetic review
  records. None of those synthetic records is reused here; both records below are new and reflect
  checks I performed.

## Exact subjects and outputs

| Subject | `review_subject_hash` | Decision | Output | `review_hash` | File SHA256 |
| --- | --- | --- | --- | --- | --- |
| `draft/metric-dependencies.json` (intrinsic recipes) | `sha256:1abb1f0825f4036a85faa3046b443388f0ab32aa5edfc7efd7c53bdbcf32e8a2` | accepted | `recipe-review.json` | `sha256:df97dfd391a3b8f0ec6daea0282bb77fcead0312324411d7045257ce48031140` | `3330e639e9ff8e63ee5eb3a5c781e624f6ec452012fcc1468cf66a535aef4d4a` |
| `draft/registry.json` (singleton family) | `sha256:1a09e9fc12c3886ca00d731ae4d069000ba4742fd56bfd7c470d7b11560d4269` | accepted | `registry-review.json` | `sha256:f204537f93f8a9f5d2a627bf0ebb7883545b80ffa180b170a42f2f43704d9aec` | `a090507e409354152d852a4b2466f1e4905e0b559c6bd177ef4b3ed87c0c4ebd` |

Both use the existing `uarch-evidence-review/1` carrier (`independent: true`), with `review_hash` =
`content_hash` of the record excluding only itself. Each validates as `ReviewRecord`.

## Environment and commands

- **Source:** private `git archive` export of tree `53f9f21b7cc3f84c0cbdb5f3f1e74e6e4aeca522`, used as CWD.
  Runtime imports used only `PYTHONPATH=<export>/src:<export>/contract` (`MYPYPATH` unset);
  `rkuarch.__file__` resolved inside the export, not the editable main checkout.
- **Interpreter:** `/home/jjaff/AI-infra-simulation/rk-uarch/.venv/bin/python` (CPython 3.12.14). No static
  checks were needed for this data review; that source tree's static and CI checks were adjudicated
  separately.
- **Commands:**
  1. A hash script over `capture-receipt.json`: all 27 listed files match SHA256 and size; the capture
     directory holds exactly its 20 listed members and draft/ exactly its 5.
  2. `python -B review-checks.py <tables/U2-public-demo-v1> <grid.json>` → **33/33 checks pass**
     (`review-checks.log`).
  3. `python -B make-records.py <tables/U2-public-demo-v1> <this dir>` → builds and validates both records
     in memory, then writes only them (`make-records.log`).

## Checks performed (`review-checks.py`)

1. **Capture authenticity and completeness.**
   - The public `load_captured_work` authenticates the 20 members.
   - There are 8 points and 8 jobs/results, ordered by bundle points, with job↔result joins.
   - An **independent in-memory recomputation** (`capture(bundle, assumptions)`) reproduces all 20
     capture members exactly.
   - The points cover exactly decode batch {1, 8} × context/seq {128, 512} and prefill n {1, 4} ×
     L {128, 512}, all at frequency ratio 1.0.
2. **Request and hardware binding.** llama-3.1-8b, BF16 compute/KV, tp 1, physical-resolved assumptions.
   The bundle hardware identity is `sha256:3b7186f3…07d9`. The export's `hw/designs/npu-l4.yaml` is
   byte-identical to the B1-accepted H1 design (`41731f6a…`), and its content equals the bundle hardware
   (design status `proposed`).
3. **Card, error, energy.** The draft card is STUB, with empty evidence and verification, null validated
   band and null energy verification; its `model_id` equals the captured legacy model id. Measured-error
   records are null with 0 samples (error unknown). Consumed analytic energy families are known-empty,
   so energy is unverified and no quantity is implied.
4. **Recipes (the recipe subject).**
   - Dependencies self-identity is valid, the review pointer is unresolved (all-zero), and the subject
     hash equals the expected value. The primary model identity is the captured model.
   - The 1,992 source and 1,992 render recipes equal `table_recipes(captured)` exactly.
   - Independently of that equality, every source recipe was checked: its artifact is a captured result
     and its metric pointer resolves; model identity is the captured model; purpose is counts for
     counts/instances, otherwise duration; granularity is operator for `/per_op/`, otherwise whole
     iteration.
   - Every source has prepared, model-assumption and model-evidence terminals at the exact bundle and
     assumptions identities, with model evidence hashing to the model.
   - Every hardware leaf is a `SourcedValue` at the exact H1 hardware identity, and every duration recipe
     includes hardware inputs. There are no nested or borrowed sources.
   - Source coverage per result equals `computation_sources(job, bundle)`. Render recipes are exact per
     row (8 rows, no wildcard), and each selects only its own row's result.
5. **Intake.** No comparison recipes are declared, and no comparison or reference-inventory artifact is
   present among the supplied capture, dependencies or registry.
6. **Registry (the registry subject).** Self-identity valid, review pointer unresolved, subject hash as
   expected, exactly one entry: `u2-h1-npu-l4-only` → `sha256:3b7186f3…07d9`, the captured hardware.

`make-records.py` additionally bound each new review to an **in-memory copy** of its subject (inputs
untouched). `verify_review` passed for both exact subjects, and the shared
`validate_metric_dependencies` passed on the bound dependency copy (1,992 render targets).

## Intake conclusion

The demonstration's inputs define exactly one fresh, standalone eight-point capture, and the capture is
reproduced by recomputation from the prepared input. No comparison was attempted in it, and none is
supplied, so empty comparison intake (`--no-comparisons`) is an accurate description of **this** run. It
is acceptable for a public workflow demonstration.

It is not a passing subset of a comparison run, and it does not replace the earlier U2 full-matrix
evidence. All physical discrepancies, capacity refusals, not-run cases and nominal/physical
obligations there remain open and separately required. Like the interface itself, this review cannot
authenticate attempts withheld from all supplied inputs; none is claimed.

## Registry conclusion

`u2-h1-npu-l4-only` is accepted **only** as an explicit administrative singleton label for exactly
hardware `sha256:3b7186f3…07d9`, the accepted proposed H1 npu-l4 design. It asserts no same-class,
silicon, measured, design or performance relationship to any other hardware. It is not evidence of
family membership for applicability transfer, and it must not be extended to other identities without
a new reviewed declaration. No measured relationship is invented.

## What these reviews do not do

- They do not validate any prediction, accuracy or error band.
- They grant no evidence eligibility; the model stays STUB, error unknown, energy unverified.
- They change no policy, schema, guard, badge, ledger or historical text.
- They do not bind review pointers, run assembly, table or report, or complete the demonstration.
  The coordinator binds the pointers and runs the remaining public commands.
- They involve no staging, commit, push, generation/adoption, tag or closure. U0021, the strict-support
  gates, the combined freeze/human lifecycle and publication remain pending.
