# B dependency-audit correction: public loader and legacy dispatch

Proposal follow-up to [coordinator B-C1/B-C2](../U3-design-audit-reconciliation-v1/README.md).
No live repair, policy acceptance, artifact generation/adoption or gate verdict.
Started clean at `1ad61f6`; integrated `8867c0c`, then A's `c17cb9c`/`5c81915`
by normal fast-forward. Existing U0002 enforcement and historical reports remain intact.

## Exact correction and bindings

The [revised unapplied patch](../U3-B-artifact-dependency-audit-v1/repair.patch) changes
**only its proposed tests**. Its loader and support-helper implementation bytes are
unchanged. SHA256:
`97d0ec302606838a7055ec3d43ce1d3b759e8e015ecb796eed154ce4b0915e55`.
The earlier patch and 30-test receipts remain historical at `a602683`/`1ad61f6`, with
SHA256 `bb15bd236938c659b3c07b8be03121aaa5f41ee339560ba150a7cb4cec8391f8`.
Old [evidence](../U3-B-artifact-dependency-audit-v1/evidence.json) and the 97→52
[support delta](../U3-B-artifact-dependency-audit-v1/support-delta.json) are unchanged.
This correction does not accept that inventory or project M's future inventory.
[New evidence](evidence.json) binds the export, exact patch, commands and outcomes.

**B-C1.** Durable tests call public `load_inputs`, with copied typed input carriers and
explicitly synthetic support metadata/manifests rehashed after substitutions. No
GENERATOR metadata is created or modified. Fixtures deny `prepare_inputs`, `run_oracle`
and `collect_snapshot`. A populated valid new-policy control passes. Four attacks pass
integrity/typed loading with `check_support=False` but must fail strict loading:

| Attack | Exact expected refusal |
| --- | --- |
| Change bound derive formula 2→3 | `input support bytes changed: src/rkuarch/hw/derive.py` |
| Remove derive inventory entry | `input support inventory changed` |
| Substitute derive digest | `input support bytes changed: src/rkuarch/hw/derive.py` |
| Add a local dependency imported by derive | `input support inventory changed` |

Unknown, empty and substituted policies refuse `unrecognized input support policy`
with either strict or integrity-only loading. Legacy dispatch uses a synthetic complete
old-rule inventory without a policy marker: valid loading passes; changed bound bytes,
omitted inventory and a newly added Python file refuse their exact old-rule diagnostics.
A rejecting new-helper sentinel ensures the legacy branch never calls the new verifier.
All source faults are restored in `finally` and exist only in the private export.

**B-C2.** Fixed historical integrity/currentness now uses the existing authenticated
20-file `tests/fixtures/u2_b/historical-u1` fixture, pinned to manifest `b3a575d…` in the
existing identity validator. Its manifest, recorded generator and snapshot inputs pass;
strict library validation refuses the obsolete generator fingerprint. This case never
uses the mutable `ui.ADOPTED` path. Unversioned U2 loader dispatch is independently covered
by the synthetic controls above, so moving the pinned historical test does not drop it.

A separate current-adoption test validates integrity and recorded inputs first. It
explicitly skips the **real new-policy positive** until an actual policy-marked adoption
exists; when present, it calls `check_generator(current=True)` and requires success,
without catching incompatibility. Thus an approved future adoption is not required to
fail. Existing library/direct/module entry controls retain strict currentness behavior.
Synthetic loader success does not satisfy this real-adoption gate or prove provenance.

## Execution and discrimination

Executed only in a private `git archive` export of `8867c0c` with the patch applied,
except the explicitly live strict check and unapplied patch check. Used the existing B
interpreter, no install; ambient `PYTHONPATH` and `MYPYPATH` removed for every test/static
command. Pytest's repository configuration selects export sources. Import-linter resolves
the existing editable B src/contract roots; every Python subject was independently checked
byte-identical to the export (the proposed changes are in scripts/tests).

