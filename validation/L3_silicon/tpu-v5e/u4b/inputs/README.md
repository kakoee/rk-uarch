# Proposed exact data inputs for the approved scope

These are pre-measurement data, not predictions, device results or a new workload format.
The mathematical scope remains the same 52 units. No engine or functional tensor workload
was run to prepare them.

- [rotary-coefficients.json.gz](rotary-coefficients.json.gz) decompresses directly to the
  existing `uarch-rotary-coefficients/1` JSON carrier: positions 0..2047, R=128, FP32
  cos/sin bit rows, unscaled theta=10000. It supplies the proposed input choice already
  documented in the suite. Use its exact bits for split-halves Q/new-K rotation; do not
  regenerate coefficients during replay. Supply them as runtime data, not compiler-closed
  constants that can erase the selected rotary work.
- [gather-page-indices.json](gather-page-indices.json) supplies exact reverse permutations
  for p=16/32 and C=2048/2049. The two 2049 entries support already-required tail correctness
  tests; they are not additional timed benchmarks. One index table can address the separate
  K and V page arrays; account for its bytes once when that sharing is declared.

Coefficient content identity:
`sha256:f1c4afb20c16bb28329810d9a7786863ce21829fed9164bc8c1465e3b11947a6`.
The raw FP32 payload has 1,048,576 bytes; JSON/gzip sizes are transport overhead, not device
traffic. Full table residency is not implied by supplying it: stage the selected rows and
respect the model's local budgets. Decoder B=8/32 can share coefficient rows only through
explicit read-only mapping dependencies.

[prepare_inputs.py](../prepare_inputs.py) records the generation recipe: binary64
`position * 10000**(-2*j/128)`, Python/libm sin/cos, rounded to FP32 bits, then the existing
canonical content hash. These are explicit supplied approximate coefficients; no claim of
correctly rounded transcendental functions or named-model equivalence is made. A different
libm may generate different low bits, so the saved artifact is authoritative. `--check`
validates saved shape, finite bits, data identity, position-zero values, unit-circle sanity
and page arrays without regenerating the table. A changed table requires a new data identity.

The artifact's producer implementation_hash is the **existing** RotaryCoefficients carrier's
field, populated with the actual recipe source identity at creation. No new source-hash
registry/attestation is introduced. Runtime/replay validates supplied data; it need not
read this generator, its source tree, or build/review evidence. The gzip wrapper has no
new semantic contract. The unchanged installed RotaryCoefficients validator accepted the
uncompressed artifact during preparation; no protected carrier was installed.
