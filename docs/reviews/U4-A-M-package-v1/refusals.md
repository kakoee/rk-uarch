# Refusal controls and limits

All tests are inside the proposed `contract/tests/mapped/test_admission.py`. Fixtures are
input documents, not observed native outputs. Mutations targeting semantics reseal graph,
point and bundle, so a stale hash cannot accidentally satisfy the intended assertion.
`validation.json` records the exact commands and source origins. No subprocess native test
has run. Pydantic schema errors precede named admission errors where applicable.

| ID | Executed schema/prototype control | Later runtime obligation |
| --- | --- | --- |
| R01 | /1 and /2 refused by MappedEngineJob; old job roots refuse /3 | native parser returns UnsupportedProtocol |
| R02/R03 | authenticated complete original v1/v2 closure reaches UnsupportedWorkloadScope | repeat via native boundary; no model admission |
| R04 | fp16/fp32/fp8 and mixed X dtype refuse | named operand in public error |
| R05 | TP8 rehash refuses; old RankScope forbids unknown PP/EP/CP fields | public rank rejection |
| R06 | normalization, kv_write and valid attention_fused rejected as UnsupportedOperator; v1 rotary rejected by existing enum | repeat admitted-schema operator cases publicly |
| R07 | steady/priming outside component matrix refused | profile-matched negative state cases at public boundary |
| R08 | K257/M1025/imported padding rejected; 1/16-op positives and 17-op schema refusal | repeat shape boundary cases in mapper/native |
| R09 | unknown policy, output_stationary and multicast rejected | alternate dataflow/mapping public cases |
| R10 | out-of-SRAM range, live alias, bad bank, absent second slot and false last-consumer inventory refuse | allocator lifetime/fault observations |
| R11 | core4, missing XY hop, wrong channel and an unsplit stripe crossing refuse | actual routing/fragment resource checks |
| R12 | dangling/self/cyclic dependency and duplicate coverage refuse | event scheduler refusal before events |
| R13 | stale graph, hardware mismatch, missing assumption join, v2 coefficient tamper | native canonicalization and full runtime closure |
| R14 | explicit requested point/hardware mismatch refuses | loader never rebuilds/retargets input |
| R15 | fixed delay in component and verification-only product admission refuse | all prepare/table/report paths wired to shared eligibility |
| R16 | incomplete output projection, malformed/nonfinite JSON and missing required result shape refuse | crash/timeout/malformed output durable error, null result/not_run; wrong job hash against real positive result |
| R17 | subsystem fidelity on fixed-delay job refuses; strict B literal vector and boolean checks | B public UnsupportedFidelity matrix |
| R18 | correctly rehashed different production hardware refuses | native whitelist and profile independent checks |
| R19 | work_repeat2/paged layout and unknown cancellation/retry/spill/bias/sparsity fields refuse | repeat exact capability variants through native parser |
| R20 | missing observation carrier/result fields refuse; complete result shape has no optional observations | each required section/record mutation against actual observed positive K2/B output |
| R21 | zero frequency, negative/boolean delay and u64 overflow refuse; zero-delay input valid | checked next_edge overflow and owner-granted zero behavior |

Additional controls: duplicate JSON keys, unknown fields, bool/string/nonfinite count
coercion, profile/case/seed mismatch, untrusted authority hashes, registry tamper, registered
test spec on production path, job-only clock setup drift, generated-schema freshness and
read-only stale-schema detection. Canonical vectors include UTF-8, negative-zero normalization,
small exponent spelling and u64. Rust has not yet reproduced them.

The disposable enforcement-off control disables only the prototype `require` refusal helper:
R04/R09 must fail with DID NOT RAISE; original and restored code must pass. This demonstrates
that these admission tests discriminate the selected enforcement failure. It is not a
native timing/count mutant, independent B verdict or fault-campaign completion.

Preserved legacy: old carrier, schema, initializer and analytic implementation bytes are
not in the patch. Existing v1 prepared replay plus v2 strict/capture/replay/adversarial tests
run in the export. Future model mapping and full result fidelity/causal checks are explicitly
runtime work, not passed by the structural/prototype suite.
