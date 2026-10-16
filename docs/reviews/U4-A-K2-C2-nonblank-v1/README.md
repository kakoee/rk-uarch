# A standalone Sourced nonblank compatibility correction

The narrow correction passes **21,694 cases and 17 standalone unit tests in each mode**:
all 21,159 historical corrected cases, B's unchanged 66 independent cases, and 469 separately
frozen focused cases. Expected refusals require the frozen layer/reason class; successful
results require exact canonical bytes and SHA256. Both modes produce identical corpus bytes.

This follows the [bounded release](../U4-K2-C2-blank-field-followup-v1/README.md) and its
[receipt](../U4-K2-C2-blank-field-followup-v1/receipt.json), joining B's exact
[81bab621 review](../U4-B-K2-C2-compatibility-review-v1/README.md) of A's
[923face source](../U4-A-K2-C2-compatibility-v1/probe.rs). Main integrated normally to
`a84a069` before work. Python remains the private **ce732f5** export, with the same verified
interpreter, Pydantic 2.13.5 and contract module hashes. All earlier packages, vectors,
failures, hashes and private receipts remain unchanged. No new dependency/C2 approval is
requested or inferred.

## Exact correction and distinct rules

[probe.patch](probe.patch) adds one local `sourced_nonblank` predicate, replaces exactly
three checks (`unit`, stipulation `rationale`, non-stub claim `source`), and adds five unit
tests. Both diffs use zero context (`git apply --unidiff-zero`); private forward/reverse/forward
checks verify their exact preimages and postimages. [probe.rs](probe.rs) is the exact
formatted/executed standalone source. It does not
trim, normalize or change stored text. Defaults, required fields, finite-value checks and
existing claim/stipulation/source conditions remain unchanged. The legacy numeric-string
adapter, NumericLeaf and all other carrier logic are byte-for-byte unchanged.

The predicate represents the **complete strip-empty character set observed in pinned
CPython 3.12, Unicode 15.0.0**. Before correction, Python enumerated all 1,114,112 codepoints
using `not chr(cp).strip()`, finding these 29:

| Characters | Count |
| --- | ---: |
| U+0009–U+000D | 5 |
| U+001C–U+0020 | 5 |
| U+0085, U+00A0, U+1680 | 3 |
| U+2000–U+200A | 11 |
| U+2028, U+2029, U+202F, U+205F, U+3000 | 5 |

A string is nonblank iff at least one character is outside that set; the empty string is
blank. The implementation uses explicit ranges/scalars, with no new Unicode library.
The new unit test independently enumerates every Rust Unicode scalar through the predicate
and compares its count and digest to the frozen Python set. No surrogate was strip-empty.
The frozen set encoding/digest is in [python-freeze.json](python-freeze.json).

Two rules are deliberately kept separate:

- **Legacy numeric-string conversion** is Pydantic's float behavior. U+001C–U+001F around
  numeric text still refuse as `LegacyFloatSyntax`; ordinary accepted numeric padding and
  underscore cases still pass. This task does not replace that adapter's `.trim()`.
- **NumericLeaf.path** uses the installed nonempty/pattern rule. The pinned Python model
  accepts a path containing only U+001C, U+001D, U+001E or U+001F, even though Python
  `str.strip()` considers each blank. The separate Python-only carrier audit also covers
  ordinary space, U+0085 and U+200B. It is recorded in the freeze and is not a new native
  qualification claim. No global trim replacement or carrier-policy change was made.

## Frozen tests and observed outcomes

[Python derivation](python-derivation.log) and [freeze](python-freeze.json) record private
import origins, module/interpreter hashes, Unicode/Pydantic versions and exact expectations.
Every contract origin is in the private ce732f5 export and matches the previous pinned
origin hash. Python ran with `-I -S -B` and explicit private reference/site-package paths.
B's 66 expectations were newly re-derived exactly, while their original JSONL bytes were
copied unchanged. The [469-case extension](focused.jsonl.gz) is separate from every earlier
corpus. It includes 248 positives and 221 refusals:

