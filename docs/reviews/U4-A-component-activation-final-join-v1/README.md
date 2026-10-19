# A final D3 retention correction and ordinary EOF integration

A accepts and resolves **B-ACT-D3-01 in the exact unapplied correction**. The installed source remains unchanged: no D3, protected ADR, default-route or checker amendment was installed. B's actual ordinary EOF consumer and test at `dec263861d8f00f1470d8efff943a5e76aad0145` are integrated normally. Their historical package is untouched. The remaining orchestration/capture join is tracked separately below; no native build is needed or performed for these preparation identities.

## Exact reproduced behavior and correction

Preserved D3 v6 hash `9e05fe88f24acbb0e8de381a9c3b4e350f667f0d5808dce03e859a9d10b824f5` saves consumer success before its final session-deadline check. When that check subsequently fails, the old saved receipt still says success. B's minimal correction wraps that last check, writes `validation_passed=false`, `failure_stage="session-finalization"` and `finalization_error=repr(error)`, then re-raises. A adopted those exact bytes as the additive v7 proposal: **`7054780cfccf7a5c893ab9bbec5ff1c6932de6d171104525e833195779f26a7a`**. No broader D3 semantic or authority change was made.

The test was written first against preserved v6. The synthetic call starts before expiry; the stub core saves its ordinary successful receipt, then the clock crosses the deadline at finalization. At the caller's exception boundary, the regression directly opens the file and requires the persisted failure, exact exception and unchanged stream/status sentinel. It asserts the second save occurs before propagation. Two paired controls return before and exactly at the deadline and require the original receipt bytes, one save only and no finalization error. These are wrapper/retention controls with a substituted private session class/core; they create no genuine session and invoke no native process.

| Executed control | Result and source attribution |
|---|---|
| Isolated v6 baseline |2 passed /1 failed. Expired case fails `assert True is False` on retained validation status at the exception boundary; both valid controls pass.|
| Exact B correction plus three affected B consumer controls |5 passed /1 failed. Correction persisted the right failure; the regression incorrectly expected `ValueError(...)` rather than the actual existing `HostBindingError(...)` representation.|
| Affected assertion correction |Only the exact exception-class spelling changed. Expired case rerun passes; the five unaffected passing cases are reused, not relabelled as one later six-test run.|
| Actual B consumer joins |Adapter/saved-output success, independently resealed session-finalization failure refusal, and D3 exact-envelope/same-code wrong-message discrimination pass with synthetic transport.|
| Focused static checks |Ruff and strict mypy for the new test pass. B's unchanged ordinary implementation/test lint, types,22-test batch and narrow comparator fault/restoration remain attributed to B.|

`independent-results.json` binds both test versions, exact implementation postimages and observed scopes. Isolated project imports are recorded in `evidence/*-origins.json`; D3 is loaded from the exact separate private overlay. Development and isolated red/failing outputs are preserved. No discarded failed test is counted as passing. No broad suite, old campaign, native fault sweep, startup launch or tracing was repeated.

## Actual B source and exact reconstruction

The31 leaves of B's final manifest `8066fb8201910e68e91c2fe89f41e02f0939ea99a6fd2e0f80b24fd57a643b6b` and its `reconstruction.json` SHA256 `af5bcb678078ff08b0f425efca2c7f08af1c3efabe01ae3e4cd08114a7636e4a` were verified before private application. Both actual B files match:

- `validation/component/ordinary_eof_acceptance.py`: `49e457b8a88852ea138da2159f68357eed39b1116f90402b72aeb930f3d5a359`.
- `validation/component/test_ordinary_eof_acceptance.py`: `e30cd15694cfab4886ed64e94e15950766abf358530f8cdd73701ca7fb19cf4d`.

`reconstruction-verified.json` records all five exact activation postimages. The unchanged runner is14e35b57…, checker e41d0baf…, and ADR ea3c9912…. D3 becomes7054780c… and preparation becomes **`b0addf0b150dead2842d2f53b9aaefacec9481f86b12bdbdefb895f711e1a6b4`**. A's original five-patch overlay followed by B's exact two amendments reconstructs those bytes. The concatenated route and standalone D3 full route independently agree. All applications occurred in fresh private directories.

The exact dec2638 current inventory has243 source entries /79 runtime-consumer pins. Its prospective activation overlay has244 source entries /80 pins. Both inventories were independently enumerated using the actual preparation rule and compared file-for-file with B's supplied records, not merely counted. The actual overlaid preparation tool was invoked only for `imports()`: it selected `docs/reviews/U4-B-component-activation-final-v1/activation-consumer-bindings.json`, SHA256 `c78e957c5f1de62afdb70f408135771eb72ad1d7b7c7495dd879c2a0ea31b9d0`. Its175 project/import inventory entries include the ordinary test as an inventory input; that test is excluded from the80 runtime-consumer pins. Its821 external files and accepted interpreter are unchanged inputs. No BuildInputs, generated engine, binary or runtime payload was created.

The preparation patch is explicitly relative to the unapplied activation overlay. The current non-D3 source is not redirected to an80-pin record claiming installed D3/default-route/checker bytes. Current source, prospective installation and historical binaries remain separate. This is not a silent replacement of A's78/79 or B's79/80 historical records. Any later B orchestration/capture files must have actual published bytes and an additive transition before entering a new inventory.

## B coordination and pending join

A's initial coordination publication is02c7d88; completed independent correction and evidence are published at `a2fe7c6e763dbdf5a0d5fa3991b7f230e353d84b`. B's actual early reply `1a27ee97d2aace483ad6ca69e513c8f843e9bdcf` is integrated. B reserved ordinary campaign and capture-monitor implementation/test paths, described the concrete adapter/cleanup protocol and promised exact final files. Those names are not inventory placeholders. No connected session route exists; published batches supply coordinator relay.

A agrees with the described direction: genuine existing session transport, null ordinary entry observations, independently frozen anchors and direct offline consumption, six-reference replay, task-local exact-owner cleanup after workers join, and explicit missing-binding/capture-loss refusal. The old private harness and old name-based trace monitor remain separate. A's image functions provide per-call/session behavior; ordinary case/global/retention enforcement and capture-monitor integration are B-owned actual-file joins, not claims made by the D3 wrapper correction.

## Boundaries

A-F3 remains deferred; the stopped startup-substitution/defense-revert activity was not retried, reconstructed or transferred. This task ran no startup check. Existing benign startup evidence remains under1f31669 and does not automatically cover future added source or establish integrity/immutable placement.

No Docker or native execution, activation build, tracing, new dependency, protected installation, deployment, genuine authority, public campaign or closure occurred. Historical runtime4d447ba binaries and all old packages remain unchanged. Construction capture remains NONE for4d447ba/46c5abb/cc899d2; the three candidate-03 gaps remain unresolved. Human L1, U0024, direction-independent /2 acquired-release restrictions, historical124/1368 schedule and unapproved120/1344 remain unchanged. B's author disposition is not an original-reviewer verdict or execution release.
