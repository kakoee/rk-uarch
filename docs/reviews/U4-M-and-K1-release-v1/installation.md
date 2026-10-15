# Human ADR installation — approved D1 and D2

Approval is recorded in [acceptance.md](acceptance.md). The helper was committed at
`d1258fb03c1ba014ac6121f10abd2461b60f96ac` and is bound to the unchanged approved ADR
patch `3dbe69f47765089d67fbd5badf5c130ee2609c04bf6022a03fc899b61d47bbc0`.

Run in the coordinator checkout:

```sh
cd /home/jjaff/AI-infra-simulation/rk-uarch
UARCH_HUMAN=1 bash docs/reviews/U4-M-and-K1-release-v1/human-install.sh \
  --package-commit d1258fb03c1ba014ac6121f10abd2461b60f96ac
```

This applies and locally commits only `docs/decisions/U0011-the-native-engine-core.md`
with normal ownership/prediction hooks. It leaves pre-existing untracked reviewer files
alone. It does not push, install M or policy sources, generate/adopt an artifact, execute
native code or claim a gate pass. Return its receipt for verification and publication;
then the prepared lane continuations can consume the installed authority from main.

The human step follows CLAUDE.md: "Agents propose and stop on contract/,
tests/golden/expected/, CLAUDE.md, docs/decisions/." Approval is already recorded;
this is execution of the repository's human-owned installation, not another decision.

## Helper checks executed

- Embedded Python syntax, shell syntax, local links and unchanged patch identity passed.
- Read-only preflight passed in the real checkout and a disposable clone; computed ADR
  postimage matched the approved hash. Neither preflight installed or staged live files.
- Missing human flag, missing/non-ancestor package pin and a dirty helper were refused.
- Live protected bytes, HEAD and tracked/index state stayed unchanged during those checks.
- No real install/commit path was executed by the coordinator. No runtime/full-suite or
  CI rerun is claimed for this helper. Source/runtime are unchanged.

The approved proposal remains preserved verbatim; its prior pending status is superseded
by acceptance.md. Subsequent documentation commits can follow the helper commit, provided
its package and approved peer inputs remain identical and protected before-image matches.
