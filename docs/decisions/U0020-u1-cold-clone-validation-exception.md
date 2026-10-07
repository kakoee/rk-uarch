# U0020 — U1 cold-clone validation-plan exception

**Status:** accepted by Javid (@jjaffari); records his existing authorization, not a new
approval request. Recorded 2026-10-07. No Reza approval is claimed.

**Scope:** U1 publication `44559fb1672e4d3468b4b6fc930cfdf4b4c1e99e` only.
U0020 was unused in the repository when this record was prepared; reserved U0001–U0018
and accepted U0019 retain their assignments. The closeout instruction explicitly adds
this ADR to the standing documentation prompt's otherwise no-ADR scope.

## Context and authorization

The [execution plan](../execution-plan.md) calls for the sprint's joint exit criterion
on the Linux box from a cold clone. The manual validation instead used a fresh GitHub
clone on ElfinKidsLaptop's Ubuntu/WSL2 environment, supplemented by hosted Ubuntu CI
on the identical published commit. The separate/designated Linux-box condition was
not met. Javid explicitly authorized this U1-only replacement, quoted verbatim in the
[preserved report](../reviews/U1-cold-clone-evidence/report.txt) and
[authorization text](../reviews/U1-cold-clone-evidence/user-approved-exception.txt):

> For U1, I approve ElfinKidsLaptop’s Ubuntu/WSL2 environment for the manual
> cold-clone check, supplemented by hosted Ubuntu CI on the same commit.
>
> Record this as an explicit U1 validation-plan exception, not as validation
> on a separate Linux machine. Proceed with the fresh GitHub clone and checks
> already specified. Preserve the exact host/kernel details.
>
> This does not designate WSL2 as the later simulator-performance host or
> waive future runner/hardware requirements.

## Decision

For this U1 revision only, accept the new ElfinKidsLaptop Ubuntu/WSL2 cold-clone
validation plus [same-commit hosted Ubuntu CI](https://github.com/kakoee/rk-uarch/actions/runs/37585143201)
in place of the separate Linux-box check. This replaces the host condition, not the
required checks, artifact identities or final human G1 decision.

Manual host: Ubuntu 24.04.4 LTS, x86_64, hostname ElfinKidsLaptop. Exact `uname -a`:

```text
Linux ElfinKidsLaptop 6.6.87.2-microsoft-standard-WSL2 #1 SMP PREEMPT_DYNAMIC Thu Jun 5 18:30:46 UTC 2025 x86_64 x86_64 x86_64 GNU/Linux
```

The fresh detached checkout, new virtual environment/cache, locked Python 3.12.14
validation, clean initial/final Git state and hosted job evidence are retained under
[U1-cold-clone-evidence](../reviews/U1-cold-clone-evidence/README.md).
The [closeout](../reviews/U1-closeout.md) distinguishes actual checks from CI conditional
no-ops and records tool versions and environment limits.

## Consequences and exclusions

U1's publication and required validation evidence are complete under this exception.
The original separate-machine requirement is not represented as satisfied. Javid also
explicitly accepted U0020 with his final G1 approval and U1 closeout acceptance on
2026-10-07; see the [final authorization](../reviews/U1-closeout.md#final-human-approval).
Closeout commit, push and `u01-end` tagging remain separate pending steps.

This does not amend existing ADR policies, waive future runner or hardware requirements,
or designate WSL2 as a simulator-performance host. U3 must still register the `uarch`
self-hosted runner, re-enable the nightly schedule and demonstrate a green manual run
before U-P5. Later engine, golden, determinism, performance and silicon gates retain
their own requirements. Contract/harness checks do not establish workload parity,
hardware accuracy or simulator performance. No other sprint inherits this exception.
