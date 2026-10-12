# Proposed local checkpoint and protected-test activation decisions

These are two distinct decisions and two separate human local commits. They may be approved
in one reply. Neither permits a push or sprint closure.

## 1. U3-adoption-local-checkpoint-v1

Approve staging and committing only the seven already adopted paths listed with their
exact SHA256 values in [checkpoint-plan.json](checkpoint-plan.json).

- Repository/branch: `rk-uarch-u3-a`, local `main`.
- Parent: `187fe3b035bee9cbeae13b03c8b4ac6ef0ee276f`.
- Message: `chore(u3): adopt reviewed RoPE support snapshot`.
- Candidate manifest: `1873760cdbc06d9f1508ac4e515dfc0acefd7b2577a230047a38d3038098105a`.
- Scope: three artifact metadata paths, three current-binding tests and the new U3 human
  administrative adoption record. All 48 artifact members have been verified together.

Placement is already approved and verified. This decision makes those exact changes a local
Git checkpoint. It includes no activation patch and no push.

## 2. U3-rotary-test-activation-v1

Approve human installation, staging and a separate local commit of A's exact one-file patch:

- File: `contract/tests/test_rotary_v2_runtime_pending.py`.
- Patch: `docs/reviews/U3-RoPE-runtime-v1/protected-tests.patch` at reviewed A `187fe3b`.
- Patch SHA256: `4280f13077b703283d3e8237011f18bd6641ee9c4580337d8b822d5193613e26`.
- Before SHA256: `a5cb45b6b4fbecdda19fa3213fd2dca411a8e3c15b10eb919289ab86cfcd4d27`.
- After SHA256: `addc0149ec2a1a8f106f94210030d259116ae7e10dd48ccbbc17b19ade84d0db`.
- Parent: the verified adoption checkpoint from decision 1, with a clean index/worktree.
- Message: `test(contract): activate approved rotary v2 admission checks`.

The patch removes 28 pending skips, adjusts the pending prose and renames the test function.
It changes no counterexample fixtures, assertions, runtime code, thresholds or support inputs.
Both rotary contract modules passed 102/102 on the exact scratch placement with this patch.
This activates existing admission checks; it makes no new hardware or G2 validation claim.

Normal human-owned hooks remain active. A guarded human helper will execute the approved
steps separately, verify exact parents/content/scopes and return both commit receipts. It
will neither push nor perform unrelated cleanup. Final integrated checks and a separate
publication decision follow. Both decisions remain pending until Javid approves them.
