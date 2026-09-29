# Fresh-session implementation template

Adapted from rk-sim's template of the same name. Replace the placeholders, then paste into a
fresh session. Use `none` for the baseline if no specific tag or commit is required.

```text
Read CLAUDE.md, docs/execution-plan.md's applicable sprint section, docs/how-it-works.md,
relevant prerequisite handoffs in docs/reviews/, and docs/prompts/<PROMPT_FILE>, including its
required context. Verify main and <BASELINE_REF> before editing; preserve existing local changes.

First resolve prerequisite contracts under the decision authority in CLAUDE.md. Verify ADR
status: do not treat proposals as accepted or reopen decisions already settled. Ask only for
decisions or permissions existing authority does not cover.

Then implement this prompt against the accepted contracts. Write its acceptance tests first,
inspect existing code, follow the prompt's guardrails, and run the required checks:
uv run pytest -q, uv run mypy src contract, uv run ruff check, and make native-test if
anything under native/ changed. Record decisions, validation, limitations and a clear handoff in
docs/reviews/U<sprint>-<prompt>-handoff.md.

Stop after this prompt. Do not implement successor prompts, declare the sprint complete, or tag
it. Leave changes local and uncommitted.
```

# After implementation: commit, do not push

```text
Commit these changes to main. Do not push.
```

# Fresh-session review

Use `docs/prompts/U-REVIEW-adversarial-review.md` at sprint end. For a single prompt mid-sprint,
use this:

```text
Review <BASE_SHA>..<HEAD_SHA>, which implement docs/prompts/<PROMPT_FILES>. Do not change code;
give findings I can pass to the implementing agent. Read CLAUDE.md, the prompts, their cited
ADRs and the handoff (claims to verify, not evidence). Check every task item, acceptance test
and guardrail; run the checks above; confirm suspected bugs with scratchpad probes. Report
most severe first with file:line: must-fix items (each with a reproducer and a proposed
regression test), decisions for the humans, coverage gaps, then a per-prompt checklist. Write
the results to a review file under docs/reviews/.
```

# Back to the implementation session: fix review findings

```text
Read <REVIEW_FILE>. Treat findings as claims: confirm each with its reproducer, write its
regression test and see it fail, then fix. If a finding is wrong, say why with evidence instead
of changing code. Leave human decisions alone. Append a "Review response" to your handoff
mapping each finding to its fix and test, or your reason. Leave changes uncommitted.
```
