# U4-PUB-C1-and-M-publication-v1

Approve the following separately recorded actions after the checks in the accompanying
reconciliation receipt are complete:

1. **Install and locally commit PUB-C1's single test correction.** In A's clone, preserve
   human commits `0cf24d91eeca5cc45182eb6fb03202677fd97dcb` and
   `5e774682a7abdc21aa0bac6a8f738e66c852d3e5`. Apply exactly B's reviewed patch from
   `3af7ae2f347d2ff33a89018af27f0e0393622f71`, SHA256
   `64fce5ddcc4e75dcd540e359336d9daad6bb86492162c4044a29a235fa0bef5c`.
   Only `tests/unit/test_u2_b_tooling_binding.py` changes, from SHA256
   `efc96c7602d2c18ca47a62cd5f82bbf3974d62caa6cc6103da33492fdfd634e4` to
   `41acad3e368de53a5f1cf4a433adf4a20956c2d33e1160dc14119b1f3ad1f74a`.
   Use normal hooks and message `test(u4): separate relocation probe inputs from generator support`.
2. **Integrate published review documentation into A.** Use a normal merge preserving both
   histories. Inspect the diff from A: only reviewed documentation may be added beyond the
   single test correction. Preserve exact tested runtime, contract, policy and artifact bytes;
   stop for reconciliation if intervening main changes add other implementation/config edits.
   Recheck strict currentness and the corrected test on the final integrated checkout.
3. **Publish with a separate normal push.** Fast-forward origin/main to the verified merge,
   never force-push. Record local commit, merge and remote identities separately. Update the
   coordinator and B only where a clean fast-forward preserves all untracked review material;
   otherwise leave the working lane untouched and provide its exact update dependency.

This is the separate publication approval reserved after the human local checkpoint. It
includes the previously unpushed 32-path source installation, ten-path adoption and this
one-path test correction (42 distinct non-review paths relative to the tested published
baseline). No human-only hook bypass is necessary: protected changes are already in the
human ancestry, and the proposed new commit changes an ordinary test only.

No policy expansion, source refresh, oracle execution, generation or artifact re-adoption.
The candidate manifest remains `b19016be07307ed987037d8a079f85af0366eab018b1132c2668394acd756bcc`.
K1 author patches remain unapplied and subject to their own Stage 3 verdict and installation
step. This decision does not accept K1, release K2, activate remote native CI, change server
or registry access, tag or close U4. Do not poll GitHub CI; Javid reports its result.
