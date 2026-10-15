# C1 actual dependency candidate: coordinator reconciliation

Reviewed publication: `cd273b99c6b9d68ed2dd07d10f8ffad4bedbadb0`.
Author package: [A's precise C1 continuation](../U4-A-K2-C1-precise-v1/README.md).

The recorded version mismatch is resolved. The actual candidate passes the unchanged
28-existing-plus-eight-additions predicate. This is ready for B's bounded dependency
review, not final dependency acceptance or C2 release.

Candidate lock SHA256:
`cbe9a580e0c6209abdb34be23965c2fe2f75b5970819d2021c943e2e02d939be`.
Construction plan SHA256:
`4a5cbb16f5f249234d8ffc0a0e01476c89f4769a57ab96f422ff3c10093eebd5`.
The experiment remains pinned to source `0718955cc0656e5bac4688d4696abbd547cb4186`;
publication on newer main does not change that experiment's identity.

## Coordinator checks executed

- Inspected and ran A's read-only `verify_receipts.py` using the coordinator Python
  with `-I -B`. It passed the actual transitions, unchanged whole-lock predicate,
  seven in-memory refusal controls, graph/feature checks, command/output bindings,
  offline-repeat identities, preservation records, links and package inventory.
- Independently read and hashed all 88 files listed in `private-receipts.json`
  beneath `/tmp/u4-k2-c1-precise.styffox_`; every byte size and SHA256 matched and
  none was missing.
- Independently hashed all 35 actual downloaded `.crate` archives against the
  published archive hashes. The author verifier separately binds those hashes to
  the exact lock checksums.
- Independently compared the full metadata package identity set with the actual
  candidate lock: all 36 name/version/source tuples match exactly.
- The tracked worktree and index were clean at the reviewed publication. Existing
  untracked reviewer evidence was preserved.

No Cargo command, container run, fetch, compilation, native test, full suite or CI
was executed by the coordinator for this reconciliation. A's tool execution,
offline metadata/fetch, feature derivation and cargo-deny results remain author
evidence. Receipt hashes establish identity, not independent reproduction of
those commands or a complete licence judgment.

## Next step

Send [lane-B.txt](lane-B.txt) to the existing B session. It reviews the real resolved
candidate, including the actual licence texts and full versus Linux graph scope.
The old `r-efi` archive's notice is in `AUTHORS`; Linux cargo-deny does not cover
that full-only node. The recorded `force-soft` features do not establish the later
compiled-code property.

A waits for this reconciliation. Final dependency acceptance and the bounded C2
probe release remain separate decisions. No live manifest/lock change, new licence
exception, image publication, public K2 implementation or qualification follows.
U0024 deferrals remain unchanged.
