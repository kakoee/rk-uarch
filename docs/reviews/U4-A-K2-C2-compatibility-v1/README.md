# A bounded C2 compatibility correction

The separately revised standalone probe passes all **20,965 original cases**, the unchanged
**three-case supplement**, **52 B cases** and **139 additional Python-derived cases**, in both
debug and release. All **12 unit tests per mode** pass. The two modes return identical bytes
for each corpus. All **160 expected refusals per mode** match frozen layer/reason classes;
passing requires exact canonical bytes and SHA256 as well as the expected outcome.

This is the bounded follow-up released by
[coordinator reconciliation](../U4-K2-C2-followup-release-v1/reconciliation.json), joining
[B's review at 41150f2](../U4-B-K2-C2-reconciliation-v1/README.md) under the existing
[C2 approval](../U4-K2-approved-C2-release-v1/acceptance.json). Published main integrated
normally from `3faa3e9` to `c277ddd` before work. The Python reference remains the original
`ce732f5bedccdde629edcf278fa76ea772d0ea82` export; C1's historical export remains `0718955…`.
Neither experiment is relabelled as having run against later main. The original
[A package at 3faa3e9](../U4-A-K2-C2-probes-v1/README.md), its counterexamples/supplement,
B's review, and all C1 evidence remain unchanged.

## Exact changes and discriminators

[Actual probe source](probe.rs) and [diff against the original](probe.patch) change only the
standalone test target; [compare.py](compare.py) is the revised host comparator.

- Explicit `Value` token/type dispatch replaces the untagged `Content` route. Rational
  objects require exactly numerator/denominator, integer tokens, u128 bounds, positive
  denominator and gcd=1. Duplicate keys are refused earlier by the existing strict parser;
  no rational is silently reduced. Scalar leaf integers retain arbitrary-precision decimal
  values, including 2^128, −2^127−1 and positive/negative 300-digit values. Bool, string and
  null stay their own types; floating tokens refuse. The caller marker guard remains ahead
  of dispatch, including escaped/nested keys.
- A quote/escape-aware lexical scan normalizes only complete integer `-0` tokens for the
  strict integer-bearing operations. It does not rewrite string contents, `-0.0` or exponent
  tokens. Zero denominators still refuse. The strict integer validator now classifies token
  type separately from range, without a floating intermediate.
- A deserializer attached only to `Sourced.value` handles the legacy float conversion.
  Defaults and existing claim/stipulation checks remain. The pinned Pydantic 2.13.5 reference
  was executed before corrected Rust: notably `"1_.0"`, `"1._0"`, `"1e_2"`, `"1_e2"`,
  `"1e+_2"` and Unicode padding are accepted, while repeated/edge underscores, Unicode
  digits, nonfinite values, null and objects refuse. This differs from calling Python's
  built-in `float()` directly. [Python observations](python-derivation.log) and frozen
  extension bytes preserve the boundary results. Rust's parse alone is not assumed to
  establish compatibility; the adapter trims and applies the observed underscore rules
  before conversion and separately enforces finiteness.
- A small `json-float` probe operation exercises B's strict-JsonFloat isolation cases; the
  original probe had no implementation for that operation. Bool/string/null are refused
  there, while a numeric integer becomes a float. This adds only standalone test coverage,
  with no public DTO or global coercion change.
- The comparator requires a nonempty, unique, ordered exact ID selection; LF framing;
  duplicate-free output objects; the exact success/refusal shape; and canonical/hash
  consistency. It refuses malformed output, missing/duplicate/extra/reordered records and
  unrelated refusal layers/reasons. [Frozen per-case rules](refusals.json) follow the failed
  condition: IntegerToken/IntegerRange, RationalFields/InvalidRatio, LeafFields/LeafScalar,
  legacy float type/syntax/finiteness, duplicate/marker, encoding, canonical and identity
  checks. A transport error cannot satisfy a duplicate-key test.

The historical Python expectations are never edited. The revised refusal overlay deliberately
uses the new visitor's actual semantic classes rather than the former u128-deserializer text:
for example, decimal/exponent tokens now yield `carrier/IntegerToken`, and a missing rational
field yields `carrier/RationalFields`. Unchanged parser/encoding/identity diagnostics retain
narrow reviewed classes. Python decode/UTF-8 versus Rust strict-json/UTF-8 distinctions and
caller-marker protocol refusal remain explicit in the overlay. An initial rule draft is
retained in the controls archive; before corrected native execution its legacy visitor rules
were refined solely to permit serde's location suffix. No expectation was changed after
observing corrected results.

## Tests first, baseline and restoration

[Extension freeze](extension-freeze.json), [refusal freeze](refusal-freeze.json) and
[unit-test freeze](unit-tests-freeze.json) precede the corrected build. B's 52 Python results
were re-derived exactly from the pinned reference. Original vectors/supplement were copied
byte-for-byte. Frozen test code, initial rules and executed host scripts are preserved in
[executed-controls.tar.gz](executed-controls.tar.gz), with [member bindings](executed-controls-index.json).
Local timestamps establish recorded ordering, not external time attestation.

The verified original binaries were copied into this experiment's private target and actually
rerun in both modes before corrected code execution. Their original/supplement outputs match
the historical bytes exactly. Baseline extension counts below measure status/value mismatch;
they do not claim acceptance of the baseline's refusal reasons under the revised visitor rules.

| Dataset | Cases per mode | Baseline status/value mismatches | Corrected mismatches, including refusal classes |
| --- | ---: | ---: | ---: |
| Original corpus | 20,965 | 10 | 0 |
| Original supplement | 3 | 0 | 0 |
| B prospective extension | 52 | 14 | 0 |
| A boundary extension | 139 | 47 | 0 |

The original ten remain `leaf:00000`–`00006`, `integer-token:00002`, and
`typed-normalization-fault:00002`–`00003`. [Baseline rerun](baseline-rerun.json) records all
newly observed extension failures. The original known-answer hashes, M/B normalized fixtures,
finite sweep, exponent/halfway boundaries and identity checks all remain in the retained
corpus. These normalized fixtures are not a full Rust public-carrier implementation.

The host ran **27 negative controls** before the correction build; the portable verifier
repeats them against the published comparator and restores positive comparisons afterward.
The saved original comparator accepts an empty pair, reordered selection, unrelated refusal
layer and unrelated reason. An actual scratch comparator reversion exits 1 on these four
checks; its restoration exits 0. The baseline nonempty results remain valid evidence of ten
failures despite these comparison gaps.

Every native reversion has its own source/workspace and target. Exact selections and sources
were frozen before those builds. Each reversion builds successfully, fails a nonempty 12-test
unit selection (expected exit 101), and fails the following comparisons in **both** modes.
Running the exact same selection on the untouched corrected binaries restores zero mismatches.

| Reverted correction | Selection | Mismatches per mode | Of these, expected-positive regressions |
| --- | ---: | ---: | ---: |
| Leaf dispatch | 59 | 50 | 20 |
| Integer `-0` normalization | 26 | 8 | 6 |
| Field-local legacy float adapter | 93 | 80 | 38 |

The remaining mismatches in that last column's complement are diagnostic/class differences
on expected refusals, not additional value failures. [Reversion plan](reversion-plan.json),
[patches](reversions/leaf.patch), [zero patch](reversions/integer-zero.patch),
[float patch](reversions/legacy-float.patch) and [actual comparisons](reversions.json.gz)
make those distinctions reviewable. Corrected debug/release source and binaries were never
replaced by the reversion experiments.

## Identities and execution boundaries

| Subject | SHA256 |
| --- | --- |
| Executed corrected Rust source | `90d7b36df0aac589ff01f360fe294641586ac1406651b697bb4e97068dc84695` |
| Debug executable | `18139fc5483fbcd9dbf42a6f8af66db2f7ca7878e84ca2c8aadd93bedc6d62a1` |
| Release executable | `6c9d7f650247083b1e513e93e9b5874287d2e93891e67f41aa4a1bee7c6234dc` |
| Accepted lock | `cbe9a580e0c6209abdb34be23965c2fe2f75b5970819d2021c943e2e02d939be` |
| Accepted crate manifest | `60299ba9498e506010a5c908ef8017beb2279d1aedab409a7fc21601d3b35ee0` |
| B extension JSONL | `9d687e0b3823b0185f8892f4ec6637cf17f3b0d07e576026e9eec6c61c7773cf` |
| A extension JSONL | `cf956471e48b5a4001cfe1c321c5fe1874a0da980d005bcde5f738e1c1f2dfa9` |

Both actual executable digests are recorded independently. This is not a final logical-engine
identity, build receipt or human first-use authority record. Original corpus/supplement
identities remain `8dae6586…` and `097fb324…`, with full hashes in the freeze and summary.

Accepted image `sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523`
and rustc/Cargo 1.99.0, cargo-deny, rustfmt and clippy outputs were reverified byte-for-byte
against C1. The exact accepted manifests/lock and full metadata resolve/features graph match
C1, including sha2 `std,force-soft`. No resolution or dependency substitution occurred.
`RUSTFLAGS=-C debuginfo=1 -C linker=/controls/linker.sh` and the existing rustc/linker wrappers
remain unchanged. No vectorization flags or further SIMD analysis were introduced.

Every container uses `--pull never --network none --read-only`, private empty Docker config,
a cleared container environment with explicit tools, and read-only verified cache/source/
controls/vectors. Targets and receipts are private writable paths. Necessary approved dependency
build scripts/proc macros run only in this standalone build. No original evidence is mounted
writable, and no engine source is included. Bulk cache, sources and builds stay outside Git
under `/tmp/u4-k2-c2r.s0udc3ig`.

[Commands](commands.json) bind exact argv, explicit environments, exits and output hashes.
[Raw command outputs](command-outputs.tar.gz) are losslessly stored once per content hash;
[the output map](command-output-map.json) binds each separate observed command to its bytes.
This storage deduplication does not collapse separate executions. Original baseline identities
are inherited and reverified; baseline reruns, Python extension derivation, corrected builds,
comparisons and reversions are new observations. No inherited C1 download/licence/network
result is claimed as newly executed here.

[Compiler/linker records](compiler-linker-commands.json.gz) contain 556 actual argv/environment
records. [Build diagnostics](build-script-output-and-depinfo.json.gz) cover 176 build directories
and 384 compiler dep-info files across corrected/reverted targets. These are available actual
outputs, not exhaustive file-read tracing. B's separate diagnostics task remains separate;
no tool acquisition, tracer, security change or final authority record was attempted.

[Preservation](preservation.json) verifies **13,104 original private files** unchanged in bytes,
size and mtime, all **1,719 copied cache entries** unchanged, historical package Git trees,
human semantic postimages, original vectors/supplement, frozen extensions/refusals and the
unchanged live lock. [Private inventory](private-inventory.json.gz) binds retained raw artifacts,
executables and build outputs without publishing bulk trees. [Host/error notes](host-errors.json)
preserve the sandbox read retry, pre-execution diagnostic framing refinement and intentional
negative experiment exits.

## Verification and disposition

Run `.venv/bin/python -I -B docs/reviews/U4-A-K2-C2-compatibility-v1/verify.py` from the A
checkout. It checks inventory/archive bindings, accepted inputs/tools, freeze ordering, every
saved comparison/refusal, nonempty unit names, exact baseline failures, all reversion/restoration
outputs and 27 host controls. It performs no native execution or Python reference re-derivation.
The public comparator is only Ruff-formatted from the executed comparator; the verifier checks
AST equality against the retained executed bytes. [Validation](validation.json) records lint,
source-format, arithmetic and relative-link checks. Inventory excludes itself and validation
receipts to avoid self-reference; none of these receipts is a qualifying anchor.

No failures remain in these finite corrected selections. They do not establish universal
numeric compatibility, public carrier/protocol qualification, mapped execution or exhaustive
build reads. The simple native transport wrapper remains a private test harness. There is no
public engine, protected source/schema edit, live installation, C3/image distribution or
qualification. U0024 remains deferred. **Stop here for coordinator/B reconciliation** of this
new package; B's published review covers the baseline/design, not these corrected results.

Before publication, main fast-forwarded normally to `ef751b57ae164d2719baf3c228b9ea0822d79419`,
joining B's diagnostic proposal and the subsequent
[acquisition/static-inspection approval](../U4-read-diagnostic-approved-acquisition-v1/acceptance.json).
That is separate B-lane work; A did not acquire tools or execute a tracer. The approval does
not close read evidence or review this corrected source. [Publication integration](publication.json)
keeps this join separate from the experiment's pinned reference and inputs.
