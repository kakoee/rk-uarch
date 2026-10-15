# B review of the actual C1 precise dependency candidate

**Recommendation: ready for Javid's final acceptance of these exact dependency inputs.**
B found no lock, feature, archive, notice or offline-availability contradiction. This is an
independent evidence review, not acceptance on Javid's behalf. C2 probe permission remains
separate; no public K2 implementation, live dependency installation or qualification follows.

| Identity | Exact subject |
| --- | --- |
| A publication reviewed | `cd273b99c6b9d68ed2dd07d10f8ffad4bedbadb0` |
| A precise package tree | `a2d8ccf5093d93d8f2ceaf47eefbbc5c69d8686d` |
| Experiment source / B starting HEAD | `0718955cc0656e5bac4688d4696abbd547cb4186` |
| B normally integrated main before review | `1751bdb12c369ae1472dd97af4784edbd6492310` |
| Construction plan SHA256 | `4a5cbb16f5f249234d8ffc0a0e01476c89f4769a57ab96f422ff3c10093eebd5` |
| Candidate Cargo.lock SHA256 | `cbe9a580e0c6209abdb34be23965c2fe2f75b5970819d2021c943e2e02d939be` |
| Scratch engine manifest SHA256 | `60299ba9498e506010a5c908ef8017beb2279d1aedab409a7fc21601d3b35ee0` |
| Actual local image | `sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523`, Linux/amd64 |

Publication ancestry does not retarget the experiment to newer installed semantics.
[Preservation](preservation.json) binds the exact source export and both changed files.
[Independent review](independent-review.json) records actual transitions, graph comparisons,
all 35 archive checksums and 75 licence/notice/pointer file hashes. The saved A package and
original failed C1 package remain unchanged, including the failed version resolution and
r-efi audit correction. No proposed tuple list was presented as resolved output.

## Lock, manifest and graphs

B extracted the unchanged historical `entries_allowed` function from its pinned file
(SHA256 `a1ec3147bbead129ed7e7ab78fdb66299aad10a98cb2bc84ea82d156279d4d0e`)
and supplied the **actual parsed candidate lock**. Its 28 retained plus eight additional
identities pass, including exact sources and checksums. All other package records, including
dependency lists, are equal across each precise transition:

- `crypto-common 0.1.7 -> 0.1.6`: intermediate lock SHA256
  `7d065da16dcc24b59f41c28e87ed35b3697fca59f107d9571315ff33e6bd7d36`.
- `typenum 1.20.1 -> 1.19.0`: final candidate above. The first intermediate is still refused
  by the final predicate. Both updates are inherited A execution, not rerun by B.

The eight additions are sha2 0.10.9, digest 0.10.7, block-buffer 0.10.4, crypto-common 0.1.6,
generic-array 0.14.7, typenum 1.19.0, version_check 0.9.5 and cpufeatures 0.2.17. Old
cpufeatures 0.3.1 remains: sha2 requests 0.2.17; chacha20 requests 0.3.1. No package is extra.
The only direct manifest changes are exact sha2 with defaults off and `std,force-soft`, and
serde_json adding `arbitrary_precision` to `std,float_roundtrip`. serde/proptest are unchanged;
there is no new workspace feature. Requested manifest features and actual metadata agree.

B compared actual full and Linux nodes, features and old edges against the respective
installed K1 metadata. Old graph changes are only the engine's sha2 edge and serde_json's
`arbitrary_precision`. The new nodes' unified features equal the plan, including digest's
transitive `alloc,block-buffer,core-api,default,std` and generic-array's `more_lengths`.
The full graph's resolved dependency identities also match every final lock dependency.
Actual target/kind edges are retained in A's metadata and reproduced byte-for-byte below.

Full has 36 nodes; Linux has 35. The full-only **old** r-efi 6.0.0 is reached by getrandom's
`cfg(all(target_os = "uefi", getrandom_backend = "efi_rng"))` edge. Both cpufeatures versions
remain in both views; their non-Linux libc edges are filtered in the Linux view. generic-array
has a **build** edge to version_check: discovering/downloading it did not execute that code.

## Actual archives and licence/notice review

B independently hashed all 35 `.crate` archives against the actual lock, read all 1,611
regular archive members and compared them with extracted cache bytes. Every selected MIT
notice has the same complete grant/conditions/disclaimer after whitespace normalization
and removal of its package-specific copyright prefix. Copyrights remain preserved in the
original archives; this review does not strip or redistribute them. The separate Apache,
COPYRIGHT, COPYING, Unicode and alternative notices are retained in the per-package hash
record. The selected permitted branch is MIT for each package, plus the existing required
Unicode-3.0 conjunct for unicode-ident. This is a review selection, not new human authority.

In particular:

- r-efi's README points to `AUTHORS`; its actual 3,733-byte AUTHORS notice hashes to
  `d027e91dbc9cdbb2f1190068e498bd6b61cff022b6a032b191021ba658d96111`. B read its MIT
  grant, Apache/LGPL alternative notices, and Red Hat/Microsoft/David Rheinsberg copyrights.
  The MIT alternative is available; LGPL is not selected. The author filename-only audit
  failure and follow-up are retained, not hidden by this positive inspection.
- generic-array's `LICENSE` is actual MIT text, not merely a declared expression.
  version_check's historical `MIT/Apache-2.0` spelling has both actual texts.
- memchr's COPYING expressly offers Unlicense or MIT; MIT is selected.
- unicode-ident's existing `(MIT OR Apache-2.0) AND Unicode-3.0` requires retaining the
  Unicode notice too. regex-syntax also carries its historical Unicode data notice under
  `src/unicode_tables/LICENSE-UNICODE`; root metadata alone is not a notice inventory.
  These are unchanged old archive bytes, not newly introduced licence/scope exceptions.

