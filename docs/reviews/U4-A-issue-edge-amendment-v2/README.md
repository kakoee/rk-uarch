# B-ISSUE-ORDER-01: revised, unapplied proposal

This revision preserves actual eligibility opportunities and corrects the independent
checker’s timestamp-wide ordering assumption. It responds to B review
`d4ef3bf00f53c693a9a8188e5edc368862e187f3`. The original proposal at `ddd299c`, B’s review,
all historical inputs and receipts remain unchanged. Only this review package is live;
all implementation changes remain unapplied outside private exports.

[manifest.json](manifest.json) pins three full replacement patches and all 22 exact
preimages/postimages. They apply to published main at d4ef3bf. The separate
[alternative delta](patches/alternative-delta-from-v1.patch) applies to the exact assembled
v1 proposal. These are alternative routes, never cumulative. Both routes were applied
and reverse-checked in fresh private exports and produced identical postimages.

| Replacement patch | Scope |
| --- | --- |
| [contract-and-export.patch](patches/contract-and-export.patch) | Full proposed ADR, carriers, schema, structural validation, tests and exporter, including the corrected opportunity law |
| [checker-and-identity.patch](patches/checker-and-identity.patch) | Full independent /3 checker and tests, with exact prospective CI identity overlay |
| [native.patch](patches/native.patch) | Full native proposal, actual transition witness, paired B fixtures and focused controls |

The narrow delta is useful for reviewing this correction. The full patches avoid a
partial installation that combines an old checker with new native observations.

The scheduler now records `reservation_opportunities` directly during reservation:

| Field | Meaning |
| --- | --- |
| `opportunity_ordinal` | Contiguous opportunity index starting at zero |
| `t_ps` | Actual scheduler time of the reservation pass |
| `event_cursor` | Number of endpoint events already emitted before that pass |
| `granted_request_ids` | Actual DMA reservations made at the opportunity, in grant order |

An opportunity occurs initially, then after terminal sequence completion changes
eligibility or releases credit. A phase-0 completion batch is drained before a single
opportunity. Each inline terminal completion creates a distinct next opportunity, even
at the same timestamp. Empty opportunities, including the final release, are explicit.
Nonterminal completions and pending-to-acquired conversion do not create opportunities.
The native runtime stores these transitions before grants; accounting projects the
stored records. It never reconstructs reservation order from alignment dispatch.

Ready-time/request-ID ordering applies among requests eligible at the same opportunity
on the same engine. Independent engines retain separate capacity pools; the serialized
witness uses the existing ready-time/engine-ID/request-ID order. A smaller request ID
that becomes ready later at the same timestamp cannot displace an earlier reservation.
Pending plus acquired capacity and strict-wait credit causes are unchanged. In
particular, equal dependency readiness and credit release remain dependency-only.

The independent checker reconstructs the exact opportunity boundaries from terminal
endpoint events. At every cursor it derives dependency completion from all predecessor
sequence terminals, and occupied credits from previous reservations whose request
terminals have not yet occurred. It then computes the complete earliest grant list
from the eligible set and available per-engine credits. Claimed grant order is compared
with that derived list. Readiness timestamps, claimed opportunity ordinals and later
alignment dispatch are insufficient on their own. Structural validation separately
checks required fields, cursor/time order, complete unique grants and reservation joins.

The exact two B raw inputs are preserved in [private-probes](private-probes), with their
original hashes. Four private executions used revised native source: two inputs in debug
and release. Both modes produce identical bytes for each input, and all four pass the
revised structural validator and independent checker.

| B case | Initial grant at time0/cursor0 | Later grant at60000 | Completion times |
| --- | --- | --- | --- |
| r00 depends on inline unicast | r01.00 | r00.00 | r01=60000, r00=120000 |
| Paired control: r01 depends on inline unicast | r00.00 | r01.00 | r00=60000, r01=120000 |

Both job readiness timestamps are0. Each run has opportunity times
`[0, 0, 26667, 60000, 120000]`; the second opportunity is cursor2 after the inline unicast
and grants nothing because capacity remains occupied. The barrier completion creates
the26667 opportunity. Removing only the new witness and recomputing result_hash restores
B’s entire canonical prior result for all four executions, not merely the duration.
[evidence/native/evidence/old-result-equivalence.json](evidence/native/evidence/old-result-equivalence.json)
binds that comparison to the original B outputs.

