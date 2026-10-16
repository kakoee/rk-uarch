# B reconciliation of the corrected standalone C2 probe

**The three corrections and comparator pass their bounded frozen selections, but two new
blank-field counterexamples remain.** B independently rebuilt the exact standalone probe:
all **21,159 frozen cases and 12 unit tests per mode** pass, including 160 semantic refusals.
Debug/release binaries and corpus outputs match A exactly. Of B's **66 additional cases
frozen before these executions**, 64 match; U+001C-only `unit` and stipulation `rationale`
are wrongly accepted by Rust and refused by the pinned Python models. This is a narrow
existing blank-field predicate discrepancy, not a reason to discard the successful evidence.

Review subject remains **`923face8359e6f7ac017c560d9af207509f173b5`**, against A baseline
`3faa3e9dbe785f43c51e26ad886eeb6bc3b00398` and B expectations
`41150f291b0b9bec0ce80812b4974e2f3bc35f8a`. Starting integrated main was
`598c37e736407437acd64fc7348fe16a449cfa62`; it is not an experiment source identity.
Python reference remains `ce732f5bedccdde629edcf278fa76ea772d0ea82`, with Pydantic **2.13.5**.
[Context](review-context.json) records these pins and the subsequent explicit authorization
for building/running only `--bin c2-probe` in the four-file standalone workspace. Two
pre-execution automatic approval rejections were resolved by that clarification; neither
rejected command ran. The retained `uarch-engine` package name preserves lock identity.

## Findings and smallest follow-up

1. **NumericLeaf: agree for the reviewed finite boundary.** Explicit arbitrary-precision
   value dispatch avoids f64 and untagged `Content`. Rational objects require the exact two
   fields, u128 integers, positive denominator and gcd=1; non-reduced input refuses rather
   than being normalized silently. Scalar integers retain unbounded positive/negative
   values; bool/string/null remain distinct and float tokens refuse. Escaped duplicate and
   numeric-marker keys refuse before carrier dispatch. B additionally checked 0/1,
   max-u128/(max-u128−1), ±(2^256+19), range/type/shape and marker counterexamples.
2. **Integer `-0`: agree for the reviewed lexical boundary.** The scan applies only to the
   intended integer-bearing operations and complete tokens outside quoted/escaped content.
   Decimal/exponent tokens remain floats; malformed `-00`, `-01`, adjacent tokens, trailing
   input and unfinished decimals still refuse. Rational denominator `-0` remains invalid.
3. **Legacy `Sourced.value`: the field-local conversion correction passes; blank-field
   parity has a concrete remaining gap.** All B52/A139 expectations were re-derived with
   the pinned Pydantic models, not built-in `float()`. Additional underscore, Unicode
   padding, finite/nonfinite, default and claim/stipulation controls pass except the two
   cases below. Strict JsonFloat and scalar-leaf isolation remain enforced. No global
   coercion or protected Python change is recommended.
4. **Comparator: ready for this bounded experiment.** All 27 author negative controls were
   newly executed on the host; B additionally demonstrated the old comparator accepting
   empty/reordered streams and wrong refusal layer/reason while the corrected one rejects
   them and restores valid positives. Escaped duplicate IDs, empty IDs, and incorrect
   canonical bytes with a self-consistent wrong hash refuse. U+2028 inside a JSON string
   remains valid: record framing is byte-LF, not Python's broader splitlines semantics.
   Transport failure is not counted as semantic refusal. This is a private harness review,
   not qualification of arbitrary public transport or DTOs.

The two new inputs are, respectively:

```json
{"value":"1","unit":"\u001c","provenance":"stub"}
{"value":"1","unit":"Hz","kind":"stipulation","rationale":"\u001c"}
```

