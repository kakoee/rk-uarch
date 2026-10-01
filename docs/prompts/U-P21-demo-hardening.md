# U-P21 · U11 · both — Demo hardening

_From build-spec §8. One prompt, one fresh session._

```text
CONTEXT TO LOAD: CLAUDE.md, README.md, build-spec §1.2 (the acceptance demo: the definition of
done), docs/execution-plan.md U11, docs/how-it-works.md, every docs/reviews/*-closeout.md.
From rk-sim READ-ONLY: docs/prompts/P13-demo-hardening.md (same discipline).

TASK: a stranger can run it, and either founder can perform the build-spec §1.2 demo cold,
including the other lane's parts.

1. docs/demo-script.md: build-spec §1.2 turned into exact commands and clicks, with the
   expected output of each step pasted from a real run and the hashes of every table it
   touches. When a step's output legitimately changes, the script changes in the same commit.
2. Seed data: every design, reference, study and fixture table the demo needs, committed, with
   hashes; `make demo-data` rebuilds and verifies them.
3. Error states: every error in contract/errors.py has a CLI message a stranger can act on.
   Test each by invoking the CLI and matching the message.
4. README: a stranger reaches a built table from a clean clone following only the README,
   engine image included, and the README says how long each step takes on the reference box.
5. docs/what-this-is.md: what a uarch number is, what it is not, the two validation verdicts
   with their scopes and bands, the sync curve's verdict (or that U9 was deferred, and why),
   the stipulation ceiling, the
   declared omissions, and the state of energy evidence, in one page.
6. A fresh session runs STANDING-how-it-works-refresh.md afterwards; not this one.

ACCEPTANCE TESTS:
1. Each founder performs the demo cold, twice, with no crashes, and the log is committed.
2. A person who has not seen the repo reaches a built table from the README; their notes are
   committed.
3. Every contract error has a CLI message test.
4. `make demo-data` verifies every hash.

GUARDRAILS: Change no model, threshold or badge rule in this prompt. A demo that needs one
changed has found a bug: file it and stop.
```
