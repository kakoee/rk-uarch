# Observed checks and publication limits

All checks below were newly run by B against published main
95c1774ac15b6de11c7a9cc6d13e18a8a9da7c17 and the exact proposal identities in
[setup.json](setup.json). Existing CPython 3.12.14 was used at
`/home/jjaff/AI-infra-simulation/rk-uarch/.venv/bin/python`; no environment/tool install.

| Check | Observed result / receipt |
| --- | --- |
| Exact M plus selected repair in disposable Git export | All 26 M postimages match A package.json; final 56-path/digest inventory equals prior audit; [setup](setup.json), [origins/inventory](audit-1.log), [delta](closure-delta.json) |
| Repair-policy, vendor-entry and final mapped tests | 173 passed, 1 skipped in 45.76s; [exact commands/environment result](audit-checks.json), [pytest output](audit-0.log) |
| Patched strict currentness | Expected exit 1, `input support inventory changed`; [output](audit-2.log). This is a refusal of the old artifact, not adopted compatibility |
| Corrected D02/D14 and synthetic CI guard tests | 22 passed in 0.33s; [command](followup-tests.json), [output](followup-tests.log) |
| Existing prompt synchronization and CI scope tests | 30 passed in 1.06s; [command](scope-tests.json), [output](scope-tests.log) |
| Live strict currentness | Exit 0; correct clone module origin and adopted source/artifact pair verified; [command](live-currentness.json), [output](live-currentness.log) |
| Retained A pin/package/lock/feature/recipe consistency | `python3 -B docs/reviews/U4-B-final-reconciliation-v1/ci_host_guard.py package .`: 27 external locked crates verified; also exercised in the 22-test suite |
| Python lint | `/home/jjaff/AI-infra-simulation/rk-uarch/.venv/bin/ruff check --no-cache .`: passed |
| Shell syntax | `bash -n` on native-host.sh and native-container.sh: passed; workflow YAML parsed in the 22-test suite |

The exported tests use explicit pyproject.toml/root, no bytecode/pytest cache, cleared
PYTHONPATH/MYPYPATH/VIRTUAL_ENV/UARCH_HUMAN and recorded scratch M origins. For each test
batch, all 1,797 exported file bytes and modification times remained identical. Tests that
exercise source-write refusal use their own disposable descendants. Scratch exports and
pytest temporary trees were removed after checks, before publication. No source checkpoint
trees or whole-source manifests are delivered.

The 22-test suite admits both exact resident fixtures, rejects cold-state/profile/anchor,
uninitialized-source and production-scope misuse, and rejects D14 test-hardware production
relabeling. Independent arithmetic checks D02's 60000 ps and D14's 61000 ps versus wrong
61667 ps alignment. CI tests reject missing selection/modes/pins, wrong image/platform/path,
missing source, missing logs, failed release, empty tests and wrong tool receipts. One test
extracts only the shell logger function and verifies exact exit 7 plus stderr preservation;
it executes no container/native command. Synthetic successful logs are parser controls,
not native receipts. Author-script identity remains bound to the canonical fixture bytes.

The sole audit skip is real human new-policy generation/adoption. A's upstream archive
verification, cargo-deny current-policy refusal/proposed-policy success and coordinator
prior checks remain inherited evidence; B neither reran nor promoted them. No fresh external
claims, licence acceptance, image build/pull/run, Rust/native compilation/execution, oracle
generation/adoption, protected installation, hardware work, gate closure or independent-review
verdict occurred. Hosted CI is asynchronous and is not credited as passed by this package.