Python raises `ValidationError` because its installed validators use `str.strip()` for
nonblank fields. Both Rust modes return success, retaining U+001C in canonical bytes.
The relevant Rust `.trim()` predicates are unchanged from baseline (baseline probe lines
345/351; corrected probe's same `SourcedValue rules` block). This review does not attribute
that pre-existing predicate to the new float adapter or claim an executed baseline rerun
of these two new inputs. [Exact frozen inputs](independent.jsonl),
[Python origins/derivation](python-derivation.json), [new results](native-review.json) and
[raw-output bindings](command-output-map.json) preserve the discrepancy without changing
historical answers. Other analogous nonblank fields have not been newly qualified here.

**Recommend only a bounded standalone blank-field compatibility follow-up**: reconcile the
unit/rationale nonblank predicate with the unchanged Python semantics, retain these two
negative cases plus nonblank positives, and demonstrate scratch reversion/restoration.
Do not waive the discrepancy or call it full carrier parity. No live implementation,
dependency vote, compiler-flag experiment or public K2 release follows from this review.
Coordinator can retain the verified three-family correction/comparator evidence separately.

## Executed evidence and identities

| New B execution | Debug | Release |
| --- | ---: | ---: |
| Original frozen corpus | 20,965 / 0 mismatches | 20,965 / 0 mismatches |
| Separately frozen historical supplement | 3 / 0 | 3 / 0 |
| Historical B extension | 52 / 0 | 52 / 0 |
| A extension | 139 / 0 | 139 / 0 |
| Standalone unit tests | 12 pass, multiplicity one | 12 pass, multiplicity one |
| New B independent cases | 64 agree, 2 counterexamples | 64 agree, 2 counterexamples |

All 160 original/extension refusal rules were independently classified against their
actual failed conditions before comparing the new native results; see
[refusal audit](refusal-audit.json). The old-to-final rule draft has 36 edits permitting
only serde's optional location suffix. Layer, class and input bindings are unchanged.
Recorded extension/refusal/unit freezes precede A's saved builds/outputs; B's independent
freeze precedes every new B native command. This is local ordering evidence, not an
external timestamp attestation. Eleven additional B native reason assertions were frozen
explicitly; remaining new refusal reasons are preserved and reviewed as observations,
not retrospectively declared frozen rules.

[New native fault controls](native-faults.json) independently repeat all three exact scratch
reversions in both modes. Leaf: 59 selected, 50 mismatches including 20 expected-positive
regressions. Integer-zero: 26 selected, 8 mismatches including 6 positive regressions.
Legacy adapter: 93 selected, 80 mismatches including 38 positive regressions. Each variant
build succeeds and its nonempty 12-test selection exits 101. Running those same selections
on the unchanged corrected binaries restores zero mismatches. Every scratch variant source
was returned to corrected bytes; variant binaries remain explicitly labelled fault binaries.
Baseline/corrected patch forward/reverse/forward checks also preserve both exact postimages.

| Identity | SHA256 |
| --- | --- |
| Corrected probe | `90d7b36df0aac589ff01f360fe294641586ac1406651b697bb4e97068dc84695` |
| Exact patch | `3b8539a63d7ac2f47d7e55a99d46fc31269b800a47c7335f0050dd775a73b09b` |
| Comparator | `05c2b2a0e81f3a5157246b6d487fedc903d6390735e4b76712f70f3c4e033338` |
| New B debug binary, equal A | `18139fc5483fbcd9dbf42a6f8af66db2f7ca7878e84ca2c8aadd93bedc6d62a1` |
| New B release binary, equal A | `6c9d7f650247083b1e513e93e9b5874287d2e93891e67f41aa4a1bee7c6234dc` |
| Accepted lock | `cbe9a580e0c6209abdb34be23965c2fe2f75b5970819d2021c943e2e02d939be` |
| Accepted crate manifest | `60299ba9498e506010a5c908ef8017beb2279d1aedab409a7fc21601d3b35ee0` |
| New B 66-case freeze | `1f469bd7e140783f077ce52d0edad8434087f15cd7179c29988b82e001aa9c18` |

The accepted image remains
`sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523`.
New image/rustc/Cargo inspection and locked offline metadata match accepted inputs:
36 full nodes, exact resolve/requested features and only the standalone bin target.
Flags remain `-C debuginfo=1 -C linker=/controls/linker.sh`; no compiler experiment occurred.
Every container used `--pull never`, network disabled, unprivileged user, all capabilities
dropped, no-new-privileges, read-only root/source/cache/controls/vectors and private writable
target/receipts. Existing dependency build scripts/proc macros ran only as part of these
approved standalone builds. There were no production engine sources or mapped jobs.

[42 new command receipts](commands.json) bind argv, environment, stdin, exit and output
hashes. Equal output content is referenced in A's pinned output archive; new content is in
[this archive](command-outputs.tar.gz), mapped separately for every actual command.
Storage deduplication is not inherited execution. [Executed helper bytes](executed-host-controls.tar.gz)
and [their hashes](executed-host-controls.json) preserve the B procedures; they contain
private-path orchestration and should be inspected/copied to a new disposable experiment,
not blindly run against historical directories. Bulk sources/cache/builds remain private
at `/tmp/u4-b-c2r-review.xpkgu2ea`.

New host work includes all 21,159 Python re-derivations, 66 independent expectations,
private module-origin checks with `PYTHONPATH`/`MYPYPATH` unset and isolated Python,
all 160 refusal classifications, scratch patch controls and comparator discriminators.
No pytest/project runtime suite was needed for this receipt review. The
[saved author verifier](author-verifier.log), [saved reversion audit](reversion-audit.json)
and [saved identity audit](identity-audit.json) are explicitly receipt inspection;
they do not themselves constitute native reproduction. C1 acquisitions/licence results,
original baseline native runs and earlier full suites remain inherited, not rerun.

## Preservation, read boundary and coordinator action

[Final preservation](preservation.json) rehashes all **10,160 original A private files**
and **1,719 copied cache entries**, checking sizes and mtimes as well as hashes. Four
baseline workspace files, corpus/rule bytes, corrected binaries and restored scratch sources
remain exact. Only this owned review package is published; historical packages, live source,
lock, artifact, authority and protected files are unchanged by B.

The separately completed [diagnostic acquisition/static inspection](../U4-B-read-diagnostic-acquisition-v1/README.md)
stays separate. No acquired executable/library was invoked or mounted. No future trace is
automatically retargeted to these binaries. Wrapper/Cargo/linker output and metadata remain
partial read evidence; dep-info does not establish exhaustive reads or environment use.
The future build/authority read-closure assertion remains open, without imposing a stop on
unrelated interim development. Hashing SIMD remains non-blocking under subsequent scope
clarification `9ee9917`; no anti-vectorization work was performed.

Run `python -I -B docs/reviews/U4-B-K2-C2-compatibility-review-v1/verify.py` for portable
receipt/control validation. It does not rerun native code or pretend the two counterexamples
passed. [Validation](validation.json) records the actual checks. Stop for coordinator
reconciliation of the narrow follow-up; final public-carrier/protocol qualification, C3,
read authority and public K2 remain pending. U0024 deferrals remain unchanged.
