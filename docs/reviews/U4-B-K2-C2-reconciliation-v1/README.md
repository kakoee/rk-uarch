# B reconciliation of the actual C2 experiment

**Baseline independently reproduced; complete typed parity, full-hash no-SIMD and exhaustive
build reads remain unresolved.** Recommend a small standalone field-compatibility/comparison
follow-up and, separately, A's exact two-flag experiment. Neither is approved or applied by
this review. The existing dependency/C2 approvals stand; no repeat vote is requested.
This is B reconciliation, not final adversarial review, public K2 release or authority.

| Subject | Exact identity |
| --- | --- |
| A publication reviewed | `3faa3e9dbe785f43c51e26ad886eeb6bc3b00398` |
| Python/reference source | `ce732f5bedccdde629edcf278fa76ea772d0ea82` |
| B starting HEAD | `32ab29c76b0bb7325366f09792a89dfa823a7d41` |
| Main integrated before review | `eb8821c8372ac28257cef09be36459b6af2a4eaf` |
| Approval receipt SHA256 | `831c9aab805324e65fa33c017bfacae0cf5ebaf140a1a3f1e84ec6fd03719d97` |
| Exact probe SHA256 | `e77b1aec69cf43ad32706ae618280463beae37e2701fa8e39e4e3f53948ed424` |
| Accepted lock SHA256 | `cbe9a580e0c6209abdb34be23965c2fe2f75b5970819d2021c943e2e02d939be` |
| Accepted crate manifest SHA256 | `60299ba9498e506010a5c908ef8017beb2279d1aedab409a7fc21601d3b35ee0` |
| Accepted cache inventory SHA256 | `ce219674649c7e77ce84806db559d8473a6c6a62b5bad7aa3ff0e93486f30148` |
| Original vectors SHA256 | `8dae6586c54462debbf1dad28ff963099a1a89d7b2daa213ba2908c7e46c7e9e` |
| Separate supplement SHA256 | `097fb324e704e49d0c129984cef713e2b961520e81f8c8b9f4885222a91a9485` |
| Actual debug executable SHA256 | `a36293c7e8778f7dab3403dc87d5aa1aa23e327c1f41c09272dea6b59b038c84` |
| Actual release executable SHA256 | `7bb89b3877a5a1931ccd16c4fb5a027e13df9a356e6c8dabab455a67270218f1` |
| Accepted image | `sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523` |

C1's historical source stays `0718955cc0656e5bac4688d4696abbd547cb4186`; it is not the Python
source above. A's [next-decision proposal](../U4-A-K2-C2-probes-v1/next-decision.md) remains
SHA256 `063af1b27bf3786ffd6a007d20e9276758cdd68469823550d18f9ed869d6f51e` and unapplied.

## Independently executed baseline and preservation

B inspected the saved probe, wrappers and host scripts first. Only the rustc/linker wrappers
were reused for execution; B wrote its own runner, derivation, comparison and static-path
checks. The copied workspace has exactly four files, one Rust binary source and no engine
library/source. Package `uarch-engine` and accepted manifests/lock remain byte-identical.
Actual metadata reproduces A's probe target/graph; no dependency change or resolution occurs.

[Commands](commands.json) record **22 newly executed baseline/tool/inspection commands**, all
exit 0. Debug/release were built from fresh private targets, then both original and supplemental
streams were run. All **six standalone unit tests in each mode** pass, with exact nonempty
names recorded in [comparison](comparison.json) and [debug](unit-debug.display.log)/
[release](unit-release.display.log) display logs. The displays trim the final blank line;
exact raw stdout remains in private receipts with hashes in commands.json. Both newly built binaries are byte-identical to A's saved
binaries, and both original outcome streams, supplements, metadata, cfg, symbol/disassembly/
ELF/relocation outputs match A byte-for-byte. Build/test logs differ in transient build names,
ordering/timings; they are independently bound, not claimed identical.

Containers used the accepted image with `--pull never --network none --read-only`, user
1000:1000, no capabilities, no-new-privileges, an empty environment plus explicit accepted
paths, and unchanged `RUSTFLAGS=-C debuginfo=1 -C linker=/controls/linker.sh`. Source, cache,
controls and vectors were read-only private copies; targets/receipts were private writable
outputs. No original evidence was mounted writable. No source/flag fix, download, image
change, engine compilation or mapped-job execution occurred.

[Preservation](preservation.json) checks all **5,994 original C2 files** unchanged in bytes,
size and mtime, plus unchanged copied source/cache/controls/vectors. Original C1/history
remains untouched. B verified all 1,719 accepted cache entries, 376 saved private receipts,
28 A command-output bindings and 19 compressed-artifact bindings. Bulk trees/outputs remain
under `/tmp/u4-b-c2-review`; the original remains `/tmp/u4-k2-c2.75eyx6ab`. Git carries only
owned helpers and small receipts, not caches/build trees or copied checkpoints.

