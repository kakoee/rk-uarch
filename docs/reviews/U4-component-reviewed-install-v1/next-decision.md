# U4-component-reviewed-install-v1 — decision draft, held for CI-C1

**Not approval-ready: resolve CI-C1 before presenting the final exact installation package.**
The semantic recommendation is P2 and the reviewed NoC convention. The current mechanical
preview fails its selection-identity test because it preserves installed K2 ADR clauses.
The independent reviewer has accepted the response checks. A later decision would select the
remaining model/profile promises and authorize guarded human installation of the corrected
code/schema/test/ADR package. This draft grants no installation or native release.

## Proposed scope after identity reconciliation

1. **Safe accumulator reuse and explicit mapping version.** Enable opt-in `ws-rowsplit@2`:
   reuse overlapping accumulator storage only when every final reader completes before
   the next producer. @2 orders all operand placement topologically, even on uniform cores.
   Historical @1/default behavior is preserved.
2. **Component observations `/2`.** Accept the exact reviewed phase, resource, causal,
   clock, queue and job-summary semantics in the proposed U0011 addition. The independent
   checker derives service laws and actual causes rather than trusting reported occupancy.
   Fixed-delay `/1` retains its existing meaning. The old scalar blocker/predecessor fields
   are explicitly unrepresented for `/2`; typed activity links carry that information.
3. **NoC occupancy convention.** At this first component stage, positive-hop NoC occupancy
   records the union of in-flight latency attributed to a router. It does not serialize
   transfers or model bandwidth contention. Zero-hop movement remains nonoccupying.
   This keeps the stated NoC0 model honest; it does not increase fidelity or validate accuracy.
4. **P2: policy-bound profiles for NEW component authority.** Accept the additive profile/2
   entry binding `{name, version, buffer_depth}` alongside graph and point identity, for
   checkpoint B component/transport-fixture admissions. New component authority must require
   profile/2 and bind its hash without fallback. Existing profile/1/K2 anchors stay unchanged.
   The parser supports both; merely creating a profile does not confer authority.
5. **Prospective human installation scope.** The current preview contains 24 paths in [postimages.json](postimages.json)
   using [install.unapplied.patch](install.unapplied.patch), SHA256:
   `a960bc1099e8ee263351c0cf05b1264aef465185a2c83a45c603cbf42da836ad`.
   This blocked preview includes the ordinarily discovered F5 regression, the other reviewed tests/checker,
   mapper/loader changes, three schema mirrors, protected carrier/tests and reconciled U0011.
   The current K2 ADR suffix and exact reviewed component suffix are both preserved. A later final approval
   would permit preparation of the guarded human install/checkpoint/publication sequence for
   the final corrected bytes; the agent does not install protected files itself.

Read [proposed U0011](proposed-U0011.md) for the exact normative text and
[the original P1/P2 explanation](../U4-A-component-stage2-v1/profile-decision.md) for the choice.
P1 would instead keep profiles graph/point-only and put policy binding into a separately
trusted execution selection. Choosing P1 requires a different, concretely reviewed patch;
it is not the 24-path candidate proposed here.

## Evidence and limits

The same reviewer's accepted subject is the original patch `81b81c6c…` plus B's additive
patch `23724b20…`, publication `354420fb8c75cb6fb922db82b9eec6bca644fefc`.
All code/test/schema bytes remain exact. U0011 reconciliation is append-only, preserving
installed K2 text verbatim. Coordinator private forward/reverse patch checks, strict vendor
currentness and mapped-schema freshness pass. The one targeted identity test FAILS on the
reconciled ADR; that must be repaired with explicit historical/installed bindings first.
Behavioral results are inherited from the independent review and authors, not newly rerun
or added together.

The unchanged 106-case selection does not bind the added F5 test; B's additive proposal
and this manifest do. Input selection is prospective evidence, not execution authority.
No oracle generation/adoption is needed for this exact support-preserving candidate.
The carrier changes future component runtime identities, so old K2 authority cannot be reused.

This decision does not authorize component native implementation/builds or mapped execution,
D3 negative transport, new dependencies, hardware measurements, remote infrastructure,
performance qualification, a full product table, G3a or U4 closure. Those retain their own
concrete scope and first-use boundaries. Human H-L1-GEMM-01/H-L1-DMA-01 and B's named O2
transient-lifetime obligation remain pending at their applicable evidence boundaries.

The existing repository rule in [CLAUDE.md](../../../CLAUDE.md) says:
“Agents propose and stop on contract/, tests/golden/expected/, CLAUDE.md, docs/decisions/.”
This package includes contract files and U0011, and its model/profile choices have not yet
been approved. That is why human approval and installation are required after review.

Do not approve or run this preview yet. B has the exact CI-C1 reproduction and the named
O2 verification obligation in lane-B.txt. The coordinator will bind the corrected package
and applicable focused evidence before asking for the human decision.
