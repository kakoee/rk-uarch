# Bounded reconciliation proposals — not applied

Dependency inputs remain the exact Javid-approved candidate. The C2 experiment has returned
actual counterexamples, not grounds to broaden versions or claim public K2 readiness.

## Typed-carrier follow-up

Keep all existing vectors and ten failures. A future separately reconciled probe revision
can stay on the same manifest/lock; no new dependency is currently proposed.

1. **NumericLeaf rational union:** derived serde untagged dispatch rejects even
   `{"path":"test.rational","value":{"numerator":0,"denominator":1}}`; all seven
   rational-union vectors fail, while direct RationalValue parsing passes through u128 max.
   Propose an explicit token/type-directed small-carrier visitor: recognize the exact
   rational object shape, reject unknown/duplicate fields, consume numerator/denominator
   as integer tokens without an f64 or serde untagged Content intermediate, enforce u128
   bounds/positive denominator/gcd1, and retain explicit scalar bool/string/null branches.
   Keep the caller numeric-marker guard. Review that visitor and repeat all vectors before
   proposing any native DTO implementation; do not infer direct-u128 success proves union success.
2. **Integer `-0`:** installed strict_json_loads produces integer0, accepted by the strict
   u128 adapter; serde's direct u128 decoder rejects the minus token. Propose preserving
   lexical integer-vs-float classification while treating only integer `-0` as integer0.
   `-0.0`, `1e0`, strings and booleans must continue to refuse in integer fields. This is a
   compatibility proposal for the standalone carrier, not an unreviewed K1 change.
3. **Legacy SourcedValue float coercion:** installed `value: float` accepts `true` and
   `"1.0"` and normalizes both to1.0; the Rust derived f64 field rejects them. The installed
   common.py explicitly distinguishes legacy aliases from strict Json* wrappers. Propose
   preserving the exact field-local Python interpretation in a reviewed small-carrier
   adapter; never enable global bool/string→number conversion. Choosing stricter public
   semantics instead would require its own protected semantic decision and is not applied.

No formatter/dependency change is proposed from this run: the reviewed shortest-digit
notation adapter matches the complete frozen finite corpus. This remains finite evidence.
The three identity supplement cases address a disclosed initial coverage omission; both
sets must remain in any repeat, with all original failures preserved.

## SIMD follow-up

Release compression is scalar in the inspected symbol. The full hash path nevertheless
contains compiler-generated packed output byte rearrangement in c2_sha256_boundary.
Movups/movaps copies and zeroing are incidental and reported separately; the packed shuffles
are not dismissed as ABI moves. Thus force-soft is insufficient for a full-hash no-SIMD claim.

For review, the smallest changed-flag experiment would use both profiles with exactly:

```text
RUSTFLAGS=-C debuginfo=1 -C linker=/controls/linker.sh -C no-vectorize-loops -C no-vectorize-slp
```

Keep the current source, lock, features, vectors, image, CPU defaults and linker map arguments.
These two additional LLVM-vectorization switches are **proposed, not executed**. They may
not suppress other compiler lowering or stdlib packed instructions; the actual same hash
path must be reinspected. Do not disable x86_64 ABI-required ISA features or promise success.
Alternatively reconcile the intended boundary explicitly if only compression is required;
this run does not assume that narrower boundary grants full-hash qualification.

## Read-audit and authority limits

No strace exists in the accepted image. Compiler/linker argv/environment, Cargo verbose
build-script output and dep-info are real evidence, but are not exhaustive file-open traces.
If exhaustive script/proc-macro reads are required for the next gate, provide a reviewed
already-available tracing mechanism or separately approve exact diagnostic tooling. No
image/tool installation is implied here; no candidate diagnostic version is invented.

Coordinator/B review this source, the ten mismatches, refusal layers, supplement freeze,
SIMD evidence and tracing limits. Any repeat/source/flag decision remains separate from
public K2 implementation, live dependencies, C3, authority records and qualification.
U0024 remains deferred. No further construction is performed in this handoff.
