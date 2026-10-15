# Stage 2 inventory, replay and fault controls

The twelve-path subject is unchanged. The following control inputs supersede the historical
K1 inputs only for a future explicitly selected Stage 2 verification run. They do not overwrite
old evidence or select a new live inventory. The restored-image results below are new local executions.

| Control | Exact reconciliation |
| --- | --- |
| Test discovery | 28 unique names, multiplicity1 in each mode; compare complete Counters, not a count-only check |
| Full execution | Actual pass names must equal that inventory; no failing/ignored/empty/filtered selection qualifies |
| Replay | Same one exact test, prefix and file sink; six fresh nonempty equal payloads, plus SHA256 `4490d63cd5b49bac327ded1661df7802356f541e003391666963965809f2a62a` |
| Semantic faults | Eleven current anchors in faults.proposed.json; preimage hash and unique anchor must match before mutation; exact test appears once |
| Release-only replay drift | replay-mutation.proposed.json rebinds simulation.rs from `58b02d87…` to `472698e6…`; replacement and test are unchanged |
| F5 host linkage fault | Needs newly captured full Cargo metadata; do not substitute roles.json, omit the test or accept a missing environment variable |
| Historical generic failures | Preserve missing-source, compiler/runtime failure, empty/ignored/filtered selection, absent cache/toolchain, Unicode refusal and restoration controls; now rerun on the exact proposal |

B's old `controls.py` accepts explicit semantic fault data, but its final call into
`replay_control.py` loads the historical replay-mutation.json through PACKAGE. The tested
[native_check.py](native_check.py) calls the unchanged `construct.verify` to produce genuine
`.stdout`/`.canonical`, metadata and verified receipts. It passes the eleven Stage 2 faults
explicitly. For replay, it clones only the existing execute function's globals in memory,
pointing PACKAGE at a newly written private copy of replay-mutation.proposed.json. The
function code, mutations, failure assertions and all exported source bytes are unchanged.
It sets seed41011/cases256 for native commands. A's diagnostic fields are literal substrings;
the adapter applies `re.escape` when passing them to the old regex consumer. It additionally
requires exit101, the exact selected FAILED row and one-failure summary, plus `foreign owner
mutation` in debug or `ForeignOwner` in release for the F1 controls. The prior literal/regex
refusal and all successful preceding cases are retained in native-prefix-campaign.json.
No historical controller or evidence is edited.

Run the owned reproducer from normal B main to check the exact unapplied proposal:

```bash
python3 -B docs/reviews/U4-B-K1-stage2-reconciliation-v1/native_check.py
```

The source remains base-plus-two-patches; this invocation never claims an installed commit.
The separate post-install helper uses native-container.sh receipt names and still emits
`fault_campaign_pending: true`: do not pass those different receipts to the old driver.
For the future installed commit, `construct.verify` on that same guarded private export
can create the driver's real predecessor receipts in a fresh receipt directory, followed by
the same explicit-input adapter and campaign. Preserve the installed source binding and
review that integration before declaring the installed inventory qualified.

The concrete native command for each named fault is the same baseline/fault/restored selection:

```text
cargo test --locked --offline --all-features --target x86_64-unknown-linux-gnu
  [--release only in release mode] --lib <fault.test> -- --exact --nocapture
```

Use each actual `fault.test` and exact `before`/`after` from faults.proposed.json. For each mode:
verify source hash/one anchor; run a passing baseline; mutate only a separate disposable export;
require exit101 and the named diagnostic from a real test failure; restore bytes and mtimes;
use a fresh target directory for the restored positive. Require one selected test in both
positive logs. A compiler failure or unrelated exit cannot substitute for the intended fault.
The saved A campaign supplies 22 individual baseline/fault/restored triples. The new B
campaign uses the full debug/release baseline suites, then 22 faults and 22 individual
restored positives. Keep these two execution shapes distinct.

For release replay drift, the source-hashed replacement appends a space only in release.
Run the exact replay test; require its genuine test pass and a fresh file sink, then require
six-payload/hash comparison to refuse the altered release bytes. Restore source bytes/mtime,
build into a fresh target and require the exact expected payload again. Old equal bytes are
insufficient: a new six-way equality check alone would not detect a stale expected payload.
The future post-install helper therefore checks both equality and the Stage 2 expected hash.

For generic failure controls, use the existing guarded `mutation`/`failure` logic as the reviewed
reference, but bind its source, inventory and receipts to the new run. Missing sources, compile
error and real failing test must preserve nonzero command receipts and intended diagnostics.
Empty/ignored/filtered Cargo invocations may exit zero; their parsed test inventory must refuse.
Offline-cache and unavailable-toolchain probes must not gain network or auto-install fallback.
Complete restored debug/release positives and source isolation follow every campaign.

For F5, the full actual metadata graph and its binding must already pass. In a temporary copy,
change the register runtime classification or README binary description using A's exact saved
fault anchors. Require the named Python test's intended assertion failure, then restore and
pass. Both controls now passed with newly captured real metadata; see linkage-controls.json and
linkage_controls.py. The graph-dependent check is explicitly selected, and imported test
modules must originate in the private export.

These controls provide bounded proposal evidence, not an independent software verdict. The same reviewer retains Stage 3 authority, including the
retroactive-insertion probe expectation and the private noncausal predecessor-list option.
