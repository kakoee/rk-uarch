# B focused recheck of the standalone Sourced nonblank correction

**The bounded correction is ready for coordinator reconciliation.** B independently rebuilt
A's exact source: **21,694 cases, 417 expected refusals and 17 unit tests pass in each of
debug and release**. Both executable hashes match the published binaries. The two U+001C
counterexamples from B's previous review now refuse for `carrier/SourcedValue rules`.
No new counterexample was found in this focused recheck. This is finite standalone evidence,
not public-carrier/protocol qualification or permission to install anything.

Exact review subject: **`c678dedd47e639f7e7f0ac55f48a8775fe524708`**, package
[U4-A-K2-C2-nonblank-v1](../U4-A-K2-C2-nonblank-v1/README.md). The comparison remains B
`81bab62112469f4b32d1b28fc2076caa5815eece` and A
`923face8359e6f7ac017c560d9af207509f173b5`. B started at `81bab621` and fast-forwarded
normally to **`1499346d327d304f89c10e7bd982d7d33768c4be`** before work; that later main
is not the experiment subject. [Setup](setup.json) binds the eight coordinator package hashes,
private export and exact four-file workspace. Python reference remains
**`ce732f5bedccdde629edcf278fa76ea772d0ea82`**, CPython **3.12.14**, Pydantic **2.13.5**,
Unicode **15.0.0**.

## Independent semantics and coverage

[Python review](python-review.json) records newly executed private reference imports, module
hashes and results. Python ran with `-I -S -B`, `PYTHONPATH`/`MYPYPATH` unset, and explicit
private contract and existing site-package paths. No editable project, `rkuarch` or `rk`
module was imported. All imported contract hashes match the pinned prior reference.

B enumerated all **1,114,112 codepoints** using `not chr(cp).strip()` and independently
matched the literal 29-character set: U+0009–000D, U+001C–0020, U+0085, U+00A0, U+1680,
U+2000–200A, U+2028, U+2029, U+202F, U+205F and U+3000. No surrogate belongs to it.
Eight-lowercase-hex-digits-plus-LF encoding has SHA256
`96d09d55259e60e1198f7f067eeac357f6581d3700497cf942886cb74a8bdbac`.
The native unit independently enumerates Rust scalars through the actual helper and checks
that count/hash; it passes in both modes. String emptiness follows because nonblank means
at least one character outside this set, including correct treatment of the empty string.

All **21,694 existing expectations were re-derived** from the pinned Python reference.
There are no new native vectors and no changes to historical expectations. The focused
coverage ledger verifies each of the 29 characters alone, mixed with blanks and surrounding
nonblank X in each of the three applicable fields. Nearby/nonblank characters, mixed text,
absent/null fields, default claim, stub/non-stub provenance, forbidden stipulation metadata
and numeric isolation controls remain in the exact 469-case corpus. Successful canonical
records preserve supplied unit/rationale/source text exactly; the helper never trims it.

A separate small literal predicate reproduced the focused carrier conditions using pinned
Pydantic for value conversion, then predicted **all 35 wrong-acceptance IDs before B's first
native command** by replacing only the blank-character set. The set includes the two B66
failures and 33 focused cases: 24 individual/mixed U+001C–001F cases, three all-blank strings
and six non-stub source cases. This is a carrier-condition check, not a timing engine.
B independently classified all **221 focused refusal conditions** and checked their frozen
layer/reason rules before native execution. The other 196 refusals retain their existing
frozen bindings and are all checked by the unchanged comparator during this reproduction.

The patch was inspected and applied/reversed/reapplied in scratch, checking exact postimages.
Removing only the helper, five added units and three call-site replacements reconstructs
923face **byte-for-byte**. Consequently the legacy numeric adapter, NumericLeaf.path,
canonicalization, other carriers and existing defaults/rules are unchanged.

- The new helper is used only for unit, stipulation rationale and non-stub claim source.
  Stub still requires source=None; absent/null non-stub source refuses. Claim rationale and
  stipulation provenance/source/date restrictions remain intact.
- Numeric-string conversion keeps its own Pydantic-compatible rule. U+001C–001F padding
  around numeric text still refuses as `LegacyFloatSyntax`; accepted ordinary padding,
  underscore conversions and bool handling remain unchanged.
- Pinned Python NumericLeaf.path accepts U+001C–001F alone despite their strip-empty status.
  B rechecked this distinction on the Python carrier. It is not new native path qualification;
  no helper substitution or public-carrier change was made.

## Fresh native results and discriminating controls

| Corpus | Cases per mode | SHA256 |
| --- | ---: | --- |
| Historical original | 20,965 | `8dae6586c54462debbf1dad28ff963099a1a89d7b2daa213ba2908c7e46c7e9e` |
| Historical supplement | 3 | `097fb324e704e49d0c129984cef713e2b961520e81f8c8b9f4885222a91a9485` |
| B extension | 52 | `9d687e0b3823b0185f8892f4ec6637cf17f3b0d07e576026e9eec6c61c7773cf` |
| A extension | 139 | `cf956471e48b5a4001cfe1c321c5fe1874a0da980d005bcde5f738e1c1f2dfa9` |
| Unchanged B independent | 66 | `1f469bd7e140783f077ce52d0edad8434087f15cd7179c29988b82e001aa9c18` |
| A focused | 469 | `935fa27a14f5fb07542f1652df37cdacb79a039b411e207036f3e03aac1881fc` |