- Each of the 29 blank characters in all three fields, alone, mixed with other blanks,
  and surrounding nonblank X; U+001C–U+001F are covered individually.
- Neighboring nonblank codepoints, NUL, U+001B, U+007F, U+180E, U+200B, U+2060 and U+FEFF;
  mixed blank/nonblank strings; empty, null and absent fields; all-blank concatenations.
- Measured/spec-derived/estimated claims, stub source restrictions, defaults, forbidden
  rationale/provenance/source/date combinations, and unchanged numeric conversion controls.

[Unit freeze](unit-freeze.json) and [refusal freeze](refusal-freeze.json) precede the code
correction and builds. The [reviewed comparator](compare.py) is **byte-identical** to 923face
(SHA256 `05c2b2a0e81f3a5157246b6d487fedc903d6390735e4b76712f70f3c4e033338`). Its 160 historical
refusal entries remain exact. [New refusal expectations](new-refusals.json) add 257 entries:
all 36 expected B-independent refusals and 221 focused refusals. This is a new A freeze;
B's original eleven reason assertions are not relabelled as having covered every reason.

New mappings follow unchanged parsing/type/numeric checks and the existing `SourcedValue rules`
condition. Missing/null required unit fields retain their missing-field/type error; validly
typed blank fields refuse at `carrier/SourcedValue rules`. An unrelated transport or numeric
conversion error cannot satisfy a nonblank check. No expectation was edited after execution.

| Dataset, per debug/release mode | Cases | 923face baseline mismatches | Corrected mismatches |
| --- | ---: | ---: | ---: |
| Historical corrected sets | 21,159 | 0 | 0 |
| Unchanged B independent set | 66 | 2 | 0 |
| New focused set | 469 | 33 | 0 |
| Total | 21,694 | 35 | 0 |

The two exact B failures remain `B2:legacy:blank-control-unit` and
`B2:legacy:blank-control-rationale`. Every new baseline failure is **acceptance of a field
that Python considers blank**, not a transport failure or arbitrary refusal mismatch.
The 33 focused failures comprise 24 individual/mixed U+001C–U+001F field cases, three
all-blank concatenations and six non-stub source controls. All legitimate positive outputs
are byte-identical before/after; the four historical corpus streams are entirely unchanged.

The original 923face executable digests were verified before copying them to private baseline
paths and **actually rerunning** all six sets in both modes. Corrected builds run the previous
12 units plus five new units (blank-set digest, control-field refusal, text preservation,
existing rules and numeric-adapter isolation): **17 pass per mode**. The 417 expected refusals
per corrected mode match their exact semantic classes.

## Reversion and exact restoration

[revert.patch](revert.patch) changes only the new predicate body back to Rust
`!s.trim().is_empty()`. Its separate four-file workspace retains all 17 tests, accepted
inputs and flags. [Reversion plan](reversion-plan.json) freezes that source and the
535-case selection (unchanged B66 plus focused469) before the fault builds.

Both fault builds succeed. Each 17-test selection exits 101 with the expected blank-set and
blank-field failures; both native selections reproduce exactly **35 wrong acceptances**.
The same variant workspace is then restored to the exact corrected source bytes and rebuilt
in both modes: **17 units pass, 535 comparisons pass**, and both actual executable digests
are identical to the original corrected builds. [Actual phase results](reversion-results.json.gz)
preserve every failure and restored success.

The fault binaries remain in Cargo's original separate deps artifacts. After restoration
replaced the primary executable paths, those artifacts were located by their recorded exact
digests and copied to explicit private saved-fault paths; [bindings](reverted-binaries.json)
record both paths. They were not recreated or substituted. Corrected and baseline binaries
remain intact in their separate targets.

## Exact identities and boundaries