B's independent cargo-deny repeat passes licenses/bans/sources. Its Linux graph does not
cover r-efi; the full-archive inspection above supplies that review. All three original
unused-allowance warnings remain in [stderr display](deny-check.display.log): BSD-2-Clause,
BSD-3-Clause and Apache-2.0 WITH LLVM-exception. The display removes one final blank line;
the exact raw stderr remains in B scratch, bound by offline-commands.json. No policy edit, new exception or speculative
revote of unchanged accepted dependencies is requested. Preserve notices in any later
separately authorized distribution; this review authorizes none.

## Newly executed versus inherited evidence

**New B execution:** [exact offline commands and output digests](offline-commands.json).
B copied the supplied source/cache/controls into `/tmp/u4-b-c1-review/repeat`, verified the
accepted image and repeated tool version checks, full and Linux metadata, full and Linux
locked offline fetch, and cargo-deny licenses/bans/sources: **11 commands, all exit 0**.
Every stdout/stderr is byte-identical to A's corresponding receipt. Raw B outputs remain
under `/tmp/u4-b-c1-review/output`; duplicate metadata is not republished.

Each container used `--pull never --network none --read-only`, user 1000:1000,
`--cap-drop ALL`, `no-new-privileges`, empty private Docker configuration and `/usr/bin/env -i`.
The entire private source copy was mounted read-only. Only the copied cache and private target
were writable; only the copied `.global-cache` changed. Original private inputs were never
mounted into a container. Accepted tool origins/full outputs are included: rustc 1.99.0
`b940084d7eb6a299eb4bfeb8e34901bc051e7ac4`, Cargo 1.99.0
`5f94df4789f005f9a352888e8355ffc645b7ed0e`, cargo-deny 0.20.2, rustfmt 1.10.0-stable,
clippy 0.1.99; Cargo reports Debian 12 bookworm, Linux x86_64, LLVM 23.1.1 in rustc output.
These are tool/metadata checks, **not native tests or dependency execution**.

The independent host reviewer verified 88 saved private receipts and 1,719 cache files,
plus the 35 copied index records. Five host tests pass, with **16 refusal subcases**:
nine lock faults (including both actually rejected intermediate locks), five graph faults,
and two declaration/partial-text substitutions. Positive controls are restored after lock
and graph mutations. Inputs stay in memory. Scripts use only stdlib; no project module or
editable checkout is imported. The loaded B helper's origin is asserted explicitly.
[Validation](validation.json) records commands, final lint/format checks and the initial
helper lint correction. No runtime/full suite or historical test suite was claimed rerun.

B compared all 4,427 original private files before/after: bytes, sizes and mtimes unchanged
(atime is not claimed). The private source equals the 2,619-file export of experiment source
except exactly its manifest and lock. B's target contains only `.rustc_info.json`, identical
to A's; no object, library, probe, executable or build-script output was produced.

**Inherited A execution:** original cache acquisition; both precise offline updates; the
sole online metadata archive retrieval; original feature-tree commands; original failures,
source extraction, preservation history and prior suites. B inspected their receipt bytes
and command scope, but did not rerun updates or online access. A records 35 inherited index
requests, zero new index requests and exactly 35 HTTP-200 archive requests. B independently
compared that URL set with the final lock's `static.crates.io/crates/name/version/download`
set and hashed the raw trace binding. The proxy's host/port allowlist is not a packet firewall;
this is a recorded-request audit, not a new network-isolation proof. No API/advisory request,
credential access, download, dependency build or execution was performed by B.

**Inherited coordinator review:** the README at `U4-K2-C1-actual-candidate-review-v1` records
its own receipt/archive/predicate checks and no Cargo execution. Those checks are not counted
as B execution. Old K1 native/fault results and semantic/coverage receipts remain historical.

## Exact remaining decisions and C2 binding

1. Javid: accept or reject the actual candidate above, including its manifest, complete
   lock, full/Linux graph and features, archive/cache/licence evidence. B recommends acceptance;
   no new licence exception is needed and no acceptance record is fabricated here.
2. Separately release or defer C2's **bounded offline standalone canonical/hash/software
   probes** from the exact reviewed construction plan. No substantive scope correction is
   needed. Its previously prospective dependency references now bind to this actual lock,
   manifest and cache inventory, not the rejected lock or newer published main. Preserve
   the root package/dependency identity when constructing the private probe workspace so
   `--locked --offline` can use this lock; if a different probe layout requires a lock delta,
   return that exact delta before resolving it. Do not broaden C2 to an engine build.

The existing C2 requirements remain concrete: freeze the 4,096 finite-float sweep and
boundary/refusal vectors before probes; check canonical bytes and hashes, u128/numeric-marker
handling, installed canonical/M/B inputs, and separately built debug/release software paths.
Actual sha2 source selects `soft::compress` under force-soft before x86 branches, but neither
that source nor metadata proves scalar machine code, no SIMD, hash correctness or canonical
parity. C2 still owes actual cfg/flags/build-script reads, link/disassembly of the reachable
hash path, known-answer runs and an explicit decision for auto-vectorization findings.
Its incidental ABI/libc distinction is already explicit in A's plan. Nothing was compiled
or probed to preempt that decision here.

C3 image/distribution, live dependency changes, final binary/host authority, public K2,
component fidelity, remote CI, performance qualification and closure remain separate.
U0024 remains in force. Stop for coordinator reconciliation.
