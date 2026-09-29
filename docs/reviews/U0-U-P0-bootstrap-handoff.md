# U0 · U-P0 — bootstrap handoff

**Created 2026-09-28** from the rk-uarch kit (BOOTSTRAP-PROMPT.md), next to rk-sim in `~/Github`.
Local only: no remote configured, nothing pushed.

## What exists
The tree in build-spec §3; `CLAUDE.md` and 23 READMEs verbatim from build-spec §4; every
package as a one-line docstring naming the prompt that fills it; `docs/` (build spec,
execution plan, U-P0…U-P21, U-REVIEW, STANDING, TEMPLATE); `rk-sim-side/` drafts; `uv.lock`.

## Acceptance (run on the linked machine, venv and caches outside the repo)
- `uv sync --extra dev` — ok (uv-managed Python 3.14.7; `requires-python >=3.12`)
- `pytest -q` — 3 passed (prompt sync, third-party register ×2)
- `ruff check .` — clean · `mypy` (strict) — no issues in 27 files
- `lint-imports` — 2 contracts kept (rkuarch ↛ rk; contract ↛ harness)
- `import rkuarch, uarch_contract` — ENGINE_VERSION 0.0.0

## Not in this commit — add by hand (the remote tools refuse to write these)
`Makefile`, `.pre-commit-config.yaml`, `.github/CODEOWNERS`, `.github/pull_request_template.md`,
`.github/workflows/ci.yml`, `.github/workflows/nightly.yml`, and the executable bit on
`scripts/hooks/*.sh`. Contents are in BOOTSTRAP-PROMPT.md PART 3 (and in the
`rk-uarch-protected-files.zip` delivered alongside). Until the Makefile lands, `make …`
commands in CLAUDE.md run as their `uv run …` equivalents.

## Not done, deliberately
U0 is not tagged: its exit criterion includes CI existing and running, which needs the files
above and a remote. The execution-plan STATUS block is unchanged.
