## Build provenance scope amendment — prospective human installation

This amendment implements Javid's direction to reconsider exhaustive construction-read
tracing while preserving build identity, testing and reproducibility. It replaces the
mandatory construction-read-capture prerequisite introduced in later U4 preparation
proposals; it does not retrospectively alter their receipts or verdicts. Until human
installation and the reviewed implementation transition, existing executable gates remain
in force. A historical requirement preserved in an older proposal is not a competing
requirement for the successor prepared under this amendment.

### Required build and result provenance

For a new admitted native candidate, retain an exact source commit/tree and declared
source inventory, generated-input bytes and their producer identities, locked dependency
versions/checksums/features, compiler/linker and image identities, and complete per-mode
build commands and explicit environment. Build from a clean source export into fresh
build-output directories using the accepted tools and verified dependency cache. A cache
of verified dependency source archives is reusable; an unexplained prior target directory
is not clean-build evidence. Record success/failure, exit status, ordinary stdout/stderr,
resource/deadline outcomes, actual executable hashes and generated output identities.
Do not silently substitute tools, dependencies, generated inputs or build flags.

Each run binds the actual executable and relevant Python consumer identities, workload,
hardware, assumptions/model and input identities, result bytes and executed checks. Future
product tables bind their run/result records and preparation/assembly implementation.
The provenance chain is table/result -> run -> executable -> build record -> source and
inputs. These records attest declared inputs and observed outputs; they do not prove an
exhaustive dynamic read set or independence from all ambient state. No self-authorizing
build receipt, test-supplied identity or fabricated human/reviewer acceptance is permitted.

Retain scope-appropriate native/Python tests, independent expectations and consumer checks,
semantic fault/restoration controls, producer-disabled saved-input replay and required
fresh-process/debug-release result determinism. Reuse unchanged evidence only with exact
identity and scope justification. Clean rebuild verification is required for a claim of
binary reproducibility: compare actual executable hashes from independent fresh-output
builds of the same declared inputs/mode. Existing qualifying evidence may be reused;
there is no repeated-build requirement for documentation-only changes. A mismatch must be
investigated and reported, not normalized away or called bit-reproducible. Debug and release
executables may differ; their comparable simulation results must meet existing determinism
requirements. No exhaustive tracing is needed for this bounded reproducibility evidence.

### Exhaustive construction tracing is optional

Compiler/build-script/linker syscall tracing, canaries, construction-read closure and
trace-specific diagnostic classification are optional investigations, not prerequisites
for U4 build provenance, component activation or table provenance. This removes the added
mandatory gate rather than deferring it to an automatic later sprint gate. A future need
for stronger assurance requires its own justified scope and authorization.

Preserve all historical trace files, NONE CAPTURED statuses and unresolved candidate-03
records. Never set read_audit_complete=true on the strength of this amendment. Separate
future build-provenance acceptance from optional read-audit status and from runtime startup
assurance through an explicit reviewed record/consumer version transition. Reject stale,
missing or mismatched required provenance; merely deleting the current boolean check is
not an implementation of this policy. Current K2 records/authority are not migrated.

Ordinary compiler progress and warnings are retained build diagnostics, not evidence of
tracer loss and not automatically build failures. Keep actual compiler exit status, Cargo
completion/artifact checks where applicable, lint/clippy warning policy, resource/deadline
limits, complete bounded output retention and failure receipts. A truncated or incomplete
required receipt cannot become success. The proposed empty compiler-stderr allowlists and
per-line tracing-policy approval are not part of the ordinary build gate. Optional tracing
must still report its own unknown/lost/incomplete evidence honestly; do not weaken an old
trace parser to manufacture a pass.

### Boundaries that do not change

This amendment does not change simulator event/resource tracing or required runtime
observations. It preserves exact executable/consumer selection, input/result admission,
independent result checking, D3 refusal semantics, immutable deployment and genuine human
authority. A-F3 startup-integrity assurance remains a separate unresolved public-first-use
gate. No stopped verification is retried, reconstructed or transferred by this amendment.
Trusted startup evidence cannot be inferred from a source hash, a clean build or a positive
simulation run. Genuine L1 workings, the affected /2 restriction, incident disclosure,
U0024 obligations, reference readiness and U4/G3a closure requirements are unchanged.
No installation, native build/run, deployment, campaign or new authority is authorized by
preparing or reviewing this amendment.
