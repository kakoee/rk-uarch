# U4-M-policy-source-install-v1 — exact source-only installation release

**Status: proposed; awaiting Javid's installation authorization.** Accepted M semantics,
trust-bootstrap design, selected U0002 policy and tool/licence choices are not reopened.

## Decision requested

Authorize Javid's guarded local installation and one source commit of the exact 32 paths
in [B's selection](../U4-M-policy-installation-readiness-v1/selection.json), using the
unchanged reviewed helper at `56d7ddcb4314ec4ecf7f7631c0b2edbe7d17a4e2`.
Selection SHA256: `04296d55479ce188e3169379f104a24fabf35021246cb6d542cccfb26a43d224`.

This installs the M input schemas/prototype checks (26 added contract paths) and the selected
artifact-dependency policy (six paths: three modifications, three additions). It installs
neither a public native executor nor a mapped workload runtime. The narrow policy follows
reviewed actual dependencies instead of binding every unrelated production Python file;
it still refuses changed dependencies and untrusted import shadows.

Exact original patches:

- M: `d392b24304a5f63fe69679ce991c5dbf2f742e95fee867a82dec2b0eef3a25e3`.
- Policy: `c238574b284ebecb6f0f1253922ce01af87259f0187aad38bcda628757e8fe6b`.

## Concrete placement and boundaries

Use the existing `rk-uarch-u4-a` clone on main after normal fast-forward to the coordinator's
subsequent actual authorization record. It was clean at `892b9ee` when inspected; recheck at
execution and reserve it from concurrent author writes during migration. The coordinator
checkout has pre-existing untracked U3 reviewer files; do not delete, stage or hide those to
satisfy the installer. B's clone remains available for normal preparation work.

After approval, the coordinator commits only the exact authorization JSON required by
[B's installation specification](../U4-M-policy-installation-readiness-v1/installation.md),
binding the helper commit, selection hash and actual parent. That record is then the pinned
HEAD for the human's command. No fabricated authorization or placeholder command is supplied
here. The human uses the existing reviewed CPython environment and normal ownership hooks.

The source commit **S stays local**: the existing artifact becomes stale under the installed
policy and strict checks must refuse it. Do not push S alone, bypass strict checks or relabel
the expected refusal as migration success. The old compatible source/artifact tip remains
published while the coordinator prepares the next exact freeze/lifecycle action.

This release does not authorize input staging/freezing, oracle generation, artifact adoption,
current-test-binding changes, K2 implementation, image publication, server/runner work or
sprint closure. Those remain at their concrete first-use boundaries. K1's fresh independent
review proceeds separately on its pinned published source; installation does not grant a
review verdict or K1 acceptance.

## Why a separate human action is required

The already installed [release](../U4-M-and-K1-release-v1/acceptance.md) accepted D1 but
explicitly released only “preparation of the separate M/selected-policy installation and
freeze.” It excluded M source installation and generation/adoption. [CLAUDE.md](../../../CLAUDE.md)
says “Agents propose and stop” on contract paths. This request is for that next concrete
installation step, not a repeated design/policy vote.
