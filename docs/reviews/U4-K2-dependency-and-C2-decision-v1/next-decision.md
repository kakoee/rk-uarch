# Exact dependency acceptance and separate C2 probe permission

Status: proposed to Javid; neither decision recorded as approved.

B review: `32ab29c76b0bb7325366f09792a89dfa823a7d41`,
[bounded handoff](../U4-B-K2-C1-candidate-review-v1/README.md).
A candidate: `cd273b99c6b9d68ed2dd07d10f8ffad4bedbadb0`,
[actual C1 package](../U4-A-K2-C1-precise-v1/README.md).

## Decision 1 — U4-K2-dependencies-v1

Accept the actual resolved dependency inputs below, including the full and Linux
graphs, exact versions/sources/checksums, requested and unified features, downloaded
archives and their reviewed licence/notice obligations. This accepts the candidate
for subsequent authorized construction; it does not install a live manifest or lock.

All paths in this table are relative to `docs/reviews/U4-A-K2-C1-precise-v1/`.

| Input | SHA256 |
| --- | --- |
| `candidate.Cargo.lock` | `cbe9a580e0c6209abdb34be23965c2fe2f75b5970819d2021c943e2e02d939be` |
| `scratch.Cargo.toml` | `60299ba9498e506010a5c908ef8017beb2279d1aedab409a7fc21601d3b35ee0` |
| `cache-inventory.json` | `ce219674649c7e77ce84806db559d8473a6c6a62b5bad7aa3ff0e93486f30148` |
| `metadata-full.stdout` | `cf727489186faf665be42d3a7f8098c664ce775810f9a06df8fbe069a9289b41` |
| `metadata-linux.stdout` | `e72003c00eeedc6278754e8e6a64b15c753a5f87f993272c794e2668526aa7e7` |

The 28 retained identities and eight additions are exactly those in the reviewed
construction plan SHA256
`4a5cbb16f5f249234d8ffc0a0e01476c89f4769a57ab96f422ff3c10093eebd5`.
The full graph has 36 nodes including the workspace; Linux has 35. The old r-efi
node is full-only. B inspected its actual AUTHORS notice separately from Linux
cargo-deny. Select the reviewed MIT alternatives, retaining the existing Unicode-3.0
conjunct and all required notices. No new licence exception or distribution is
authorized. B's exact selections/notices are in its `independent-review.json`, SHA256
`1bb2e09a1c4c5b0d51e6db01c7f3d3701936fcf6550554b08050ba46a022a02f`.

## Decision 2 — U4-K2-C2-probes-v1

Separately authorize A to construct and run only the bounded standalone offline
software/canonical/hash probes in the existing
[construction plan](../U4-A-K2-semantic-construction-v1/construction.md), under its
C2 and canonicalization-matrix sections, bound to Decision 1's actual inputs.

This permits private debug/release probe compilation, the accepted dependencies'
necessary build scripts/procedural macros, and probe execution in the existing
accepted image
`sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523`.
Use `--pull never`, networking disabled, private source/target paths and a verified
read-only candidate cache. Preserve original C1 source/cache/receipts. Use locked,
offline Cargo; no resolution updates or dependency/feature changes.

Freeze the complete prescribed vectors before probes, including the seeded 4,096
finite-float sweep and boundary/refusal cases. Compare actual Python canonical
bytes and hashes with Rust, including installed canonical/M inputs and B's 113
inputs. Pin every source and input: the C1 experiment stays historical at
`0718955cc0656e5bac4688d4696abbd547cb4186`; installed semantic inputs include human
commit `1aae27b298f3a051cc80fe94f4889da260633a0b`. Record the actual current source
used for Python references separately rather than relabelling C1 evidence.

Record actual compiler cfg/flags, build-script activity, binaries, software-path
selection and debug/release reachable hash-path disassembly. `force-soft` is not
proof of scalar machine code. Preserve mismatches and auto-vectorization findings;
return any needed algorithm/dependency/flag change for review. Do not substitute
a SHA implementation or silently normalize away canonical mismatches.

No native engine binary, mapped workload execution, MappedEngineResult output,
public K2 wiring, live dependencies, protected edits, artifact adoption, image
construction/distribution, host authority or qualification is released. C3 and
U0024 deferrals remain separate. The private probe must retain the accepted package
identity/lock; if its layout requires a lock delta, return that delta before resolving.

## Coordinator verification and recommendation

Recommend both decisions, separately identified above. After inspecting B's helper,
the coordinator reran its five host tests (including 16 refusal subcases), verified
all 17 B inventory entries, verified the unchanged A package tree
`a2d8ccf5093d93d8f2ceaf47eefbbc5c69d8686d`, and independently hashed the five inputs
listed above. All passed. Earlier coordinator archive/receipt checks remain recorded
in [C1 reconciliation](../U4-K2-C1-actual-candidate-review-v1/README.md).

B's 11 offline/tool checks, archive-member/notice inspection and preservation run
remain B-executed evidence; the coordinator did not rerun Docker, Cargo or a full
suite here. No compilation has occurred in this reconciliation.

[Prepared A handoff](lane-A-after-approval.txt) is conditional on both decisions.
Do not send it as an execution release before approval. A returns C2 evidence for
coordinator/B reconciliation; success alone does not release K2 implementation.
