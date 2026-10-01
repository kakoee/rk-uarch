# Review prompt — rk-uarch Rev 2: book coverage and plan soundness

You are a fresh session reviewing the planning documents of `rk-uarch`, a simulator of one AI
accelerator's microarchitecture that feeds rk-sim. You did not write any of them. Treat every
statement in them, and in any earlier review, as a claim to verify, not as evidence.

The founders describe the goal as **"a cycle-accurate simulator of a hardware accelerator's
microarchitecture."** You answer two questions:

1. **Coverage.** Are most of the concepts in a performance-modeling textbook's table of contents
   covered by the plan, the prompts and the planned outputs?
2. **Soundness.** Does this plan make sense as a way to build that simulator, and will it
   execute as written?

## Sources: the repository only

- Use only files in this repository and its git history. No web search, no fetching URLs, no
  rk-sim checkout, no documents from outside the repo.
- You may use your own computer-architecture knowledge to *judge*. Label every such judgement
  `[judgement]`. Label every fact `[R path:line]`. A claim about an external tool (ONNXim,
  PyTorchSim, Ramulator 2, BookSim 2, SCALE-Sim, Accelergy, TPU v5e, Blackhole) that the repo
  does not support goes under "Cannot verify from the repo". Do not assert it.
- The book is **not** in the repo, only its table of contents
  (`docs/reviews/book-toc-performance-modeling.md`). Judge coverage of the concepts the headings
  name. Do not invent the book's content.

## What to read

Read these in full (build-spec §0's "never feed an agent the whole document" applies to
implementers, not to this review):

- `CLAUDE.md`, `docs/build-spec.md` (Rev 2), `docs/execution-plan.md`, `docs/glossary.md`;
- every file in `docs/prompts/`;
- every `README.md` outside `docs/`;
- `rk-sim-side/` (the draft ADR and the two rk-sim prompts);
- `docs/reviews/U0-U-P0-bootstrap-handoff.md` and `docs/reviews/book-toc-performance-modeling.md`.

**Do not open `docs/reviews/rk-uarch-book-coverage-review.md` until step 4.** Form your own view
first.

The Rev 2 changes are `git diff 0868dd3 HEAD -- docs CLAUDE.md rk-sim-side '*.md'`. Read that
diff as well as the current text.

## Steps

**1. Mechanical consistency.** Run them and paste the results:

- `uv run pytest -q`. `tests/unit/test_prompt_sync.py` proves that `docs/prompts/` matches
  build-spec §8.
- Every README and `CLAUDE.md` equals its block in build-spec §4.
- `rk-sim-side/prompts/P18-*.md` and `P19-*.md` carry the same text blocks as U-P19 and U-P20.
- Numbers repeated across documents agree. At least check: the integration rule count ("eight
  rules") everywhere; benchmark and class counts in U-P9 and U-P15 against gates G4 and G7; the
  measured errors listed in §2.3.3, U-P1, U-P7 and the table README; the composite C2 rule in
  §2.4, U-P13, CLAUDE.md invariant 9 and gate G6; the error classes in §7.4 against U-P1 item 10.
- `docs/execution-plan.md` §7 arithmetic: per-sprint sums, totals, milestones and weeks at
  20 h/week, recomputed from §7.1. Each sprint from U1 on adds 2.5 h best and 5 h realistic of
  review per lane; the rk-sim schema PR (U10) and U-P21 (U11) split evenly between the lanes; U0
  has no review.
- Leftovers from Rev 1 that contradict Rev 2: "six rules", "two errors", or a field that one
  document has and another omits.

**2. Coverage, independently.** For each two-level section (x.y) of the TOC, give a status:
Covered · Partial · Gap · N/A (CPU/GPU mechanism with no counterpart on a scratchpad NPU) ·
Out of scope (excluded by build-spec §1.3). Split a row only where its subsections differ.
Cite the strongest `[R path:line]` for each Covered or Partial row. "Covered" means a prompt
builds it *and* a test or output shows it, not only a mention.

**3. Soundness, for a cycle-accurate accelerator simulator.** At minimum, probe:

- **What "cycle-accurate" means here.** The plan's top level is "cycle-approximate" (level 2) with
  tile-level events, and RTL appears only as a reference. Say plainly where the plan
  deliberately stops short of cycle-accurate, whether that is the right call for its stated
  question, and whether any document overclaims.
- **Architecture.** Fork first, then a native C++ event-driven engine. The picosecond time base,
  the timing wheel, the reservation NoC, Ramulator 2 as a library, the per-subsystem ladder and
  the composite rule. Is anything missing that a cycle-level accelerator model needs (for
  example: instruction issue, scalar control, accumulator and operand buffering, DMA descriptor
  handling, back-pressure), or is anything included that the question does not need?
- **Workload and mapping realism.** Named policies with no search; layer reuse; canonical batches;
  the gap between uarch's mapping and a real compiler's.
- **Validation.** Can L0–L3 and the gates actually fail? Is each threshold pre-registered? Do the
  TPU v5e and Blackhole suites test the claims the demo makes? Is "detail is not accuracy"
  enforced or only stated?
- **Execution.** Sprint order and dependencies; whether each sprint's exit criterion is runnable;
  the effort estimates against the scope (especially U6, U7 and U9); Lane A as the critical path;
  any prompt an agent could not complete in one session as written.
- **Rev 2 itself.** Did it close real gaps or add scope creep? Name any Rev 2 addition that
  should be deferred, and any book concept it should have added but did not.
- **The next prompt, U-P1.** Could a fresh agent execute it now? Is every decision ADR U0001 must
  make listed, with a default?

**4. Compare with the earlier review.** Now read `docs/reviews/rk-uarch-book-coverage-review.md`.
List each place your status or judgement differs from it, and say who is right and why, with
evidence. Do not adopt its conclusions to break a tie.

## Output

Write `docs/reviews/rev2-plan-review.md`, incrementally, as you finish each step. No preamble, no
praise, no summary of what the plan says. Use this structure and these limits:

1. **Verdict.** At most 5 sentences. Is the plan fit to build a cycle-level accelerator simulator,
   and is it ready for U-P1? Yes or no first.
2. **Findings.** At most 12, ranked by severity. Each one is labelled BLOCKING (an agent builds the
   wrong thing, or a number overclaims, before or during U1–U4), MAJOR or MINOR. Each has at most
   3 sentences, at least one `[R path:line]`, and a concrete fix naming the file or prompt to
   change.
3. **Mechanical checks.** Each check from step 1: pass or fail, with the evidence.
4. **Coverage table.** From step 2, with counts per status at the top.
5. **Disagreements with the earlier review.** At most 8, from step 4.
6. **Cannot verify from the repo.** What would need outside evidence, and why it matters.

## Guardrails

- Change no file except `docs/reviews/rev2-plan-review.md`. Do not commit.
- Prefix every git command with `GIT_OPTIONAL_LOCKS=0` so that a read-only command such as
  `git status` never leaves a stale `.git/index.lock` behind.
- Do not fix anything. Produce evidence and a ranked list.
- Do not soften a finding because the rest looks good, or pad the list to reach 12.
- If a check cannot be run (no `uv`, say), write that it was not run and why. Never write that it
  passed.
