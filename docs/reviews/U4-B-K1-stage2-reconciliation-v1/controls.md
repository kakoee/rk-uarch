# Stage 2 inventory, replay and fault controls

The twelve-path subject is unchanged. The following control inputs supersede the historical
K1 inputs only for a future explicitly selected Stage 2 verification run. They do not overwrite
old evidence, select a new live inventory or claim native results in this session.

| Control | Exact reconciliation |
| --- | --- |
| Test discovery | 28 unique names, multiplicity1 in each mode; compare complete Counters, not a count-only check |
| Full execution | Actual pass names must equal that inventory; no failing/ignored/empty/filtered selection qualifies |
| Replay | Same one exact test, prefix and file sink; six fresh nonempty equal payloads, plus SHA256 `4490d63cd5b49bac327ded1661df7802356f541e003391666963965809f2a62a` |
| Semantic faults | Eleven current anchors in faults.proposed.json; preimage hash and unique anchor must match before mutation; exact test appears once |
| Release-only replay drift | replay-mutation.proposed.json rebinds simulation.rs from `58b02d87…` to `472698e6…`; replacement and test are unchanged |
| F5 host linkage fault | Needs newly captured full Cargo metadata; do not substitute roles.json, omit the test or accept a missing environment variable |
| Historical generic failures | Preserve missing-source, compiler/runtime failure, empty/ignored/filtered selection, absent cache/toolchain, Unicode refusal and restoration controls; prior native runs are inherited |

B's old `controls.py` accepts explicit semantic fault data, but its final call into
`replay_control.py` still loads the historical replay-mutation.json by its own PACKAGE path.
It also expects older `.stdout`/`.canonical` receipt names and `verified.json`; the new
post-install helper deliberately does not manufacture those receipts to unlock that driver.
**Do not invoke the old driver unchanged against Stage 2.** Its hash refusal is correct.
The source-hashed Stage 2 fault plan is ready; integrating a future native driver must consume
these explicit inputs and the new run's genuine receipts. No native adapter is claimed tested
while the runtime is unavailable.

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
All eleven current pairs were verified against A's saved logs; none was rerun here.

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
pass. Without the real metadata, only the independent README check can run; this session did
not rerun the graph-dependent F5 failure/restoration control.

These are execution requirements and proposal inputs, not a current failure-campaign pass or
an independent software verdict. The same reviewer retains Stage 3 authority, including the
retroactive-insertion probe expectation and the private noncausal predecessor-list option.
