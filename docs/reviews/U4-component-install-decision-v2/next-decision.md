# U4-component-semantic-install-v2 — approval requested

**Recommendation: approve the reviewed component semantics, P2 profiles, and exact 29-path
human installation package.** CI-C1 and the O2 preparation coverage join are reconciled.
This replaces the earlier blocked 24-path installation preview; no repeated tool or licence
approval is requested.

## What changes

- **Mapping and accumulator lifetime:** opt-in ws-rowsplit@2 allows exact-size accumulator
  reuse only after all terminal readers precede the next producer. It places all SRAM/HBM
  operands in stable topological order, including uniform-footprint cores. @1/default behavior
  remains historical. No capacity increase, spill or new workload scope is implied.
- **Component observations /2:** adopt the exact reviewed phase, causal, clock, resource,
  queue and job-summary semantics. Required occupancy follows declared mechanisms; the
  independent checker derives durations and causes. Typed activity links express causality;
  the old scalar blocker/predecessor fields are explicitly unrepresented for /2. Fixed-delay
  /1 remains unchanged.
- **NoC convention:** positive-hop occupancy records the union of in-flight latency attributed
  to a router. It adds no serialization or bandwidth contention. Zero-hop movement is
  nonoccupying. This remains NoC0, with no extra fidelity or accuracy claim.
- **P2 for new component admissions:** profile/2 binds mapping policy name, version and
  buffer_depth as well as graph/point identity for checkpoint B component/transport scopes.
  NEW component authority must explicitly require and authenticate profile/2 with no fallback.
  Legacy profile/1 and existing K2 anchors are preserved. A profile file alone is not authority.
- **Protected installation:** authorize guarded human installation of the exact 29-path
  code/schema/ADR/test/binding package below. U0011 preserves the installed K2 text and appends
  the exact reviewed component text. Discoverable F5 and transient-lifetime tests and explicit
  historical-versus-installation identity checks accompany the implementation.

## Exact subject

- B publication: `aa5428e91c02fca985bb33d91bdefc1c474bb9b5`.
- [Combined unapplied patch](../U4-B-component-install-joins-v1/install-with-joins.unapplied.patch):
  SHA256 `008dc61147431cc6be3d78656a482512e17fd6d0f84a6beaf0920fe1bf641b70`.
- [29 pre/postimages](../U4-B-component-install-joins-v1/postimages.json):
  SHA256 `e8cef2bcbfc04a29c27c0e22a8f4156665a399df11f372841e1a99877e8defb9`.
- [Exact proposed U0011](../U4-component-reviewed-install-v1/proposed-U0011.md):
  SHA256 `edf565f9094c524b280888feaf29bcecc63b176aa573393c136b3494c7c640fd`.
- [Installation transition](../U4-B-component-install-joins-v1/transition.json) binds the new
  verification paths while preserving the immutable 106-case selection and all input bytes.
- [P1/P2 explanation](../U4-A-component-stage2-v1/profile-decision.md): P2 is included in these
  exact bytes. Choosing P1 instead requires a different bounded candidate, not a silent fallback.

The original software response plus F5 has independent Stage 3 acceptance. B's subsequent
verification-only joins are coordinator-reconciled: six focused tests, private patch
reconstruction/current-main postimages, mapped-schema freshness and strict vendor currentness
pass. Broader author/reviewer checks remain inherited, with no inflated or additive counts.
See [coordinator evidence](checks.json) and [B's evidence](../U4-B-component-install-joins-v1/README.md).

## Authority and execution boundaries

Approval covers the exact semantic choice and preparation of the guarded human source/test/ADR
installation, local checkpoint and subsequent verified publication sequence. It does not
permit the agent to write protected live files itself. No U0002 oracle regeneration/adoption
is required for these support-preserving bytes; currentness must be checked at installation.
Any changed source preimage or postimage is a mismatch to reconcile before placement.

This is not a component native implementation/build/execution release. It supplies no new
engine/build/host/profile authority or D3 negative transport permission. The changed mapped
carrier requires new component runtime bindings; existing sealed K2 roots and authorities
remain unchanged. Human H-L1-GEMM-01/H-L1-DMA-01 are still due at L1 acceptance. O2 synthetic
coverage is now supplied, but real native outputs must still satisfy the applicable checker.

No new dependencies, hardware measurement, remote infrastructure, performance qualification,
full product table, G3a or U4 closure is granted. U0024 and the independent optimizer's scope
are unchanged. Component implementation/verification prompts follow installation/publication
under their separately concrete native scope.

[CLAUDE.md](../../../CLAUDE.md) requires: “Agents propose and stop on contract/,
tests/golden/expected/, CLAUDE.md, docs/decisions/.” This package changes contract files and
U0011 and selects the still-pending P2/NoC semantics, so human approval/installation is needed.

Suggested reply: **Approve U4-component-semantic-install-v2, including P2 and the stated
NoC and /2 semantics, for the exact 29-path human installation package.**
