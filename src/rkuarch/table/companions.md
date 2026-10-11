# Public companion workflow

`companions.py` authenticates complete saved analytic captures and drafts declarations
for independent review. `rkuarch.provenance.companions.assemble_stub_context` is B's
required production assembly authority. Its absence produces
`PeerImplementationMissing`; assumptions, preparation, capture and drafting remain
usable. No private fallback assembly or evidence policy exists in A.

From the repository with the existing environment, an explicit example is:

```sh
uarch assumptions --model physical-resolved --output work/assumptions.json
uarch prepare hw/designs/npu-m256.yaml --model llama-3.1-70b --precision fp8 --tp 8 \
  --synthetic-assignment --output work/prepared.json
uarch capture --prepared-input work/prepared.json --assumptions work/assumptions.json \
  --output work/capture
uarch companions draft --prepared-input work/prepared.json \
  --assumptions work/assumptions.json --capture-dir work/capture --output work/draft
```

This example explicitly opts into synthetic balanced embedding assignment. A real
selected-rank assignment instead uses `prepare --embedding-hits FILE --rank-index N`
with the appropriate conserved hit vectors. Empty logical vocabulary shards still
refuse; zero local embedding hits remain supported. No hardware or carrier is changed.

**Stop for actual independent declaration reviews here.** Drafting writes:

- `model-card.json`: actual legacy model identity, STUB, empty evidence and verification,
  null validated error band and energy verification.
- `metric-dependencies.json`: exact intrinsic table/source recipes in the existing carrier.
  `review_hash` is all zeros and explicitly unresolved; `dependencies_hash` is valid.
- `review-subject.txt`: existing `review_subject_hash` of those exact declarations.
- `README.txt`: explicit UNREVIEWED status and review instructions.

No ReviewRecord or family registry is generated. Give an actual independent reviewer
the prepared input, assumptions, complete capture, model card, dependency declarations,
all supplied comparison attempts and their full original source/inventory/refusal closure.
The reviewer must supply the actual existing `ReviewRecord` for the dependency subject,
a `FamilyRegistry` declaring the exact hardware hash once, and its actual review record.
Do not substitute engineering approval, a synthetic test review, or an inferred family.

If comparisons were attempted, the final dependency declaration must include their
complete reviewed recipes as well as the intrinsic recipes. `draft` only produces
intrinsic recipes; it does not discover attempts or draft comparison policy. Review the
final declarations, not the old draft subject. The existing
`uarch_contract.hashing.review_subject_hash` excludes only the self-identity and review
pointer, allowing explicit review binding without changing the subject. Edited
`MetricDependencies`/`FamilyRegistry` files must also have correct self hashes. Supply
these records as `work/recipe-review.json`, `work/registry.json`, and
`work/registry-review.json`; no command impersonates the reviewer or authors these files.

With the received B production assembly module and actual external reviews, explicit
**no-comparison** intake:

```sh
uarch companions assemble --prepared-input work/prepared.json \
  --assumptions work/assumptions.json --capture-dir work/capture \
  --recipes work/draft/metric-dependencies.json --recipe-review work/recipe-review.json \
  --registry work/registry.json --registry-review work/registry-review.json \
  --model-card work/draft/model-card.json --no-comparisons \
  --artifact-dir work/companions --output work/context.json
uarch table --prepared-input work/prepared.json --assumptions work/assumptions.json \
  --capture-dir work/capture --context work/context.json \
  --model-card work/draft/model-card.json --artifact-dir work/companions \
  --output work/table/table.json
uarch report work/table/table.json --output work/report.html --markdown work/report.md
```

Replace `--no-comparisons` with repeated `--comparison FILE` for **every supplied
attempt**, including failures/refusals. Place its full hash-named artifact closure in
`work/companions` before assembly. The two intake modes are mutually exclusive and one
is mandatory. Before independent review, index comparison recipes as
`/comparisons/{index}/...` using **lexicographically sorted comparison hashes**.
The context uses that canonical order regardless of CLI argument order. Changing
indexes changes the review subject and requires review of the resulting declaration;
production assembly never repairs already reviewed indexes. Include all prior attempts
and any new capacity refusal, with their complete source/refusal records.

Records and raw source blobs use `<64 hex>.json`; raw blobs retain their
original bytes and byte hash. Structured objects use the existing canonical JSON plus
newline. The input artifact directory also receives the assembled output closure.
Nothing is silently filtered from the supplied mapping. B owns completeness, subject,
family, source and evidence validation. A cannot authenticate history withheld from all
inputs and does not claim otherwise. Default reports hide unvalidated predictions;
B's `--show-unvalidated-predictions` is an explicit display choice, not validation.
When rendering both modes, pass distinct HTML **and** Markdown paths, for example
`--output work/default.html --markdown work/default.md` and
`--output work/optin.html --markdown work/optin.md --show-unvalidated-predictions`.
Omitting `--markdown` uses the same table-derived default path across both calls;
conflicting content correctly refuses rather than overwriting the earlier report.

`assemble` binds only the explicitly supplied review hash (unresolved or already equal),
rehashes that declaration and delegates all review/source policy to B's exact API.
Missing, stale or rejected review is not repaired. It writes `context.json` plus the
returned hash-named package only after B succeeds. A checks returned identities before
writing. Outputs are preflighted as a set; differing files, aliases and symlinks refuse
with `OutputConflict`. Existing identical bytes are preserved. Inputs with equivalent
but noncanonical JSON bytes at an output pathname are not silently rewritten; use a
fresh output directory/canonical structured companion copies. There is no transactional
rollback guarantee for an external filesystem error after successful preflight.

`table --capture-dir` authenticates and reuses saved jobs/results, requires
`--prepared-input` and workers=1, and never prepares or executes. Without that option,
`table` retains its existing analytic execution path. A table writer creates its own
adjacent `artifacts/` so the whole output directory can be moved and reported offline.
The table CLI authenticates and retains the complete explicit hash-named input package,
including original raw reference members and capacity-refusal inputs that a validator
may reach through manifest metadata rather than direct envelope fields. Keep the
artifact directory dedicated to those hash-named objects/blobs; invalid extra members
refuse under the same directory reader used by assembly. Missing original inputs are
not regenerated or replaced by a reviewed subset.
Captured-record replay is neither new engine execution nor a hardware measurement.

## Python boundaries

```python
load_captured_work(directory: Path, prepared: PreparedBundle,
                   assumptions: AssumptionSet) -> CapturedWork

draft_companions(captured: CapturedWork) -> tuple[ModelCard, MetricDependencies, str]

# Owned by B; called lazily, with this exact signature:
assemble_stub_context(captured: CapturedWork, *, dependencies: MetricDependencies,
                      registry: FamilyRegistry, model_card: ModelCard,
                      comparison_hashes: tuple[str, ...], artifacts: Mapping[str, Any]
                      ) -> tuple[ReportContext, Mapping[str, Any]]
```

Saved capture membership is exactly the existing capture output: bundle, assumptions,
request, derivation and one job/result for every point. Missing, extra, stale, substituted
or incorrectly named members refuse. Bundle point order determines job/result order,
not directory enumeration. Validation uses the original hardware projection, current
engine/model identity, exact request and assumptions, and existing execution/result
validators; it does not recompute or certify predictions. No new wire schema is used.

Tests with synthetic declaration reviews or a peer stand-in are explicitly labelled.
The complete public chain with B's received implementation, real independent declaration
reviews and final demonstration remains a separate joint exit. Unknown error and
unverified energy remain explicit. This workflow does not generate/adopt canonical
references, fix strict support fingerprints or confer positive evidence eligibility.