| Subject | SHA256 |
| --- | --- |
| Corrected probe | `a4129c184bb04e4dedcbe518c593c47c5ecc27154debd3ff558ccba67c86153c` |
| Corrected debug executable | `53af189a49175417f12d3e3ea2fd00b5041cb4f99261c7be83297c4ffb083ff3` |
| Corrected release executable | `c2eb867ad1f8f6a03eba5b9ae8e97b6521797b511444d03f034ce6293485067f` |
| Focused vectors | `935fa27a14f5fb07542f1652df37cdacb79a039b411e207036f3e03aac1881fc` |
| Unchanged B66 | `1f469bd7e140783f077ce52d0edad8434087f15cd7179c29988b82e001aa9c18` |
| Accepted lock | `cbe9a580e0c6209abdb34be23965c2fe2f75b5970819d2021c943e2e02d939be` |
| Accepted crate manifest | `60299ba9498e506010a5c908ef8017beb2279d1aedab409a7fc21601d3b35ee0` |

[Starting inventory](starting-source.json), [build inputs](build-inputs.json) and actual
metadata verify exactly four workspace files and **one `c2-probe` binary target**, with no
production engine source/target. The retained package name `uarch-engine` preserves the lock.
Only `--bin c2-probe` and its standalone tests were built/run. Necessary accepted dependency
build scripts/procedural macros remain within the same authorized construction.

Image `sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523` and accepted
tool outputs were reverified. Full locked/offline metadata matches the accepted dependency
resolve/features graph. Compiler flags remain exactly
`-C debuginfo=1 -C linker=/controls/linker.sh`, with the same wrapper bytes. Every container
uses `--pull never --network none`, unprivileged UID/GID, dropped capabilities,
no-new-privileges, read-only root/source/cache/controls/vectors and private writable outputs.
No original evidence is mounted writable. No downloads, installation, image/security changes,
tracer invocation, vectorization experiment or mapped execution occurred.

[50 command receipts](commands.json) bind actual argv/environment/exit/output hashes;
[raw outputs](command-outputs.tar.gz) and [per-command map](command-output-map.json) retain
separate execution identities while deduplicating equal bytes. [Host workflow](host-workflow.json)
and [executed helper bytes](executed-controls.tar.gz) retain the host derivation/orchestration.
Those scripts contain private-path operations and must not be blindly rerun against retained
evidence. Bulk caches/builds stay private at `/tmp/u4-k2-c2b.khaj67gd`.

[Compiler/linker receipts](compiler-linker-commands.json.gz) record 286 actual argv/environment
invocations. [Available build diagnostics](build-diagnostics.json.gz) cover 88 build directories
and 194 dep-info files. They are not exhaustive read evidence. B's acquired diagnostic tools
were neither mounted nor used; this correction does not close the future read/authority gate.

[Preservation](preservation.json) verifies **23,264 original A private files** unchanged in
bytes, sizes and mtimes, all 1,719 copied cache entries, earlier package Git trees, human
semantic postimages, live lock, historical vectors/refusal rules and reviewed comparator.
[Private inventory](private-inventory.json.gz) binds retained raw sources, outputs and binaries.
The baseline identity, old successes/failures and C1 licence/network evidence are inherited
inputs; Python derivation, baseline/corrected/fault/restored runs here are new observations.

## Verification and coordinator/B disposition

Run `.venv/bin/python -I -B docs/reviews/U4-A-K2-C2-nonblank-v1/verify.py` for read-only
verification of saved receipts. It checks all stream/hash/refusal comparisons, exact baseline
failures, nonempty units, restored source/binary identities, freeze ordering, unchanged
comparator/classifications and meaningful wrong-refusal controls. It does not rerun native
code or Python reference derivation. [Validation](validation.json) records lint, pinned
formatting, link and arithmetic checks. Inventory excludes itself and validation receipts;
no receipt is a qualifying authority anchor.

No failure remains in the corrected finite selections. Public carrier/protocol qualification,
production K2, live installation, C3, final build/host authority and qualification remain
separate. Exhaustive read evidence remains incomplete, and hashing SIMD remains non-blocking.
U0024 remains deferred. **Stop for coordinator/B reconciliation**: B reviewed 923face; this
new nonblank correction and its results await that review.
