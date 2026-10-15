# Two independent U4 K2 decisions

**Status: proposed; neither approved by this record.** Exact source base:
`0718955cc0656e5bac4688d4696abbd547cb4186`.

## 1. U4-K2-semantic-candidate-v1

Recommend accepting the [ten-path candidate](candidate.json) and
[combined patch](combined.proposed.patch), SHA256
`775e93b92931ff48b3e5bf9a0de98c7b6d38026f1ff25f9b83db3d56a6f6e7cf`,
for preparation of guarded human installation. It contains A's exact semantic patch,
B's notification-order guard and the coordinator's two permanent regression controls.

The semantic choices are:

- Raw clock alignment is separately observed: K06-02 raw1667 ps and owned zero-job835 ps
  are distinct checks. Diagnostic raw overflow does not excuse positive-cycle overflow.
- Fixed-delay waiting/service observations have no invented physical clock domain.
- Critical intervals have positive length; zero-duration jobs remain in immediate causal
  links. All-zero elapsed time has an empty critical interval list.
- Completion phase0 precedes release/readiness phase1 and grants phase2; phase1 eligibility
  is batched canonically. Dependency notifications require an earlier available completion,
  including inline zero-duration completions.
- The explicit private Wheel exception is scoped as in the proposed U-P11a/U0011 text;
  private controls confer no public execution credit.

B's [prospective coverage mapping](../U4-B-A-addendum-reconciliation-v1/coverage-delta.json)
retains the original113 IDs,100 K07 cases,100 private Wheel schedules and17 witnesses and
separately lists new obligations. Approval selects this prospective mapping; it does not
mint actual revised profile/registry bytes or rewrite the historical corpus. Exact finite
inputs must still be prepared and bound before public execution.

This decision is semantic/protected-patch acceptance only. The human installation helper
and its exact selection must be prepared before applying the protected files. Installation,
commit and push are distinct actions. No dependency fetching, native implementation,
construction-test execution or final HostRecord authority follows from decision1.

## 2. U4-K2-C1-resolution-v1

Recommend authorizing **one disposable dependency-resolution/fetch experiment**, using
A's exact [construction plan](../U4-A-K2-semantic-construction-v1/construction-plan.json),
SHA256 `4a5cbb16f5f249234d8ffc0a0e01476c89f4769a57ab96f422ff3c10093eebd5`,
and [instructions](../U4-A-K2-semantic-construction-v1/construction.md), as clarified by
[B's reviewed execution order](../U4-B-A-addendum-reconciliation-v1/records-and-C1.md).
Use the stated source base in a private export. The accepted initial Cargo.lock remains
`3df872c1e8c445b179dd8162430a5265fa770a62bcfa009009dae49d878bf084`.

Scope: exact accepted local tool image; private CARGO_HOME/CARGO_TARGET_DIR; the proposed
serde_json arbitrary_precision feature and sha2=0.10.9 std+force-soft addition; the exact
eight new package/version/checksum allowlist. Preserve all existing package identities.
Registry metadata/archive access only to index.crates.io and static.crates.io/crates.
Inspect the resolved full lock before archive-fetching metadata operations; stop on drift
or unsatisfiable constraints. Capture full and target graphs, features, actual archive
licences/checksums, offline repeats and command/network/tool/preservation receipts.

No live manifest/lock/cache edit, engine or probe compilation/execution, package installation,
new tools, image build/distribution, credentials, server work or infrastructure is authorized.
The resulting lock/cache is an unaccepted candidate. Return actual evidence before deciding
its acceptance and C2 standalone offline probes. Public K2 implementation and final binary/
host first-use authority remain separate. Existing tool/licence approvals are not reopened.

**Suggested reply:** “Approve both U4-K2-semantic-candidate-v1 and
U4-K2-C1-resolution-v1”, or approve either decision individually.

Why approval is needed: [CLAUDE.md](../../../CLAUDE.md) says “Agents propose and stop on
contract/, tests/golden/expected/, CLAUDE.md, docs/decisions/” and “Don't add dependencies
beyond pyproject.toml / native/Cargo.toml without asking.” Decision1 covers protected
contract/ADR changes; decision2 is the separately scoped experiment with new Rust dependency
candidates. No new permission is requested for already accepted K1 tools or ordinary docs.
