# Newly executed checks and limits

[checks.json](checks.json) records exact argv, cwd, expected and observed exit codes for the
corrected full audit. Individual command logs are adjacent; the inventory output is normalized
in inventory.json. Interpreter: existing CPython 3.12.14 from
`/home/jjaff/AI-infra-simulation/rk-uarch/.venv/bin/python`. The inventory receipt records
executable, Linux/WSL kernel/platform and asserted scratch module origins. No tool/dependency
installation occurred. Host Python supplies these Python checks; no native tool/image result
is claimed by this task.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  docs/reviews/U4-M-policy-installation-readiness-v1/audit.py \
  --python /home/jjaff/AI-infra-simulation/rk-uarch/.venv/bin/python
```

The reproducer requires its exact audited HEAD, `9b1408437b6dc08d9b77848f5fffe56c0cf1db72`,
and writes only readiness receipts plus temporary exports. It refuses another HEAD rather
than silently changing the source claim. To reproduce after publication, use a disposable
clone at that baseline and the published audit script; do not reset a live worktree.
The original patch files, A manifest and required source ancestry must remain available.

| Check | Observed |
| --- | --- |
| Exact patches and postimages | Both digests match; M 26/26 postimages; repair 6/6 matches independently reconstructed accepted-baseline postimages |
| Selected support and actual reads/imports | 56 entries, broad combined 101; no path/hash delta from prior final audit; current AST/data review retained |
| Combined pytest | 369 passed, 1 skipped in 139.41 s; no empty collection |
| M / legacy / rotary-v2 schema check | All fresh; check mode only against source mirrors |
| Source mypy / contract-test mypy | 82 / 32 files, no issues |
| Ruff / import contracts | Pass; 2 contracts kept, 0 broken |
| Live strict currentness | Pass; existing source/adopted pair |
| Combined strict currentness | Expected exit 1 with `input support inventory changed`; not credited as compatibility |
| Read-only live adoption positive | 1 passed in 0.63 s; current 1,008 rows/four refusals and U3 review join |
| Installer preview/refusals | 9 passed in 0.75 s; all patching confined to scratch; install branch never enabled |
| Final source isolation | All 1,987 export files and 1,958 live tracked files unchanged in bytes/mtime; empty isolation-delta.json |

The exact suite names and flags appear in checks.json. Its additional controls cover all
existing repair-policy/vendor entry points, final M admission, contract rotary-v2, tests/rotary_v2,
U2 A prepared replay and B final fixture inputs. The live adoption check selected only
`contract/tests/test_u2_historical_snapshot.py::test_current_canonical_is_exact_adopted_1008_four_real_refusals`;
other tests in that module can stage inputs and were not invoked by this task.
Installer tests use explicit root/config, bytecode/cache disabled and a separate `/tmp` base.
They test a complete disposable preview, wrong/missing/new-path collisions, postimage drift,
symlinks/path escape, exact synthetic authorization parsing and absent-human-flag refusal.
Their synthetic dictionaries are not actual authority records. No human install branch was
run or validated as a completed human commit.

The audit clears PYTHONPATH/MYPYPATH/VIRTUAL_ENV/UARCH_HUMAN/SHA/RK/PARAMS, disables bytecode
and pytest caches, sets explicit scratch-root/src/contract precedence and asserts module
origins. M and policy source bytes are modified only while constructing the disposable
proposal. Negative source mutations stay in the existing tests' throwaway roots. Schema
mutation tests may generate synthetic schema mirrors in test temp directories; these are
not oracle input staging, generation or adopted artifacts.

An initial full run passed the suites/static checks but failed the final export-isolation
assertion. The audit called import-linter's Python API with a CLI argument in sys.argv;
that API ignored the argument and created its default cache. [audit-retry.json](audit-retry.json)
records a separate reproduction: five new cache files, no changed existing files. The original
failed export was already removed, so its precise delta is not retrospectively asserted.
The harness now passes `no_cache=True` directly and propagates the API return code. The full
corrected run passed and proves source isolation; no failure was waived or labelled a pass.
Initial new-helper lint findings were corrected before publication.

Inherited: prior selected-policy design/fault campaigns, A's original M tests-first history,
accepted host-trust mechanism and B scalar derivations. Current normal controls were rerun;
those earlier campaigns are not claimed as fresh executions. Real native K1 review, K2/B
fault campaigns, human L1 work, real new-policy generation/adoption and infrastructure remain
outside this preparation. Other hosted checks remain active, but no GitHub CI result was
polled, awaited or credited.
