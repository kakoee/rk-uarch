# U4 kickoff — bounded native engine and silicon readiness

Javid authorized U4 on 2026-10-14: “Let's start U4. You know the process, same story as
Lane A, Lane B sessions, etc.” This releases U4 work under its accepted first-use gates;
it does not silently approve the still-open exact schema, toolchain, licences, corpus,
artifact installation, human generation/adoption, hardware spending or performance budgets.
The earlier U3-closeout-only restriction remains historical; this is the later U4 release.

## Verified starting point

U3 is closed. Human annotated tag `u03-end`, object
`e029adcedb82cfe192f8e700a3b5ffc20db92b47`, peels to
`6d39a234a14855c86ca54b795501a0b0b2618d7b`, verified on origin/main.
[Final main CI](https://github.com/kakoee/rk-uarch/actions/runs/38578691552) and
[documentation closeout CI](https://github.com/kakoee/rk-uarch/actions/runs/38576360379)
passed on their exact commits. [U3 technical dispositions](../U3-closeout.md) and
[accepted U0011](../../decisions/U0011-the-native-engine-core.md) remain the starting scope.
No native implementation or silicon qualification is inferred from U3 closure.

## Start two fresh worker sessions

- A cwd: `/home/jjaff/AI-infra-simulation/rk-uarch-u4-a`; use [Lane A prompt](lane-A.md).
- B cwd: `/home/jjaff/AI-infra-simulation/rk-uarch-u4-b`; use [Lane B prompt](lane-B.md).
- Coordinator stays in `/home/jjaff/AI-infra-simulation/rk-uarch`.

These are independent clones on main, not linked worktrees. U3 folders and historical
review evidence are preserved. Do not resume the U3 author sessions for these new tasks.
Javid relays handoffs; workers must not start duplicate agents or contact the peer/humans
through external messaging. Each lane follows [shared workflow](workflow.md).

## First concrete checkpoint

| Lane | Deliver now | Dependency / next release |
| --- | --- | --- |
| A | Exact M carriers/fixtures/profile patch, proposed importer/exporter edges, schema/refusal checks; immutable Rust/dependency/licence pin package | B checks exact closure and independent expectations. Human schema installation and separate pin/licence decisions precede their applicable implementation boundaries |
| B | Independent cases/variant proposals and human L1 worksheets; exact Linux CI proposal with A's pins; audited artifact-policy transition against concrete M | Independent work starts immediately. Final closure/CI reconciliation waits only for A's published exact package |

This is implementation preparation, not another architecture redesign or repetition of the
completed U3 adversarial reviews. Publish usable bounded outputs as they are ready. For this
first handoff, stop before live protected installation, policy repair, generation/adoption
or kernel coding. K1 can begin once its exact toolchain/licence prerequisites are accepted,
independently of M installation; K2 additionally needs installed mapped carriers and M's
fixed-delay boundary. B component execution follows K2. R is actual reference readiness
before G3a/U5. T full tables remain U7; rk-sim production integration remains U10.

The concrete handoffs must identify each decision and its exact bytes, recommendation,
owner and next executable task, so subsequent releases do not become open-ended planning.
The coordinator will reconcile A/B and present only unresolved exact decisions to Javid.
Human-worked L1 results must come from a human; B may prepare questions and inputs but
cannot label its own arithmetic as human working. No human assignee is invented here.

Hosted Linux correctness work can proceed without self-hosted runner registration under
U0023. Performance/automation and reference-hardware obligations remain at their accepted
later gates. No host provisioning, hardware acquisition or measurement is released here.
