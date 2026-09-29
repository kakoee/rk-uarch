# U-P0 · U0 · either, run once — Repo bootstrap

_From build-spec §8. One prompt, one fresh session._

> **Prefer the standalone file.** `BOOTSTRAP-PROMPT.md` at the root of this kit is this prompt with
> the tree, `CLAUDE.md`, every README and all the tooling inlined. Attach that one file to a
> fresh session in a directory holding this kit's `docs/`, and say "follow this file." Use the
> short form below only when `docs/build-spec.md` is already loaded as context.

```text
CONTEXT TO LOAD: docs/build-spec.md §1 through §6 (scope, architecture, repo layout, the
README set, interfaces, conventions). docs/execution-plan.md §1 (the sprint loop).

TASK: create the rk-uarch skeleton. Structure and documentation only: no schema, no engine,
no test logic. When you are done, someone should be able to clone the repository and
understand the whole system before a single model exists.

1. The tree in build-spec §3, exactly. Python packages get __init__.py with a one-line
   docstring. Directories filled by later prompts get a .keep plus their README now.
2. Every README in build-spec §4 and CLAUDE.md, verbatim. These are the point of the task —
   do not summarise, merge or improve them.
3. Tooling: pyproject.toml (uv, Python 3.12, hatchling with
   [tool.hatch.build.targets.wheel] packages = ["src/rkuarch", "contract/uarch_contract"]),
   Makefile, .importlinter, .pre-commit-config.yaml, .gitignore, .github/CODEOWNERS,
   .github/workflows/{ci.yml,nightly.yml}, native/CMakeLists.txt (an empty project that
   builds nothing yet), containers/Dockerfile.engine (base image only), and
   third_party/LICENSES.md with the allow-list and an empty register.
4. tests/unit/test_prompt_sync.py: asserts every ```text block in build-spec §8 equals the
   text block in the matching docs/prompts/ file. It passes on day one because the kit
   ships both.

ACCEPTANCE TESTS:
1. uv sync --extra dev succeeds on a clean checkout.
2. make test runs and passes; make lint and make typecheck are clean.
3. Every CI job exists. A job that has nothing to test yet reports "nothing yet" and exits 0
   ONLY where build-spec §6.7 says it may. Every other job fails on an empty suite.
4. python -c "import rkuarch, uarch_contract" succeeds, and import-linter forbids
   rkuarch -> rk.
5. git status is clean after committing.

GUARDRAILS: Do not create any file that is not in build-spec §3. Do not write model,
schema, engine or test logic — later prompts own all of it. Do not edit anything under
docs/ except to add docs/decisions/U0000-record-architecture-decisions.md, adapted from
rk-sim's ADR 0001.
```
