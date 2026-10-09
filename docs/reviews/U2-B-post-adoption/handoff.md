# Post-adoption B correction handoff

**AD-C1 ready for coordinator reconciliation; AD-C2 remains an active failure with an unapplied correction proposal.** All work is uncommitted. This is not a green full-suite claim, model-accuracy verdict, final U-REVIEW, publication or sprint closure.

## Verified receipt and preservation

Entry verified the previous B 20,564-entry manifest `e688d9aebb39b3fd0fda0d93c602cb4bc9ede80e6b2026c7a7fbdb85e14bbdfb` and captured 20,864 pre-existing paths in `entry.json`. `preservation.json` rechecks 20,857 unchanged paths, exactly seven authorized test modifications, no deletions, and unchanged old handoffs/reports/manifests/ledgers. Exact originals of all seven tests are preserved under `original-tests/`. Six modified tests were members of the previous changed-path manifest; the seventh previously matched tracked HEAD. Neither historical manifest was rewritten.

Verified received identities:

| Receipt | Raw SHA256 |
| --- | --- |
| Real adopted 48-file manifest, integration canonical and preserved generation candidate | `2d15afd7dd80124f70d387bc7cde4addda29162cd49370d40da7b99830709b44` |
| Previous 20-file manifest, both preserved/displaced integration copies and B canonical | `b3a575d0e3f27a4057678a2298609a580fd5a5e1dd858b0f4af086f2dc9e0e1d` |
| Approved input manifest, all members rechecked | `81df43c063396c89bd3333f43957c71efc7087cfa65b2a401177f2227fca8898` |
| Historical 299-file source manifest, all integration members rechecked | `8457d0607baf0af08c0b6d1c6eead00e141e778f6fd501d8869d9ae5eaadf443` |
| Received administrative adoption ReviewRecord | `4aad401c01a828a1463853796c38c19c20359f4649e2c706880c6e8a1cdcdbcf` |

`receipt.json` hashes the received acceptance/execution summaries, human-pair preflights and evidence logs. Administrative adoption is exact artifact acceptance, not model validation or independent final review. **B's canonical vendor remains the old 20-file snapshot.** All current-adopted validation below ran in the isolated combined integration tree named by `stage-path.txt`, not against B's old canonical vendor.

## Implemented AD-C1

`AD-C1.patch` and `AD-C1-delta.json` give exact old/new bytes for the seven assigned modules. New B test source is only `contract/tests/historical_snapshot.py` and `contract/tests/test_u2_historical_snapshot.py`. The complete 20-file `tests/fixtures/u2_b/historical-u1/` is received historical data, byte-for-byte equal to both preserved originals; no B oracle generation. The administrative review fixture is likewise exact received data.

The helper checks the pinned raw old manifest, exact 20-file inventory, every member hash and absence of symlinks in member paths on every call. There is no ambient fallback. Historical 864-row/two-refusal assertions and the old fingerprint expectation remain unchanged. Historical orchestration uses an explicit function-scoped binding only for requesting tests; the production historical identity guard is unchanged and independently refuses the current canonical manifest before the candidate executes. Relocated copies work without another worktree or archived review directory; changed/missing/extra/rehashed members refuse.

Refresh builders now begin from this declared historical source, retain 864 genuine historical expected rows and add exactly 144 independent synthetic H1 premises. The tooling-binding builder also starts from the historical snapshot, then retains its original independently authored **1008 synthetic matrix literals** (144 H1); it does not claim those literals are 864 authenticated oracle answers. Both retain exactly 1008 unique rows, four explicitly synthetic direct events, their synthetic marker, joins, negative controls and oracle traps. New tests redirect ambient `ui.ADOPTED` to an absent sentinel and demonstrate that neither builder depends on it. No copytree collision workaround or 864→1008 historical assertion change was used.

Complementary tests inspect the exact real adopted 48-file canonical snapshot: 1008 unique rows, 504 prefill/504 decode, omitted vector counts and unknown decode writes preserved; four actual refusal pairs with exact callable/component/PIN/execution/exception/boundary joins; and the hash-pinned real administrative ReviewRecord. Raw inspection still says `adopted=False`; authority is separately validated against the received record. These checks do not manufacture accuracy authority or infer real timing evidence.

## Executed validation

Commands, environment and return codes are in `tests-before.json`, `focused-checks.json`, `full-suite.json` and `broad-failure-recheck.json`; exact reproduction scripts are saved as `.py.txt`. All pytest runs use the existing main venv, `-B -p no:cacheprovider`, `PYTHONDONTWRITEBYTECODE=1`, explicit source paths and temporary cache locations. No dependencies were installed.

