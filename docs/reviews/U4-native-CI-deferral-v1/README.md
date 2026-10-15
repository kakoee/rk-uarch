# U4 native CI deferral — Javid instruction

Javid asked to postpone remote-server and GitHub compilation while Reza is unavailable,
and to progress with work that does not need those facilities. This record applies to
**native/Rust remote execution**, not all existing GitHub checks. Source baseline:
`09a3a27dcdf4501c7f6bf9fdfda4b08aa5297c38`.

## Effective action

- The live legacy `jobs.native` is explicitly skipped with `if: ${{ false }}`. It previously
  still ran on code pushes, independently of B's uninstalled replacement. No successful
  native check or qualification may be inferred from this skip or an overall green workflow.
- Private image publication, owner environment/secret setup, hosted-native activation and
  remote runner setup are deferred. Earlier scoped publication approval is preserved;
  it is not an instruction to execute during this deferral. No destination change to
  jjaffari was authorized by the preceding feasibility question.
- Python, contracts, licences/patches and other existing CI checks retain their conditions.
  The documentation-only classifier is unchanged. No running workflow is cancelled here.
- B's built image, local test/fault/replay evidence, exact pins and prepared access workflow
  are preserved. No image publication, credential or server operation was performed.

## Productive work that can continue

1. Coordinator prepares the already accepted exact M schema plus selected-policy installation
   and frozen-input package, with the required human installation/generation/adoption steps
   still separate. This needs neither a remote runner nor image publication.
2. Local independent K1 review can assess the actual code, tests, faults and deterministic
   results using the built environment. Author corrections and local reruns remain within
   the existing private K1 release. They do not supply hosted CI evidence.
3. Required M/K2/B fixture/profile identities and independent mathematical expectations can
   be prepared at their existing preparation boundaries. Human L1 work remains human work.

Installed U0011/U0023 gates are unchanged. K1's qualifying Linux CI is pending, not waived.
Public K2 implementation/execution, later models and sprint closure are not released by
this scheduling decision. If advancing a later stage requires changing an unmet prerequisite,
bring that concrete amendment to Javid; do not quietly treat local evidence as its substitute.

## Resume

On Javid's resumption instruction, B uses the preserved exact package and access receipts
(or a separately accepted runner arrangement), installs a fully resolved pinned native job,
restores its documentation-only guard, updates the corresponding workflow assertion and
executes the real required controls on the then-current source. No placeholder job or stale
K1 receipt counts as current verification. The one-line pause must not be removed merely
because a token or machine becomes available. No global CI disablement is proposed.

## Executed checks

36 workflow-scope, prompt-sync and numbered-patch checks passed; scoped Ruff and whitespace
checks passed. Parsed workflow comparison confirms only `jobs.native.if` changes semantically;
all other job definitions are identical to the source baseline. No runtime/native test,
hosted CI or full-suite pass is claimed for this scheduling change.

## Subsequent multi-sprint decision

Human-installed [U0024](../../decisions/U0024-temporary-local-verification-and-deferred-native-ci.md)
supersedes this note's restriction on development progression solely for missing remote
native CI. Current local checks and independent review may support interim development
within U0024's limits. The actual CI pause and final qualification debt remain in effect.