| Run | Result |
| --- | --- |
| Original tests / only loader verification call removed | 30 passed / 30 passed: blind spot reproduced |
| Corrected tests, same exact loader-call removal | **4 failed, 40 passed, 1 skipped**; four attacks accepted, assertions fail `DID NOT RAISE` |
| Exact loader bytes restored | **44 passed, 1 skipped** |
| Corrected tests plus vendor library/CLI-entry regressions | **53 passed, 1 skipped** |
| Existing synthetic integrity/environment refusal selection | **14 passed, 36 deselected** |
| CI-form Ruff / mypy production+scripts / mypy contract tests / imports | passed / 79 files / 31 files / 2 kept, 0 broken |
| Live strict vendor / patched-export strict vendor | passed / expected `input support inventory changed` refusal |

The one skip is the real new-policy adoption positive, not a synthetic success. The 36
cases were excluded by the named bounded regression selection. A new-test E501 was fixed
by wrapping one line before final Ruff; tests then reran with final bytes. The original
helper-only fault receipts remain historical, not credited for loader discrimination.
No full suite, hosted CI, native execution, oracle generation, adoption, corpus/report
regeneration or nightly was run. Existing U2 adoption is complete; only a prospective
new-policy migration remains pending. Strict refusal in patched scratch is expected and
must not become the permanent expectation for the current artifact.

## Reconciliation with A's received M note

Read A's [concrete proposed relationships](../U3-native-stage-design-v2/interface.md#proposed-m-dependencies-for-bs-audit)
at `c17cb9cfb56c8c08db2f2a1d4501bcf5360939eb`, and inspected current initializers and
`u2_inputs → hw.export → hw.derive → engines.protocol`. B's classification is:

| A proposal | B support consequence under the still-unaccepted repair |
| --- | --- |
| Direct caller import of additive `mapped.py` / `protocol_mapped.py` | No reverse edge from importing an already retained carrier; outside only while no generation/verification root reaches it |
| Root re-export, shared-carrier change or retained protocol/derive import | Retain the entire changed file and all new transitive imports, including `rotary_v2.py` if reached; local/conditional/TYPE_CHECKING imports count |
| Dedicated mapped generator, producer/mapper or native parser | Follow actual incoming edges and initializers; no blanket folder exemption or zero-refresh promise |
| Mapped schemas, fixtures, bundles, assumptions and hardware/model/coefficient reads | Classify the actual reader; reached staging/verification reads require reviewed explicit data binding and missing/changed/substituted-data controls |
| Add files to existing a2-export/model-shape/provenance families | Existing family enumeration already changes inventory; calling them mapped fixtures does not exempt them |
| New native build/identity/environment inputs | Audit explicit reads/lock dependencies separately; Python AST reachability is not proof of complete runtime dependencies |

A's note resolves the requested design consultation, not the implementation consultation.
It identifies no installed new edge and no basis for changing the baseline inventory.
Mapped serialization and component oracle projection remain distinct functions, with
possible shared dependencies. Dynamic registration, hidden data/config inputs and static
walk limitations still require review. The new public-loader tests exercise the generic
new-edge fault, **not an unimplemented mapped interface**. At the exact M patch, A supplies
all import/initializer/data/environment edges; B recomputes the actual closure and adds
public-loader relevant/unrelated/data controls against those concrete changes.

## Remaining decisions and next steps

1. Coordinator reconciles B-C1/B-C2 and A's corrected aggregate-only clock scope; no
   author-independent review or acceptance is claimed. Historical 22/24 and all skips stay.
2. Separate review/Javid decision on exact repair policy and migration before protected M
   installation. If not ready, explicitly retain U0002 and budget source-bound cycles.
3. Obtain the exact M patch/read inventory for the conditional checks above; no speculative
   exclusion or carrier installation follows from this note.
4. If separately authorized later: committed source freeze, human two-process generation,
   complete candidate currentness, 1008-row/four-refusal query/count/duration/null/attribution
   comparison, full matrix and tamper checks, explicit complete adoption and protected-test
   activation. Re-run the real new-policy positive and integrated CI/full suite at that
   checkpoint, following the existing [migration plan](../U3-B-artifact-dependency-audit-v1/migration.md).

Stop for coordinator reconciliation. No live source or protected file changes accompany
this proposal. Commit IDs and final worktree status are returned with the publication.
