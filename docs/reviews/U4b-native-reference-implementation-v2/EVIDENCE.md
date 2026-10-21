# Bounded correction evidence

Executed locally by the correction author on 2026-10-21, against corrected source tree
`6b186db2dd90c09f97ba86282dfaaadd234da7cd`, unless explicitly labelled inherited below.
This is implementation evidence, not an independent recheck or device validation.

## Newly executed

| Check | Result | Record |
| --- | --- | --- |
| Original B1 on reviewed source | Existing production-isolation test fails on `importlib.resources` | [before-b1](evidence/before-b1.txt) |
| New B2 regression before guard | Both variants fail with `DID NOT RAISE ValueError` | [before-b2](evidence/before-b2.txt) |
| Focused arithmetic and new B2 controls | 5 passed, 26 deselected | [focused](evidence/focused.txt) |
| Relevant contract suites, including existing production-isolation test | 150 passed | [contract](evidence/contract.txt) |
| Existing everyday selection plus two B2 regressions | 62 passed, 2 large gather fixtures deselected | [everyday](evidence/everyday.txt) |
| Ruff over reconstructed source | Passed | [ruff](evidence/ruff.txt) |
| Both mypy commands | Passed, 109 source files and 39 contract-test files | [mypy](evidence/mypy.txt), [contract types](evidence/mypy-contract.txt) |
| Import-linter | 2 kept, 0 broken | [imports](evidence/imports.txt) |
| Original schema, reference schema and native reference carrier checks | Passed | [schema](evidence/schema.txt), [reference](evidence/refschema.txt), [carrier](evidence/carriers.txt) |
| New-guard-only ablation | Forgery accepted directly and by replay; both regressions fail; exact restore rejects forgery and both regressions pass | [receipt](evidence/ablation.json), detailed records below |
| Installed wheel from outside checkout | Resource loads; nominal CLI run byte-equals existing result; nominal and lawful synthetic replay pass; forged replay refuses | [receipt](evidence/installed.json), [control](evidence/installed-control.py.txt) |
| F3/F6 preservation probes | Both remain accepted, explicitly unresolved | [F3](evidence/f3.txt), [F6](evidence/f6.txt) |
| Fresh complete successor reconstruction | Exact tree matches; consolidated affected selection: 212 passed, 2 deselected (5.21 s) | [reconstruction](evidence/reconstruction.txt), [tests](evidence/final-reconstruction-tests.txt) |
| Source and review preservation | Exactly three changed source paths; 34 independent-review files byte-unchanged | [preservation](evidence/preservation.json), [review identity](evidence/review-manifest.json) |

The focused selection retains independent literal schedule expectations: 42 ps with two HBM
credits, 52 ps with one, and 41 ps with fractional service at 3 B/ps. These are synthetic
arithmetic expectations, not expectations fitted to the nominal campaign. B2 separately uses
the 42 ps lawfully scheduled result and a resealed 41 ps forgery under the same inputs.

Commands were run from `/tmp/rk-uarch-u4b-correction-v2`, a disposable reconstruction, with
Python 3.12.14 and the existing development dependencies. `PYTHONPATH=contract:src` selects
this reconstruction for source checks. `REFERENCE_NATIVE` and `ORDINARY_NATIVE` point to the
unchanged reviewed-source debug executable under
`/tmp/rk-uarch-u4b-published-build/target/x86_64-unknown-linux-gnu/debug/uarch-engine`.
The corresponding unchanged release executable is used for the installed nominal run.
No new native source or binary build is claimed. The final consolidated run used the same
contract and everyday selections together in `/tmp/u4b-b1-b2-final-review`, freshly exported
by this successor's helper; all 212 selected tests passed. This is a reconstruction check of
the affected selection, not a second campaign.

```sh
export PYTHONPATH=contract:src
export REFERENCE_NATIVE=/tmp/rk-uarch-u4b-published-build/target/x86_64-unknown-linux-gnu/debug/uarch-engine
export ORDINARY_NATIVE="$REFERENCE_NATIVE"
pytest -q contract/tests/test_u_p2_review.py contract/tests/test_u2_resource_isolation.py contract/tests/test_u2_schema_freshness.py
pytest -q tests/reference tests/unit/test_ordinary_native.py tests/native/test_ordinary_process.py -k 'not gather_2049'
pytest -q tests/reference/test_process.py -k 'dependency_readiness or literal_hbm_overlap'
ruff check .
mypy src contract/uarch_contract scripts
mypy --no-explicit-package-bases contract/tests
lint-imports
python -m uarch_contract.generate --check
python -m uarch_contract.generate_reference --check
python native/export_reference_carriers.py --check
```

The relevant installed tools came from the coordinator's existing `.venv/bin`; that checkout
was not edited. Use equivalent installed dependencies and a native binary built from the
unchanged proposed native sources to repeat these commands in another disposable tree.

## B2 guard ablation and boundary controls