## Typed-carrier disposition

B re-derived **every one of the 20,965 original Python expectations**, all 488 fixture
identity pointers, ten normalized M inputs, 113 B inputs and three supplemental identities.
Interpreter bytes, Pydantic 2.13.5 and all contract module hashes match the freeze; imports
originate from the private `ce732f5` export under `-I -S -B` with explicit site-packages and
PYTHONPATH/MYPYPATH unset. No producer/oracle or editable project checkout was imported.
[Python derivation](python-derivation.json) and [52 separate prospective cases](B-expectations.json)
retain literal bytes and results. Those 52 are newly executed **Python-only expectations**,
not added to A's frozen corpus and not reported as native passes.

Both actual Rust modes reproduce **20,955 matches and the same ten failures**:

| Counterexamples | Independent interpretation | Minimal proposed compatibility work |
| --- | --- | --- |
| `leaf:00000`–`00006`: rational numerators 0, 1, 2^53−1, 2^53, 2^53+1, u64_max, u128_max; denominator 1 | Python accepts each reduced rational. Direct Rational parsing passes; untagged Leaf dispatch refuses at the Rust carrier layer. The actual serde derive routes through ContentRefDeserializer; that implementation lacks i128/u128 overrides, whose trait defaults refuse. | Agree with explicit token/type dispatch avoiding this Content intermediary and f64. Exact rational object keys; strict integer tokens; numerator 0..u128_max, denominator 1..u128_max; gcd=1. |
| `integer-token:00002`: integer `-0` | Python strict JSON produces int 0; strict u128 accepts. Direct serde u128 refuses the minus token at carrier layer. | Agree with lexical **integer -0 only** compatibility. Do not replace text inside strings or accept `-0.0`, `1e0`, bool or strings as integers. Apply consistently to rational integer fields too. |
| `typed-normalization-fault:00002`/`00003`: legacy value true / "1.0" | Installed SourcedValue's float accepts and normalizes both to 1.0. Rust derived f64 refuses at carrier layer. | Agree with a field-local legacy adapter; defaults, finiteness and claim/stipulation rules remain. No global coercion and no protected Python tightening. |

Two precise clarifications are needed in the visitor/adapter follow-up, without changing
accepted dependencies:

- NumericLeaf's **scalar StrictInt has no i128/u128 bound**. Preserve integer 0, −1, 2^128
  and −2^127−1 as integers; bool, text and null retain their own branches, while float 1.0
  refuses. The existing untagged scalar i128/u128 alternatives also traverse the unsupported
  Content path (source-derived concern, not an additional measured native mismatch here).
  Restricting all scalar leaves to machine integers would tighten installed semantics.
- Legacy float compatibility is more than the two reported literals: Python also accepts
  false→0.0, " 1.0 "→1.0, "1e0"→1.0 and "1_0"→10.0. It refuses nonfinite strings,
  null and objects. A simple Rust f64 string parse must not be assumed equivalent.
  JsonFloat and strict integer/rational fields still reject bool/string numeric coercion;
  NumericLeaf legitimately accepts bool/string **as those types**, not as numbers.

The combined original and B matrices discriminate 1/2 versus unreduced 2/4 and 0/2 (refuse, never silently reduce),
zero denominator, missing/duplicate/unknown keys, u128 overflow, strict float-token/bool/string
refusals, and reserved marker objects. Caller marker refusal is the explicit C2 protocol
control; generic Python JSON accepts these as ordinary objects. It is not a Python numeric
parser refusal. Production DTO parity cannot be inferred from Python-normalized M fixtures
or from this small-carrier experiment. No proposed visitor/adapter was applied.

## Freeze, coverage, framing and comparison controls

[Provenance](provenance.json) verifies accepted approval/input hashes, the exact reference
archive, probe formatter output and saved freeze/output order. The initial pre-build probe
hash differs from the formatted build hash; the actual rustfmt stdout postimage matches the
published/executed probe. Only the final build hash identifies the reproduced binaries.
Saved local timestamps establish receipt ordering, not external clock attestation.

The original 20,965 IDs remain unique and unchanged. B independently regenerated the 4,096
MT19937 patterns (seed `0x5534433250524f42`, one rejected draw), 12,280 signed binary-exponent
boundary entries and 3,798 decimal-boundary entries, and rechecked all finite/halfway canonical
expectations. Four SHA answers include literal standard empty/abc/multiblock/million-a hashes.
All returned successful bytes/hashes agree; the ten expected-positive carrier cases refuse
as recorded above. This is finite evidence, not a
universal numerical proof. The three later-frozen registry/profile cases remain a separate
3/3 result; the original registry-selector omission is not rewritten out of history.

