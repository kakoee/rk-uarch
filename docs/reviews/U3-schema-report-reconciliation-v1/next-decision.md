# Proposed U3-RoPE-install-and-runtime-v1

**Pending Javid's approval.** This is a concrete next-step proposal, not an acceptance record.

1. Approve human installation and a local protected commit of the exact 17-path patch at
   `53435927497eb3e4552e32e2c5e887e0bcb05ddc`, file
   `docs/reviews/U3-RoPE-protected-patch-v1/protected.patch`, SHA256
   `8a02ed6cf56846c6f688d195b068aadd19bb2bab11fe751a8af36d8408e04169`.
   It adds the two contract modules, eleven schema mirrors, three test files and U0022's
   schema addendum. The agent prepares/verifies the narrow human installation command;
   the human runs it with normal hooks. Installation and commit do not authorize push.
2. After that installation, authorize A's tests-first implementation of the already accepted
   [design](../U3-RoPE-schema-v1/README.md), sections 2–5: additive v2 protocol/generator,
   strict prepared-input/job/result admission, explicit-coefficient preparation, RoPE counts
   and traffic, analytic v2, version dispatch and v2 capture. Proposed owned modules are
   workload/prepared_v2.py, workload/producer_v2.py, engines/protocol_v2.py,
   engines/analytic/rotary_v2.py, engines/analytic/dispatch.py and table/capture_v2.py,
   with corresponding owned generators, schema mirrors and tests. Preserve legacy module
   bytes and execution identity. No new semantics, automatic v1 upgrade, coefficient guessing,
   protected edits by agents, public v2 table/report attachment or B evidence eligibility.
   Any further protected-test change is proposed separately for human installation.
3. Keep ordinary local Git commits in A's existing independent clone. Reconcile source and
   interfaces before one combined freeze of the completed reviewed change. Do not publish
   known-stale support receipts. Human U0002 generation, candidate audit, exact adoption
   approval, protected adoption commit and a separately verified main push remain required.
   The initial schema installation will intentionally make strict support stale locally;
   no historical-mode substitution or support exclusion is approved. Avoid a separate oracle
   refresh for each unfinished local implementation checkpoint.

B's standalone-v1 correction can proceed independently under its existing authorization.
This proposal does not approve simulator selection, instrumentation, U0005/200-second timing,
performance claims, runner registration or nightly completion. The existing 40–64h A estimate
is a planning estimate; human/reviewer work and calendar waits remain separate.

Why a human step is required: CLAUDE.md's Workflow says, “Agents propose and stop on
contract/, tests/golden/expected/, CLAUDE.md, docs/decisions/.” The existing
scripts/hooks/human_owned.sh also requires the human-owned commit flag. This proposal
contains contract files and an ADR addendum; neither restriction is bypassed.