The [consistent forgery](private-probes/consistent-ineligible-first.json) starts from the
paired output, rebinds it to B’s failing graph and repairs dependency causes and all
identity hashes. Its reservation times, complete grant lists, queues, clocks, capacity,
job/allocation endpoints and event joins remain consistent. It passes structural
validation. The independent checker rejects it specifically at
`opportunity eligible grants / ready tie`: r00 was not eligible at the initial cursor.
Removing only the dependency-completion predicate permits the forgery; exact restoration
rejects it again. The paired valid control passes throughout. See
[evidence/consumers/checker-fault.json](evidence/consumers/checker-fault.json).

Focused evidence observed for this correction:

- Python tests first:11 behavioral failures and9 existing passes before the new witness
  and checker implementation. Final affected selection:43 passes, including explicit
  unavailable-credit, same-opportunity ties, phase-0 coalescing, inline opportunities,
  empty/missing/shifted opportunities, independent pools and66 same-edge reservations.
- Native tests first:the two exact B mapped regressions fail for missing witness rows.
  Final selection:12 controls pass in debug and release, with one explicit file exporter
  ignored except when invoked for the four focused runs. The selection retains the
  prior strict-wait, capacity,33-issue and historical-version controls. A typed barrier
  control discriminates phase-0 coalescing from separate inline opportunities; it is
  labeled synthetic and is not claimed as mapped admission.
- Two native faults fail and exact restoration passes after explicit clean recompilation:
  a cursor shifted toward later dispatch, and omission of terminal eligibility changes.
- Mapped schema and all three native snapshot modes pass; Ruff passes for six changed
  proposal files and strict mypy for four source files. The prospective CI overlay and
  historical selection guard pass. Both patch routes match all22 frozen postimages.
- The packaged read-only consumer replay verifies all22 postimages before importing
  the private validators/checker, then accepts the four controls and refuses the forgery.

[evidence/python-checks/receipts.json](evidence/python-checks/receipts.json),
[evidence/native/native-report.md](evidence/native/native-report.md) and their raw logs
separate new checks, setup failures and inherited evidence. The private unit executable
hashes are debug `8df70d8cf6f5c4d3e108a9f90e82052bbce0e4650e2a2d9da389e11d2fd9c43d`
and release `996d173bb16c7ccf86578df743322c522f6d5661e178e7c70ce40fafda697827`.
These identify private test executables, not production builds, authority or independent
reproducibility. Accepted Rust image/tools, lock/features and offline cache were used;
all1719 cache files were verified. Python used the existing Lane A environment. No
new dependency was introduced.

B’s twelve-probe final-source campaign, mechanism literals, prior faults and old
construction/read-audit evidence are inherited from d4ef3bf and earlier records. They
were not rerun or relabeled as revised-source executions. Earlier draft /3 outputs lack
the required new witness and are not retrofitted or silently accepted under this revision.
Installed model1 / observations1 and2 are unchanged. The still-uninstalled model2 /3
proposal is revised in place, with exact new prospective source/schema/checker bindings.
The original installation binding and106-case selection remain immutable; only the
separate proposed overlay changes its exact postimages. All56 selected U0002 support
files remain byte-identical; dependency acceptance is neither reopened nor expanded.

For read-only replay after applying one patch route in a disposable export, use the
existing pinned environment to run:

```text
python docs/reviews/U4-A-issue-edge-amendment-v2/verify_consumers.py /tmp/PRIVATE-EXPORT
```

This verifies recorded outputs; it does not execute native jobs. Do not apply these
patches to protected live files as part of review.

[peer-reply.md](peer-reply.md) delivers the exact corrected checker, semantic law,
identities and discriminating evidence to B through the published peer workflow used
by d4ef3bf. B confirmation of the corrected postimages is pending; this package does not
claim that response or approval. Exact human semantic approval/protected installation,
future runtime/profile/selector/HostRecord authority and public negative transport remain
separate. No public component job, broad campaign or trace rebuild ran. Prior trace gaps,
human L1 workings, public first use, U-P11b acceptance and U4/G3a/performance closure remain
open under the previous package’s scope.
