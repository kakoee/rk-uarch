# Narrow C2 nonblank-field compatibility follow-up

B's review at `81bab62112469f4b32d1b28fc2076caa5815eece` confirms A's three corrected
families and comparator on all 21,159 cases per mode, but preserves two new failures
among its 66 independent cases. [B handoff](../U4-B-K2-C2-compatibility-review-v1/README.md).
[Exact subject bindings and coordinator receipt](receipt.json).

## Disposition

Release a bounded standalone correction of Python-compatible nonblank checks. Do not
change the Python contracts or normalize stored string contents. In the reported cases,
Python's `str.strip()` treats U+001C-only text as blank, while the Rust `.trim()` predicate
accepts it. Nearby U+001D/U+001E/U+001F behavior must be covered so this is a predicate
correction, not a special case for one observed character. Numeric conversion trimming
is a different field-local rule and must not be changed globally.

The installed SourcedValue also uses the same Python nonblank rule for a non-stub claim's
source. Include that existing standalone predicate in the bounded audit and tests; no
claim is made here that B executed its native analogue. Any change must be tied to the
pinned Python validator, not a new whitespace convention. Other unrelated carriers
remain outside this correction.

## Coordinator checks

Inspected and ran B's portable read-only verifier: 22 inventory entries, 42 command
receipts, 21,159 saved cases and 12 unit tests per mode, the two preserved independent
counterexamples and three recorded fault/restoration families verify. These are saved
receipt checks, not a coordinator native rebuild.

Separately verified the file hashes in B's Python-origin receipt and imported the pinned
reference from its private export with isolated Python and no bytecode writes. Both
U+001C-only unit/rationale inputs refuse. Both corresponding values with an embedded
nonblank X pass and retain their exact original text. Python strip-empty is also true
for each U+001C through U+001F. No Rust process, full suite, tool acquisition or tracer ran.

## Lane action

Send [lane-A.txt](lane-A.txt) to the existing A session. No repeated dependency/C2 vote
is needed for this bounded compatibility correction. The existing approval expressly
covers building/running `--bin c2-probe` and its standalone tests inside the verified
probe-only workspace, notwithstanding the retained `uarch-engine` package name.
Production engine sources and mapped execution remain outside this task.

B can wait for the narrow correction before its follow-up review. Its separately
published diagnostic acquisition receipt is available on main; no tracer execution or
read-closure acceptance is granted by this reconciliation. Hashing SIMD remains
non-blocking. Public K2, live installation, C3, authority and qualification remain separate.