[New native results](native-review.json) bind all successes, exact unit names and actual
fault outcomes. The four historical streams (21,159 cases) are byte-identical to B's previous
observations; debug/release agree on all six streams. Every successful record matches exact
canonical bytes/hash and every expected refusal matches its frozen layer/reason class.
The unchanged comparator digest is
`05c2b2a0e81f3a5157246b6d487fedc903d6390735e4b76712f70f3c4e033338`.

Only `sourced_nonblank` was scratch-reverted to the old Rust trim predicate. In **both modes**:

1. Fault builds succeed; the nonempty 17-unit selection exits **101**.
2. The exact B66+focused469 selection produces **35 wrong acceptances**, exactly the
   independently predicted IDs. These are expected refusals returning success, not altered
   error text. All **278 expected positives** still return exact bytes/hashes.
3. The same scratch workspace is restored to the exact corrected source and rebuilt.
   Both binary digests return to the published corrected values; **17 units and 535 cases
   pass**. Fault binaries are separately retained by digest in private saved-fault paths.

Targeted host controls also confirm a transport error or `LegacyFloatSyntax` cannot satisfy
the old U+001C nonblank refusal. Legitimate refusal and positive comparisons pass afterward.
No unrelated fault campaign was repeated. A's saved 923face baseline executions remain
inherited; B freshly executed the exact predicate-only reversion and restoration.

| Build identity | SHA256 |
| --- | --- |
| Corrected source | `a4129c184bb04e4dedcbe518c593c47c5ecc27154debd3ff558ccba67c86153c` |
| Source patch | `f5f14580ca390660521858c27371c8e505a5dfa6891a080b26bd0ff5de3b966c` |
| Fresh debug executable | `53af189a49175417f12d3e3ea2fd00b5041cb4f99261c7be83297c4ffb083ff3` |
| Fresh release executable | `c2eb867ad1f8f6a03eba5b9ae8e97b6521797b511444d03f034ce6293485067f` |
| Accepted lock | `cbe9a580e0c6209abdb34be23965c2fe2f75b5970819d2021c943e2e02d939be` |
| Accepted crate manifest | `60299ba9498e506010a5c908ef8017beb2279d1aedab409a7fc21601d3b35ee0` |
| Accepted workspace manifest | `707748415914b62d281084193635c3300c598422fec88229b85ae68587cb33c3` |

[32 fresh commands](commands.json) record actual argv, environment, stdin, exits and output
hashes. Image/rustc/Cargo inspection matched accepted identities; real locked offline metadata
confirmed 36 nodes, unchanged requested/unified features/dependencies and exactly one
`c2-probe` bin target before compilation. Four-file guards exclude production engine sources.
The accepted package name and necessary dependency scripts/macros remain within the explicit
standalone authorization.

Image remains `sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523`;
flags remain `-C debuginfo=1 -C linker=/controls/linker.sh` with accepted wrapper bytes.
All containers use `--pull never`, networking disabled, read-only root/source/cache,
UID/GID 1000:1000, dropped capabilities, no-new-privileges and private targets/receipts.
No original evidence was mounted writable. No dependency resolution/download, new tool,
image/security change, mapped execution or production engine compilation occurred.

## Preservation and disposition

[Preservation](preservation.json) verifies **7,667 original A private files** and **1,719
copied cache entries** unchanged in bytes, sizes and mtimes; all four source inputs and six
corpora remain exact. Private root: `/tmp/u4-b-c2b-review.vfce4wnr`.
[Raw-output mapping](command-output-map.json) binds each actual command separately. Equal
content references A's pinned archive; new content is [stored here](command-outputs.tar.gz).
Deduplicated storage does not substitute inherited execution. [Executed helpers](executed-controls.tar.gz)
and [hash index](executed-controls-index.json) preserve the actual private-path procedures;
inspect/copy them into a new disposable experiment rather than rerun against old evidence.

The [author verifier log](author-verifier.log) is a newly executed **saved-receipt check**,
not native reproduction. A/coordinator baseline results and C1 acquisition/licence evidence
remain attributed to them. B's fresh Python, native, metadata, reversion/restoration and
preservation work is separately recorded above. No full project/runtime suite was rerun.
Run `python -I -B docs/reviews/U4-B-K2-C2-nonblank-review-v1/verify.py` for portable receipt
validation; [validation.json](validation.json) records actual checks and their limits.

**Recommend coordinator reconciliation of this exact narrow correction; no further source
amendment is identified by this recheck.** Read closure and the separately acquired diagnostic
payload remain separate; no tracer or acquired diagnostic library ran or was mounted, and
future trace commands were not retargeted. Utility hashing SIMD stays non-blocking. No live
installation, public K2, C3, authority, qualification or U4 closure follows. U0024 remains in
force. Stop here for the coordinator.