| Check | Observed result |
| --- | --- |
| Tests first, before AD-C1 fixes | 42 passed, 13 failed, 40 setup errors: nine original AD-C1 failures, two new isolation regressions, active AD-C2 and one omitted staging policy document |
| Focused seven modules, new controls and strict snapshot suite | **101 passed**, including all six strict snapshot gates; no setup errors |
| Complete integration suite, run once | **966 passed, 14 failed, zero setup errors**, 223.02s pytest time |
| Only the 14 failed nodes after copying omitted exact staging inputs | **13 passed, one failed**, 1.32s; remaining failure is AD-C2 |
| Final per-case disposition across full run plus targeted recheck | **979 passed, one active failure, zero setup errors/skips/xfails**; not a single 979-pass full-run log |
| Ruff on all nine changed/new test/helper files | Passed |
| AD-C2 unchanged B and staged guard reproductions | Both fail at `proof_raw.py:13`, as expected |
| Unapplied AD-C2 prototypes | 21 guard cases pass; both directory and ZIP helper layouts decode all six members identically and refuse a missing member |

The 13 extra broad failures came from my incomplete temporary-tree inputs: prompt/build-spec/license/CI/review documents, proposed schema, and an exact recorded capture artifact. `stage-missing-inputs-receipt.json` records each copied integration byte and the missing capture identity. No source or test was changed to recover these cases. Original red/full logs remain. The final 606-file staging inventory identifies received integration A/B lineage, real adopted data, historical data and B test overlays separately. The inherited proof/report-adapter/A2 fixture-path adaptations remain intact. No entire reviews archive was copied. Passing broad cases were not rerun merely to obtain a cleaner summary.

## AD-C2 concrete choice, still unapplied

Recommend **option A** in `AD-C2-proposal/decision.md`: allow only the exact unaliased `importlib.resources.files` import in the exact reviewed `proof_raw.py` path and complete raw file hash. All dynamic/import/vendor prohibitions otherwise remain active. This pins the existing fixed local package and six-member JSON loader; any source change, including a comment, requires renewed review. It is a conservative source guard, not a defense against arbitrary obfuscation or hostile Python environments.

Option B removes the import by storing exact six-member raw JSON bytes privately in source, preserving supported JSON values and directory/ZIP behavior while leaving packaged schema files untouched. It incurs source duplication and requires a byte-parity regression plus a new support/input reconciliation. Exact unapplied patches, old/proposed hashes, malicious/foreign/dynamic negative cases and helper-only packaging results are supplied. No wheel was built/installed; real wheel packaging and selected-patch integration checks remain required after reconciliation. The actual guard and production source are unchanged. No exception is approved by this handoff.

## Freeze impact and remaining work

All **84 generator-bound support paths remain byte-identical** in B, integration and the combined tree; all approved input members remain identical. No `src/`, `scripts/`, shared carrier/schema, hardware/policy, runtime helper, generator/adopted artifact or fingerprint metadata changed. The seven AD-C1 tests are supplemental members of the historical 299-file inventory: their exact affected membership/hashes and proposed helper/data additions are in `freeze-impact.json`. The combined tree has exactly those seven changed frozen members. B's two pre-existing proof/report-adapter path differences from integration are explicitly recorded, not new authorship. Option A would change one more supplemental test member and no support member; option B would change one member of both. Coordinator should review a new supplemental inventory after selecting any guard correction; the existing source freeze, human pair, input digest and adoption receipt stay historical and exact.

Received coordinator execution: real nominal 1008 compatibility_pass, zero nominal errors, evidence refused from actual precision refusals; physical 1008 = 96 H1 executions, 48 actual capacity failures and 864 not_run. Physical producer-disabled replay reproduced 3308 artifact files plus three top-level nominal/physical/inventory JSON files, while nominal still executed. Real default report completed with exit 0 in 440.068s: 24 rows, 40320 ratios, 46296 recipes, 14904 sources. These are received results, not newly executed B full-runtime checks.

The prior complete **synthetic-reference** report checks remain preserved with their original limitations. The next bounded real-report completion must use the exact adopted package to exercise opt-in/STUB behavior, repeated default/opt-in byte equality, full replayed package/report equality with producer traps, and full-size capability refusals. This task does not claim those exits or B-F16. Retained physical HardwareSpecs/full physical matrix; independent real measurement/history/compiler/collector/nonempty-energy evidence; final reviews, publication on main, published-commit CI/cold clone and closure remain pending. Known-empty energy consumption in this analytic engine produces no energy quantity or positive energy verification. Not_run, modelled absence and capacity failure remain distinct from passes.

`preserved-case-dispositions.json` is an exact copy of the prior independent ledgers; `case-dispositions.json` adds this checkpoint's observations without promotion: B64 52 executed/12 pending, proof 13 executed/42 superseded/73 pending, BP1 six entries separately retained. Estimates remain **256–400 engineering hours**; these validation times do not justify a revision.

`authorship.json`, `path-inventory.json` and `checkpoint-files.txt` identify the complete old/new delta and received versus new B work. `SHA256SUMS` covers the complete current changed-path set, excluding itself. Proposed checkpoint message: **Isolate U2 historical test data after adoption and propose narrow resource guard correction**.

Stop for coordinator reconciliation. No stage/commit/push/tag, new oracle generation/adoption, human flag, dependency installation, agents/messages, cleanup or A/integration/main edits occurred. Hashes identify bytes; this uncommitted work is not protected by branch history.