The regression reproduces the reviewer's impossible schedule exactly, including its resealed
content hash; [parsed comparison](evidence/fixture-equivalence.txt) against the original probe's output passed. W arrives at
26 ps, yet the forgery records vector readiness 26 and start 25, with consistent downstream
activities, jobs, sequences, allocations and a shortened 41 ps duration. The legal result has
vector readiness/start both 26 and duration 42. The positive control also admits HBM reads
issued at readiness (11 ps) and after spacing (ready 11, issue 12); greater-than-or-equal is
intentional for that phase.

The [executed ablation driver](evidence/ablation-driver.py.txt) removes **only** the new six-line
`require(...)` guard. Variable bindings, other checks, native executable, fixtures and tests
remain unchanged. This is a semantic mutant, not a hash-only or malformed-output fault:

1. The original reviewer probe accepts the forgery through checker and ordinary replay:
   [ablated probe](evidence/ablated-probe.txt), exit 0.
2. Both new tests then fail specifically with `Failed: DID NOT RAISE ValueError`:
   [ablated regression](evidence/ablated-regression.txt), pytest exit 1.
3. The original checker bytes are restored in `finally`, verified byte-for-byte. Corrected
   and restored SHA-256 both equal
   `3e6f8383c587fe8a984e9deaa1dc27f1d87deb06022497cb5f1b68e3b1776e3b`.
4. Both regressions pass: [restored regression](evidence/restored-regression.txt).
   Both original-probe paths refuse with `IncompleteObservations: first activity dependency
   readiness`: [restored probe](evidence/restored-probe.txt). That probe exits 1 because it
   was written to demonstrate acceptance; refusal is the expected corrected outcome.

Each regression runs lawful → forged → lawful. No mutation remains in the successor.
The [synthetic schedule](evidence/synthetic.txt) and the copied reviewer-generated
[fixtures](evidence/synthetic/) allow direct inspection. They do not replace or modify any
saved nominal job or historical campaign artifact.

## Installed execution and replay

Built a new wheel offline ([build log](evidence/wheel.txt)) and installed it noneditable into
`/tmp/u4b-correction-installed` ([install log](evidence/install.txt)). Existing third-party
packages are reused via a `.pth` pointing to the development environment's site-packages;
project and contract module origins were asserted to come from the newly installed wheel.
The original model JSON loaded equals the wheel's regular packaged JSON. No checkout path
or `PYTHONPATH` selects the source tree.

The [executed control](evidence/installed-control.py.txt) asserts its working directory is
`/tmp/u4b-correction-installed-use`, outside a checkout. It uses the prior saved nominal job
without modifying it; the new ordinary CLI run is byte-identical to the prior result. Replay
imports are guarded before importing the shipped CLI: mapping and producer modules are
blocked, and PATH contains no `uarch-engine`. Nominal and synthetic lawful CLI replay return
0; the resealed forgery returns 2 with the new semantic refusal; lawful replay after that
fault again returns 0. [Receipt](evidence/installed.json) records module origins, exit codes
and hashes of the unchanged saved inputs/results. Basic data provenance is sufficient;
these paths and hashes do not introduce runtime authority or executable attestation.

## Inherited evidence, deliberately not rerun

- **Author campaign:** all 52 units in publication
  `0a5cebb9e81a2a382bcbaf4b9dfe5d13a2d2d58d`, including debug/release byte comparison,
  installed replay, state/priming controls and host-runtime breakdown. See unchanged
  [v1 EVIDENCE](../U4b-native-reference-implementation-v1/EVIDENCE.md) and its receipts.
- **Independent reviewer:** 14 units spanning all six classes, byte-identical jobs/results
  against the author campaign; the other 38 units were inherited by that review too. The
  reviewer's separate native 86 unit + 2 process tests, `fmt`, `clippy -D warnings`, two
  larger gather fixtures, arithmetic and decoder-role controls are inherited here.
- **F5 analysis and F4 CLI probe:** attributed to the independent reviewer, whose README
  SHA-256 is `1609d87bcc19e70faf201d25e0c3716ab28178a2d9a9548ca0c5d50301c70940`
  and serialization-analysis SHA-256 is
  `46a740effe4c99f7e57fb9e7c71cf7d4770d1441586eff9a8c97848935c89795`.
  F5's numbers are simulator-output observations, not device measurements or new author runs.
- Vendor, license, third-party, untouched Python suites and other historical controls are
  inherited only to the extent recorded in their existing evidence. No new pass is claimed.

The exact three-file delta proves native scheduling, mapper, model parameters, workload
selection, contracts, saved jobs and historical campaign evidence are unchanged. The checker
acceptance law is intentionally changed; its focused synthetic and nominal installed
controls are executed above. Historical outputs have not all been rechecked by the new
checker. The reviewer's proposed dependency-law probe separately accepted seven nominal
results; that observation is inherited, not a claim of 52 new checks.

No full Python suite, all-52 campaign, performance optimization, device access, measurements,
spending, CI polling, protected installation or U4 closure was performed.
