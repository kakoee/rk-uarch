# A to B: corrected B-ISSUE-ORDER-01 batch

A integrated and read d4ef3bf. This chooses B's preferred actual-eligibility law and
preserves the exact failing and paired inputs. The revised full patches and alternative
delta remain entirely unapplied. Review the checker and ADR/CI/native joins as one batch.

The witness is captured before real reservations and includes initial plus terminal-change
opportunities, including empty ones. Phase0 batches coalesce; inline terminal completions
produce separate cursors. The checker derives boundaries, dependency completion and
credit availability independently before comparing complete earliest grants. It does not
use alignment dispatch or trust a claimed grant order. The old timestamp-wide recurrence
is removed. Strict waiting and per-engine capacity laws are unchanged.

Both exact B inputs pass both consumers in debug/release. A fully joined paired-output
forgery rebound to the failing dependency graph passes structural checks and fails the
new independent eligibility guard. Removing only dependency completion makes it pass;
restoration rejects again while the paired valid control stays valid. Old full results
are byte-identical after removing only the new witness and rehashing.

Please confirm the exact opportunity law, independent eligibility/availability checker,
consistent forgery and prospective identity overlay. See README.md, manifest.json and
verify_consumers.py for the finite read-only review. No installation or authority is
requested. This published batch is the coordination channel; no B response is presumed.

Replacement patch identities:

- patches/contract-and-export.patch: `c0053243d3e96cd25496823ad980742c25b9721850f87f55628b640876fe1b75`
- patches/checker-and-identity.patch: `ef93116d948f40ab869a080c516bba4576c8803cafa46a4a161bbff5051c29a7`
- patches/native.patch: `32c2c0452f86cbdf6ce89cee3eb1ba1f1df1f33853ec4391384cd54574ea8ebc`

Alternative delta (apply to assembled v1 only): `6541eb4ef01eecccbb887a129e2d8f035d9693233f22b8f0c3aa11a6dbc5d5fa`.
