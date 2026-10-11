# U3 combined freeze coordinator review — 2026-10-11

**Ready for Javid's exact freeze and two-process generation confirmation.**
Reviewed B proposal commit `70adf0988b218aed895fcf5d2d8b039ca2ba0566`, containing only
its nine-file proposal package. Primary main was fast-forwarded normally to that commit.
No A source history was imported into published main. This is coordinator review, not
independent U-REVIEW, artifact adoption, runtime publication or sprint closure.

## Reviewed identities

- Source: A local `187fe3b035bee9cbeae13b03c8b4ac6ef0ee276f`, tree
  `fe10c7d4b08a6910f165da9b92f8e13a2a37c107`.
- Input SHA256SUMS: `27c6238d42e57dc4f2b1baf0c8846c11f1eec2968176dcefcdc463beb64bc80f`.
- Upstream: pristine `1e5706e0ebfcc67c1a7333079a35b75f693e9963` in the existing pinned checkout.
- Current adopted manifest: `20eee19b0e864ad07a7b122da7544e385116fdd50d279e1fac1bfbbf03a697ad`.
- Output: A's presently absent, ignored `tables/U3-rope-generation-v1/`.

## Coordinator checks actually executed

The commit-pinned preflight ran successfully **from primary**, using A's isolated interpreter
with bytecode writes disabled and explicit A imports. [Receipt](preflight.json) records
source/ancestry/clean state, hooks, input digest, matrix and exact source/oracle environments.
Both existing environments pass locked offline checks without installation. CPython is
3.12.14; uv is 0.12.9. This is local software readiness, not runner/nightly readiness.

A second pure staging independently reproduced the 23 input payload files plus SHA256SUMS.
The old/new inventory is identical; only `support-files.json` and `SHA256SUMS` differ.
Support grows **87 to 97**: exactly the ten expected additive carrier/runtime Python files,
with no removed or modified old support entries. All 36 execution dependencies belong to
the complete support set. [Audit](input-audit.json) records this comparison and four
read-only negative controls: wrong proposal commit, wrong source commit, wrong input digest
and ambient PARAMS override all refuse; the source control passes after restoration.

Both helper files were parsed, and scoped Ruff passed. The generation helper was read in full
but **never executed**. Its generator interfaces and exact stdout expectations match the
unchanged implementation. It verifies its package bytes against the approved proposal commit,
checks before/between/after source/input/environment identities, launches two isolated vendor
processes against one separate candidate, requires created then verified-identical, verifies
candidate support/current generator identity and retains logs plus the manifest digest.
It does not adopt, activate tests, commit, push, install dependencies or configure a runner.
No human flag was set by the coordinator.

The B audit/placement plan correctly preserves the 1,008 nominal rows, seven precision
combinations and four real precision refusals, and requires complete old/new semantic and
byte comparison after generation. Equality is expected, not yet observed. The pinned oracle
has no new physical RoPE channel; this refresh cannot establish physical-v2 parity. B's
existing reports retain their v1 implementation bindings and limitations.

No runtime, full-suite, full matrix or oracle execution was repeated here. The preceding
[coordinator runtime checks](../U3-RoPE-runtime-reconciliation-v1/README.md) remain separate
executed evidence. A's protected-test patch and all adoption-pin changes remain unapplied;
the two currentness gates remain open. A's reviewed HEAD/index/tracked files remain unchanged.

## Decision and sequence

[U3-combined-freeze-v1](next-decision.md) is ready for Javid's confirmation. It selects these
exact inputs and permits the human's two-run generation only. Under U0002, “Only a human
runs `make vendor-rk`”; its lifecycle also requires explicit approval of the complete candidate
before adoption. The runtime authorization already anticipated this lifecycle, but did not
select the present digest or grant approval to an as-yet nonexistent candidate.

After confirmation, use the commit-pinned command in the decision. Keep A stopped on the
reviewed source through both runs. Return the final digest and receipts; the coordinator
then audits the complete candidate before a separate adoption decision and human protected
test activation. Final integrated checks and source publication remain later steps.
The existing helper refuses any occupied output root: if a run stops partway, return its
error and retained receipts for reconciliation rather than deleting or overwriting them.
