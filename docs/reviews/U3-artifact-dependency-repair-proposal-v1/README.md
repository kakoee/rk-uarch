# Separate proposal: audit and narrow artifact dependencies

For Javid and the coordinator, 2026-10-12. This is a bounded **design/audit task proposal**,
not an exact repaired inventory or permission to change U0002/enforcement. It implements
the follow-up separation recommended for PF-05. The companion plan amendment leaves the
current lifecycle fully operative.

## Problem and preferred direction

`scripts/u2_inputs.py::support_files()` binds every Python file under `src/rkuarch`,
`contract/uarch_contract` and `scripts`, plus explicit inputs. Strict currentness rejects
unrelated additions/edits along with generator-relevant changes. This is broader than an
established generator dependency closure. It is not literally every Python file in Git.

Prefer an explicit, reviewed generator/support inventory with defensible transitive input
coverage. Do not choose the inventory by whether current outputs happen to change. Do not
replace source provenance with equality on one fixture matrix. Dynamic imports, imported
package initialization, configuration/data files, serialization, locks and environment
dependencies need examination, not just an AST import graph.

## Bounded task for a later authorized worker

Owner: B for scripts/enforcement, with A consultation on producer/analytic dependencies.
Public carriers and ADRs remain human-owned. Pin the actual starting commit and current
adopted manifest; do not assume today's identities are current after subsequent work.

1. Trace the exact two-process generation path, input preparation, source capture and
   strict consumption checks. Inventory dependencies by purpose, including generated-data
   behavior, provenance metadata, verification and packaging. Mark unresolved dynamic or
   environmental edges explicitly. Runtime import traces supplement, not replace, reasoning
   about unexecuted branches.
2. Produce proposed retained/removed/additional entries with a rationale for each grouping.
   Distinguish immutable generation provenance from the consumer's current compatibility
   requirement. No blanket exclusion of report/CLI/native files without evidence of their
   relationship to generation and verification.
3. Write an exact unapplied enforcement/test patch and prospective ADR amendment. Specify
   how newly introduced dependencies are discovered or refused; an allowlist that silently
   misses new imports is insufficient. Prefer a small maintainable mechanism over a second
   source/version-control system.
4. Demonstrate, in a private export without oracle generation/adoption:
   - current adopted artifacts retain integrity;
   - a relevant generator/formula/input/serializer edit invalidates the appropriate check;
   - a newly introduced relevant dependency cannot evade inventory validation;
   - audited unrelated Python additions/edits no longer force artifact refresh;
   - pin, input, lock/environment, inventory and content substitution controls still refuse;
   - producer-disabled replay and ordinary committed-fixture consumption remain supported.
   Separate test setup failure from expected refusal and include valid controls. If a
   migration is necessary before some positive checks can pass, state that rather than
   changing artifact metadata or generating a candidate without authorization.
5. Propose exact migration placement, old/new metadata interpretation, historical replay,
   rollback and human generation/adoption requirements. Changed enforcement code is itself
   currently bound; reconcile that transition under the existing human policy.

Deliver one reviewable proposal with the dependency rationale, exact patch, test evidence,
known blind spots and an engineering estimate derived from the actual work. No vast
checkpoint copies or whole-repository manifests. Stop for coordinator review and Javid's
exact policy/migration decision.

## Exclusions and decision boundary

No live U0002, production, schema, workflow, support-inventory or generated-artifact edits.
No CI generation, upstream fetch, credentials, tool installation or human impersonation.
No source-currentness waiver while this task is pending. No automatic acceptance based
only on unchanged numeric output. No claim here that the dependency closure has already
been traced or the repair tested.

The plan amendment can proceed independently of this repair. Native work must either
follow the still-current lifecycle or wait for the separately approved repair where its
changes touch bound inputs. That remaining operational cost is explicit, not hidden.
