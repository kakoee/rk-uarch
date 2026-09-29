# U-REVIEW · standing — Adversarial review (review → response → adjudication, per lane, every sprint end)

_From build-spec §8. One prompt, one fresh session per stage. Adapted from rk-sim's P14, which
is the authority wherever the two differ in process._

```text
U-REVIEW IS A THREE-STAGE LOOP AND NO STAGE IS A HUMAN. Read the stage that is yours.
Stage 1 REVIEW (a cold agent) -> Stage 2 RESPONSE (the authoring session) ->
Stage 3 ADJUDICATION (the reviewer again).

=== STAGE 1 · REVIEW — you are a fresh session that did not write this code ===

You are reviewing rk-uarch's Sprint U<N> diff against docs/execution-plan.md §3 (that sprint's
block) and its prompts in docs/prompts/. Do not trust commit messages or the author's review
records; they are claims to verify.

YOU MUST NOT HAVE WRITTEN THE CODE YOU ARE REVIEWING. If you find you already know it because
you wrote it earlier in this conversation, SAY SO AND STOP. A clean verdict from the author is
worse than no review, because it will be believed.

CHECK, in order:
1. Does the sprint's joint exit criterion actually run, on the Linux box, from a cold clone?
   Execute it. Paste the output.
2. Does any number reach a human without its badge? Grep report templates for raw values;
   run `uarch report` on the sprint's tables and scan for "±0"; check CLI output paths.
3. Did any golden change? If so, is there a docs/decisions/U*.md for it, and does it match the
   diff?
4. Numerical smells: units missing from names; cycles crossing out of engines/ or native/;
   time converted anywhere but next_edge(); MACs counted as one op; the tp rule; seeds not
   plumbed into a new randomness source; unordered iteration reaching output. Re-derive the
   three most-touched formulas from their docstrings and say whether the code matches.
5. Provenance: any stipulation outside hw/designs/? Any claim without a source? Any reference
   spec that loads with a stipulation? Any derived value whose kind or provenance is better
   than its worst input?
6. Evidence: any model card promoted without ledger entries? Any promotion wider than its
   entries' scope? Any error band of zero? Any prediction file edited after its freeze commit?
   Run check_ordering yourself.
7. Fidelity: any composite C2 with a subsystem at level 0, or in lax sync mode without a
   covering curve? Any C2 row faster than its u_c0_duration_s?
8. Determinism: build one golden table at --workers 1 and --workers N yourself and diff the
   bytes. From U9, also at 1 and 4 threads in exact mode.
9. From U6: run the native-vs-fork harness on one matched configuration yourself.
10. Scope: anything built that build-spec §1.3 lists as out? Name it.
11. READMEs: does any directory's README now describe something that is no longer true?

WRITE THE REPORT TO docs/reviews/U<N>-lane-<A|B>-review.md, incrementally, as you finish each
check. Number findings F1, F2… and label each BLOCKING or NON-BLOCKING with evidence:
file:line, pasted output, or a reproducing command. Do NOT fix anything. Style is out of scope.
You are producing evidence, not a verdict.

=== STAGE 2 · RESPONSE — you are the session that wrote the code ===

Read the report. Verify each finding yourself first: a reviewer can be wrong. Then write
docs/reviews/U<N>-lane-<A|B>-response.md answering EVERY numbered finding:

  APPLIED   what changed, and the test that now covers it. No regression test, not applied.
  REJECTED  why, in a sentence a stranger can evaluate. Reproducing the finding and showing
            it does not hold is a reason; "disagree" is not.
  DEFERRED  what it waits on, and where that is recorded. "Later" is not a plan.

Put every BLOCKING finding you rejected or deferred at the top, under a heading that says so.
You may not close a finding by editing the report.

=== STAGE 3 · ADJUDICATION — the reviewing session reads the response ===

Check three things and nothing else: (a) every numbered finding has a row; (b) each REJECTED
reason addresses the finding rather than restating intent; (c) each APPLIED change has a test
that fails without it. Check one at random by reverting it in a scratch copy. No new findings.
Append ACCEPTED, or NOT ACCEPTED with the rows at fault.

=== WHAT NO STAGE MAY DO ===

No stage tags the sprint. Humans tag u<NN>-end after the adjudication verdict is ACCEPTED.
```
