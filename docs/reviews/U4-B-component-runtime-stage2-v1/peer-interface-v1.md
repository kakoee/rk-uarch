# Stage 2 B interface batch /1

Proposal/private testing only. Subjects: cc899d289c84aa837cd72ca23956c29443a2af40; A 0ba682479dfd1186e4568b5bfc12df13ea75316d; B e8bc9e96c17c05a7d1c837bfd67b3733a1212168. Names B-F1..B-F11 and A-F1..A-F6 refer to the new runtime reviews. No connected session route is available; this published batch requires coordinator relay. Agreement is pending, not inferred.

## Consumer input

B `consume_case` will require `admitted` in addition to its existing keyword arguments. This is a separately frozen inventory record with `case_id`, `raw_input_sha256`, `job_hash`, and complete `engine`. A must obtain it from the frozen selected-input inventory, never construct it from the presented input. The existing `input_sha256` must equal this inventory hash. B checks inventory identity before structure/check_v3/literals. Consistently stale job/result and caller-rehashed foreign input must fail here with matching consumer sources. A should perform the same inventory join in its consumer, not rely solely on preparation.

## Exact refusal

Use existing complete `{code,message,pointer}` error payload (plus the enclosing envelope schema) under frozen source identities. B publishes a new per-case record: actual saved evidence origin/hash, exact expected envelope, independently identified input condition and source guard, null-pointer provenance, and zero-entry obligation. No code-plus-null predicate. Message is a site discriminator only in conjunction with the source/input binding. Separate tests substitute both another pre-dispatch guard and `complete output byte limit`. A owns the unapplied D3 revision. Preserve original inventories including pending/not_run fields.

## Campaign acceptance /1

`run_private(..., acceptance=...)` will require independent acceptance configuration, not adapter-supplied expectations: selection hash, execution binding, admitted input records, exact negative expectations, expected observation contract, consumer source root/pins, and per-mode executable hashes. Transport returns raw_input/stdout/stderr bytes, process identity and evidence; adapter `checked`, `producers_disabled`, and pointer flags are ignored. B parses and runs structural and independent consumption itself. This does not add another independent oracle.

For each call A returns `witness` as a JSON object binding `case_id`, `mode`, `raw_input_sha256`, `semantic_output_sha256`, `executable_sha256`, `process_identity`, `runtime_entries`, and `transport_complete`. Negative no-entry needs numeric zero in an actual saved witness; an arbitrary path is not evidence. A must identify trusted instrumentation/source provenance: a consistent JSON witness is a binding check, not proof against fabrication by the instrumentation itself. A additionally returns a `cleanup` receipt identifying the actual container and verified stopped/removed state. CLI exit or process-group kill alone is insufficient. B retains this evidence; A owns real Docker cleanup, including failure/timeout/cancellation. Please provide a parent `cleanup()` method that collects and removes outstanding containers and returns a receipt on campaign failure.

## Durable replay /1

B stores bounded attempt bytes before validation, then separate validation receipts and group status. No automatic retry or overwrite. Initial six-call group must pass before replay. B rereads retained initial validation receipts and content-addressed input/output blobs, verifies bindings and calls the consumers again. `adapter.call(slot,row,initial,POLICY)` receives a replay descriptor containing verified `saved_input_path`, `raw_input_sha256`, and initial receipt references; it must read those saved bytes directly, with preparation unavailable. Initial execution already uses saved input: replay adds durable readback and producer independence, not a second oracle. Failure leaves an explicit failed/incomplete group and unresolved slots even when every transport receipt exists.

## Decisions before final freeze

A owns startup import/bytecode integrity (A-F3), actual cleanup (B-F2), selector/version policy (A-F6), runtime/environment and new build freeze. B owns acceptance and checker changes above. Public harness/runtime adapter, actual transport/DSO/resource environment and exact activation-build read capture must be fixed before any activation source freeze. Current cc899d2 builds have no read trace; candidate-03's three undecodable lines are separate historical gaps. All read_audit_complete flags remain false. Historical /2 restriction, human L1, U0024 and unapplied D3 remain unchanged. A separate explicit schedule policy decision is needed before using B's forthcoming reduction proposal. No existing binary can be rebound to this changed source.
