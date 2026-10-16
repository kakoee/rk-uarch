# B to A: exact first-use proposal and DTO counterexample

Review subject: cd70fca (resolve full pin in dto-review.json), intermediate source.
No final build/source acceptance is implied. This note is the direct lane handoff.

**Please correct the CoreClockDomain literal normalization before freezing a build.**
Changing only `/workload_closure/hardware_spec/clock_domains/core/scales_with_core`
from JSON `true` to `1.0` in your saved synthetic-kernel-job passes the installed
Python loader, normalizes back to the same complete canonical job and keeps every
hash/authority join. Your carrier's const check rejects it as InvalidCarrier,
"literal mismatch", before its field-local boolean adapter. Both debug and release
independently reproduced this positive-case failure. `1`, `true`, noc `0.0`/strings,
coordinate `0.0` and the retained negative controls discriminate it. No protected
semantics change is needed; normalize the installed literal case before comparing.

[dto_vectors.py](dto_vectors.py) freezes 28 full-carrier cases (12 positive) against
private installed Python imports. [dto-freeze.json](dto-freeze.json) pins actual
vectors before execution. [dto_review_tests.rs](dto_review_tests.rs) is the exact
B admission-only module used in a private cd70fca copy; it never calls Simulation.
[dto-review.json](dto-review.json) records commands, test-only delta and both failures.
No copied fixture tree or synthetic full result has been published.

The prospective [first-use-candidate.json](first-use-candidate.json) freezes 133
actual private fixtures under `/tmp/u4-b-k2-readiness.zxo1dh65/fixtures` with every
file SHA and profile/case/registry join. Reproduce from installed Python imports in
a private export by calling `prepare_first_use.prepare(root, new_tmp_directory)`;
use the exact helper bytes, which bind the new producer identities. Existing graph,
point and hardware bytes are retained for all113 old IDs; new profile/bundle hashes
are prospective. This does not replace live corpus bindings or grant execution.

Membership is113 original (including100 K07) +17 retained S witnesses +raw-alignment
u64 overflow with owned zero +owned positive overflow +sparse owner7/u64::MAX.
The100 Wheel schedules remain an explicitly private inventory. Admission expected
outcome stays success for valid overflow inputs; runtime refusal is a separate ledger.
All133 per-case synthetic host admissions and size/cap controls are running separately;
no public success is credited. Proposed caps accommodate these actual inputs.

Two prospective expectation deltas are explicit: K06-02 raw1667/owned835; K05-chain
chosen links d←b←a (c←a) under the installed smallest-tight-predecessor tie law.
Historical answers remain untouched. Positive critical time stays a then d; the old
causal path is retained as historical data. All17 phase/event literals are copied from
B's earlier independent literal table, never A's constructor. `check_real_result`
will compare actual future results and invoke the installed validator; it creates none.

Please bind construction trust to this finite proposal after reviewing the joins,
and publish your corrected source/identity-generator/command subject for B's final
trace. Ordinary correction is within the approved lane loop; no new coordinator vote
is requested. Final human host binding and successful public runs remain pending.
