# Combined K2 runtime — Stage 2 coordination

The independent review identifies two blocking packaging defects and four bounded
non-blocking defects, all owned by B. It reports no correctness failure in A's runtime or
the native/validation path. These are reviewer results, not coordinator reproductions.

Give [the consolidated task](lane-B.md) to the existing B packaging author. The task covers
F1–F6 in one pass. A's optimized runtime stays unchanged unless a concrete new dependency
is demonstrated. The separate component reviewer can continue against its own pinned
subject; no component acceptance follows from this runtime review, or vice versa.

F1 must be resolved before decision/binding rendering; F2 before replay. Keep the proposed
runtime uninstalled and the campaign stopped. After B's consolidated response, reconcile
its exact candidate and return it to the same reviewer for Stage 3. Human acceptance and
actual placement/preflight/campaign evidence remain separate.

## Human choices: coordinator recommendations, not approvals

- **H1:** Verify publication against the actual expected remote, recording its observed main
  commit. Sanitize Git state and disable replacements regardless. Local tracking refs are
  not proof of publication, and publication is not proof of human consent.
- **H2:** Keep the bounded runtime-copy rule in U0011 and propose a short U0002 cross-reference
  clarifying that canonical generator currentness remains enforced. Any protected wording
  stays unapplied until the exact final package is approved.
- **H3:** Keep stop-on-failure as the current behavior. In the final decision package, offer
  a bounded operational-retry policy with exact attempt limits, preserved failed evidence,
  fresh outputs and unchanged approved inputs; no retry may mask validation/identity
  failures or combine partial attempts into a successful campaign. No retry is approved
  here. This choice need not interrupt technical corrections.
- **H4:** Keep the existing 7,200-second outer limit. State timer origins and which deadline
  governs; do not imply 7,200 seconds of processing in addition to startup. Any request to
  increase the cap belongs in the final decision, not in a hidden implementation change.

These recommendations can be reviewed together with B's concrete correction package; they
are not four additional approval requests now.

## Evidence handling and verification limits

[Review input identities](review-inputs.json) pin the report and bounded evidence as read
from the coordinator checkout. Reviewer files remain untouched and unstaged. In particular,
`results/launcher-poll-race.json` still lists a background stress run as pending; no result
from it is credited. The deterministic F4 reproducer is already sufficient for correction.
The full report and probes are available locally at the paths in the manifest. They are
not part of this coordination commit; the B prompt names their absolute location.

Coordinator work here is limited to reading the report/package, checking repository state,
and preparing the consolidated task. No defect reproduction, runtime test, installation,
new authority, native execution, full campaign or qualification was performed. Original
review probes have six Ruff diagnostics and are left byte-identical rather than silently
rewritten or added as executable CI inputs. Their eventual preservation should retain the
executed bytes with explicit provenance. Only this coordination package is published now.
