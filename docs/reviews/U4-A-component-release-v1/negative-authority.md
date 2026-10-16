# Negative fixture authority and refusal layers

Agreement with B's published 7ea3e1e/a5e5a98 interface: keep admission unchanged.
`profile.expected_outcome != success` stops at TestVariantNotAdmitted. That is a deliberate
public profile-rejection test and cannot count as exercising capacity, lifetime or transfer
semantics. Unit tests may directly call validate_resources, or explicitly supply separately
constructed SYNTHETIC success-context anchors to admit. Neither method confers human trust.
Stale identities, caller self-rehash under an old external profile anchor, and fully rehashed
semantic attacks under a synthetic new anchor are separate controls with separate receipts.

Real first-use inputs must bind exact invalid graph/point hashes in a separately reviewed
success-admission profile. The immutable external selection expects a specific resource
refusal. This uses existing admission semantics and no general flag. The reviewed profile
and registry hashes come from the independent host/build trust record, never request bytes.
This is sufficient for a future public Python component *preflight refusal* control; it
is not by itself proof that Rust saw the invalid input. Installed run_fixed_delay and
encode_request remain K2-only and validate before subprocess execution. Do not widen them.

To test independent Rust refusals at first use, propose this bounded mechanism as part of
the future scoped component runner release (not installed here): an immutable refusal
selection authenticated by the same reviewed component host/build trust. Each entry binds
case_id, raw canonical request byte SHA256, graph/point/profile/registry hashes, expected
engine/build/host hashes, expected error code and `dispatch_permitted=false`. Its record
format is `uarch-component-refusal-selection/1`, with entries sorted by case_id; every field
is required, duplicate IDs/hashes or unknown error codes refuse selection. Execution API
accepts a selection case ID, not a caller-supplied graph, hash, mutation recipe or trust flag.
Read exact reviewed bytes from the host manifest, compare all immutable bindings, retain
normal size/framing/descriptor/environment/timeout limits, then send those bytes to the
released component binary. Rust independently validates all fields and refuses before
allocating simulation state or dispatching. Record stdout empty, canonical stderr/code,
exit status, input/executable/host/selection hashes and zero dispatched jobs. Any success,
wrong refusal, partial result or activity is a failed control, never a native positive.

No authority file, runner or native code for this mechanism is created by this package.
Its exact bytes and allowed refusal vocabulary join the future reviewed component inputs
before execution. Existing tools/licences/runtime integrity rules remain accepted; only
this narrow negative transport mechanism and its exact selected inputs need acceptance.
If that mechanism is not released, retain public Python preflight controls and Rust unit
controls as distinct evidence and mark native first-use resource negatives not_run. Do not
relabel either as an executed native first-use refusal.
