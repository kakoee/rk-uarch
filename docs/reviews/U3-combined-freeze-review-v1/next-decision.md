# U3-combined-freeze-v1 — proposed human decision

Approve the exact source/input freeze in B proposal
`70adf0988b218aed895fcf5d2d8b039ca2ba0566` and personally run its two-process generation:

- A source commit `187fe3b035bee9cbeae13b03c8b4ac6ef0ee276f`, tree
  `fe10c7d4b08a6910f165da9b92f8e13a2a37c107`.
- Input digest `27c6238d42e57dc4f2b1baf0c8846c11f1eec2968176dcefcdc463beb64bc80f`.
- Pinned upstream `1e5706e0ebfcc67c1a7333079a35b75f693e9963`, existing checked environments.
- New output only under `rk-uarch-u3-a/tables/U3-rope-generation-v1/`.

This confirms generation of a review candidate. Adoption, protected-test activation,
commit/push of source-bound work, runner/nightly and closure remain separate. No numerical,
precision, scope or tolerance change is approved. The prior snapshot remains canonical until
an exact complete candidate has been audited and separately approved.

The [coordinator review](README.md) reproduced the digest and read-only preflight. The
[proposal and audit/placement plan](../U3-combined-freeze-proposal-v1/README.md) are unchanged.
After Javid confirms this named decision, Javid may run this exact command from his shell:

```sh
env -u PYTHONPATH -u MYPYPATH -u VIRTUAL_ENV -u PARAMS UARCH_HUMAN=1 GIT_OPTIONAL_LOCKS=0 \
  /home/jjaff/AI-infra-simulation/rk-uarch-u3-a/.venv/bin/python -I -B \
  /home/jjaff/AI-infra-simulation/rk-uarch/docs/reviews/U3-combined-freeze-proposal-v1/human_generate.py \
  --approved-proposal 70adf0988b218aed895fcf5d2d8b039ca2ba0566
```

The helper prints its final candidate manifest digest after both generation processes finish.
Logs and the machine-readable generation receipt remain in
`rk-uarch-u3-a/tables/U3-rope-generation-v1/receipts/`. Return the final output to the
coordinator; the original `created` and `verified-identical` lines are retained in
`run-1.stdout` and `run-2.stdout`. Stop before adoption. If a guard or process fails, return
that output with the retained receipts; do not manually resume, overwrite or delete them.

Approval is still pending when this proposal is published. No execution is claimed.
