# U4-K1-reviewed-installation-v1

**Proposed; no K1 installation yet.** Stage 3 accepted the exact twelve-path proposal, not
its installation or K2 release. The [read-only preflight](preflight.json) confirms both
patches apply to published M/PUB-C1 main `34de1d70ed9f19641b5e984d7e153eedb72af95d`;
all twelve current paths are unchanged from the original K1 review base.

Authorize the following bounded next step:

1. Install A's primary patch followed by B's exact guard patch from
   `docs/reviews/U4-A-K1-stage2-v1/`. Require SHA256 values
   `9897cb1407d26412bcea76e8e8a5a353c508b4d0ce5ca236efa8fb6b66cabfad` and
   `7bf806d04280f0ac66e37bfe0d292207e9a17b6e615b952a868ccb4e8afcc57e`, respectively.
   Require exactly the twelve postimages in preflight.json. Retain A/B ownership in the
   receipt; the implementation and guard must travel together.
2. Create a normal local commit of exactly those twelve paths, with normal hooks and no
   human-owned override. Proposed message: `fix(native): enforce reviewed K1 ownership and event ordering`.
   No contract, policy, artifact, toolchain, historical 0001 patch or accepted licence-set change.
3. On that real installed commit, run B's accepted-image post-install procedure, including
   genuine Cargo metadata, both 28-test modes, six replays, explicit metadata-fed Python
   linkage checks, source isolation and applicable fault/restoration controls. Use only the
   existing accepted image offline. Keep all failures and actual source identities visible.
4. After checks pass, publish with a separate normal push, preserving peer history. B can
   prepare the new inventory, replay binding and fault anchors against that installed source.
   Return the concrete inventory candidate for coordinator review before replacing the live
   historical 19-test inventory. Do not silently relabel proposal receipts as installed runs.

The detailed procedure is [B's post-install handoff](../U4-B-K1-stage2-reconciliation-v1/post-install.md).
A local installation commit is necessary to supply its real source identity; no installed
result or inventory approval can be claimed in advance. If any reviewed byte must change,
stop and reconcile the delta instead of broadening this authorization.

U0024 still applies. No hosted/remote activation, registry publication, server work, native
performance qualification, K2 release, G3a acceptance, sprint closure or tag. Do not poll CI.
