# STANDING · every sprint end — Refresh docs/how-it-works.md

_One fresh session. Same mandate as rk-sim's standing prompt of the same name._

```text
CONTEXT TO LOAD: CLAUDE.md, docs/how-it-works.md, docs/execution-plan.md (STATUS and the sprint
just closed), the sprint's docs/reviews/ closeout and handoffs, and the code the sprint touched.

TASK: amend docs/how-it-works.md so it is true of main at the tag you are given, and is
readable by someone returning to the other lane after a month.

1. Amend it; do not append. Every section earns its place. A subsystem that grew earns the
   lines that explain it; a section describing something that no longer exists is deleted.
2. Real numbers: quote at least one real table row, with its hash, for every engine the
   sprint touched, and the current composite fidelity and badge of each golden design.
3. Say what the numbers do not claim: the stipulation count, the evidence scope, "unknown"
   error bands.
4. Link every claim about behaviour to the test that pins it.

ACCEPTANCE: every file path and command in the document exists and runs at the tag; every
quoted number is reproduced by the command next to it.

GUARDRAILS: Documentation only. Change no code, fixture or ADR.
```
