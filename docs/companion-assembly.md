# Externally reviewed STUB companion assembly

`rkuarch.provenance.companions.assemble_stub_context` is the pure B assembly
boundary. It consumes A's existing `CapturedWork` and existing contract carriers:

```python
def assemble_stub_context(
    captured: CapturedWork, *,
    dependencies: MetricDependencies,
    registry: FamilyRegistry,
    model_card: ModelCard,
    comparison_hashes: tuple[str, ...],
    artifacts: Mapping[str, Any],
) -> tuple[ReportContext, Mapping[str, Any]]: ...
```

The caller obtains the capture, card and draft dependencies through A's workflow.
An actual independent reviewer must supply the exact accepted dependency review;
the selected family registry also needs its exact independent accepted review.
Engineering approval does not supply either review. Assembly neither creates a
review nor fixes an unreviewed declaration. Review subjects use the existing
`review_subject_hash` rules; a changed subject needs review of that subject.
The normal tests use explicitly SYNTHETIC administrative reviews, with no authority
outside the tests. No synthetic review is issued by this production module.

Pass the complete hash-addressed artifact mapping, including raw source bytes,
review records, registry/dependency closure and all supplied comparisons, inventories,
reference contributors and refusal records. Every mapping key is authenticated;
unused invalid members also refuse. Structured values are detached into canonical
JSON-compatible objects; byte blobs remain byte-identical. The returned outer mapping
is read-only and sorted by hash. Its nested JSON objects belong to the returned store,
not the caller's input. Captured metadata, the new context and verified table closure
are added to that store. No files, producer, engine, oracle or network are accessed
by the assembly call.

Every supplied comparison object must occur exactly once in `comparison_hashes`.
Context comparison hashes are sorted lexicographically. Before external review,
comparison recipes must therefore use `/comparisons/{index}/...` paths in that
sorted order. Assembly does not rewrite reviewed paths to accommodate a different
order. Every fixture/channel must have all four comparison quantity recipes,
including unassessed, failed and refused cases. A shorter passing-only list cannot
hide a comparison still supplied in the store. An empty tuple is accepted only
when the supplied store and recipes contain no comparison. This cannot authenticate
an attempt withheld from **all** inputs; the external reviewer must assess intake
completeness. Keeping an old table/context in the supplied store also requires its
complete closure.

Actual source declarations must retain A's exact model, purpose, granularity,
applicable dimensions and terminal input identities. Exact and generic row recipes
are supported. Recursive factoring must preserve the source model and scope of the
factored recipe and the complete original terminal set; cycles and source borrowing
refuse. Whole-iteration source scopes retain all executed operator scopes. Comparison
reference sources pass the installed original-input/R202 checks independently of the
actual model's sources. Equal numerical values do not establish source identity.

The output context has empty evidence/verification indexes and the actual analytic
engine's known-empty consumed-energy scope. This is not a general energy-consumption
capture. The caller's exact model card is checked by the installed production card
validator. Positive badge, error-band or energy assertions refuse rather than being
rewritten. The public table builder and in-memory report verifier both run before
assembly returns. Default reports remain STUB, predictions hidden, band unknown and
energy unverified; opting into predictions does not change those qualifications.

With externally reviewed inputs already in memory, the supported B/public-table
sequence is:

```python
from rkuarch.provenance.companions import assemble_stub_context
from rkuarch.table.build import build_table, write_table

context, complete_store = assemble_stub_context(
    captured,
    dependencies=reviewed_dependencies,
    registry=reviewed_registry,
    model_card=draft_card,
    comparison_hashes=all_supplied_comparison_hashes,
    artifacts=complete_input_store,
)
package = build_table(
    captured, context=context, model_card=draft_card, artifacts=complete_store,
)
write_table(package, output_table_path)
```

These variables are externally supplied inputs, not newly defined schemas or review
issuance examples. A owns capture loading, draft creation, public commands and disk
layout. The B helper does not substitute for those APIs. A's received production
workflow and actual external declaration reviews are required for the remaining
joint public demonstration; this module alone does not complete that exit.