All 41 expected refusals retain their actual reasons/layers: strict-json rejects duplicates,
reserved markers and several malformed tokens; carrier rejects typed bounds/shape; identity
rejects stale/nested/version/self-reference hashes. Python's decode/UTF-8 layers differ from
Rust for malformed UTF-8/surrogates; overflow 1e999 reaches canonical finite refusal. Raw
errors and per-case mappings remain explicit. Identity tests omit only the named top-level
field, leaving nested hashes in the input; they are not a complete authority/cycle resolver.
Malformed **inner payloads** were exercised; the transport wrapper is well-formed JSONL.
There is no claim of a general public subprocess protocol qualification.

B splits bytes on LF only and checks terminal LF, JSON shape/duplicate keys, exact nonempty
ordered IDs, canonical bytes, hashes and expected refusal layers/reason classes. Sixteen
in-memory negative controls and restored positives pass. These are host controls, not native
fault injection. Two narrow original comparison gaps were demonstrated:

1. `compare([], [])` returns zero mismatches despite its empty-selection error wording.
2. Replacing a genuine duplicate-key refusal with an unrelated transport failure—or the
   same layer with an unrelated reason—also returns zero mismatches. A records refusal
   layers but does not fail comparison on them.

Fix these small harness checks in the next standalone follow-up. They do **not** invalidate
the verified nonempty baseline outcomes or turn its ten mismatches into successes. Preserve
allowed cross-language layer differences explicitly rather than forcing identical errors.
A's original invocation error, U+2028/splitlines failure and supplement omission remain intact.

## Hash path and smallest compiler experiment

[Independent static path inspection](hash-path.json) uses B's actual objdump/readelf outputs
from the byte-identical rebuilt binaries. Debug reaches compression through digest/update/
block-buffer calls; release's GOT slot `0x9fb48` resolves to `0x4c9a0` (`compress256`). The
boundary actually calls that slot, and loads it into r13 for subsequent indirect calls.
No SIMD-register instruction occurs in the selected sha256 compression/helper symbols.
This conservative call/pointer analysis is not exhaustive dynamic tracing of arbitrary
indirect calls or libc internals.

Release boundary `0x33c20` nevertheless contains **14 packed output transformations** at
`0x33e3d`–`0x33e7d`: unpack, shuffle and pack operations. They follow final compression and
transform the digest state into output bytes. These are part of the hash path, distinct
from incidental movups/movaps/movdqa copies, xor/pxor zeroing, libc calls and unrelated
parser/formatter code. Correct SHA answers and force-soft do not make this a no-SIMD pass.
No boundary waiver or compression-only redefinition is recommended.

A's smallest informative next compiler experiment is the exact proposed addition of
`-C no-vectorize-loops -C no-vectorize-slp` in **both modes**, preserving the baseline
probe, dependencies, vectors, image, CPU defaults and linker-map setup in separate private
targets. Recommend it as a separate release from compatibility edits so each delta is
attributable. Reinspect the same complete hash path, retain all packed/copy/libc findings
and rerun both corpora/units. These flags may not suppress other lowering or prebuilt stdlib
instructions. They have not been executed or approved here; success is not promised.

## Read-audit dependency and remaining decisions

[Read-audit disposition](read-audit.md) separates observed argv/environment/output/dep-info
from actual reads. B observed 139 compiler/linker wrapper records and 96 dep-info files;
A recorded 138/96. The extra B record is exactly an additional `rustc -vV` query, not changed
source or flags. Necessary dependency scripts/proc macros ran under the existing C2 approval.
No exhaustive read trace exists. This is an unmet evidence item, not a waiver from the
approved request to record build-script reads or a complete future ToolInputs/BuildReceipt.

Coordinator's smallest next release list:

1. Standalone visitor/-0/field-local legacy compatibility plus the two comparison guards,
   retaining all original failures, original/supplement cases and the explicit B discriminators.
   Preserve unbounded scalar leaf integers; return exact code for review. No production DTOs.
2. Independently, the exact two-flag experiment above on the unchanged baseline source.
3. Resolve a bounded read-diagnostic input before claiming exhaustive reads or using these
   inputs for final build/authority records. Existing partial diagnostics and the concrete
   proposed tracer-only scope are in read-audit.md; tool identity/access is still pending.

No new dependency vote, C3, live installation, host authority, public K2 implementation,
component fidelity, remote activation, performance claim or qualification follows. U0024
remains in force. Stop for coordinator reconciliation; A is holding further construction.
