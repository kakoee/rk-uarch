# U3-artifact-adoption-v1 — proposed decision

Approve adoption of the complete **48-file** human-generated candidate with manifest:

`1873760cdbc06d9f1508ac4e515dfc0acefd7b2577a230047a38d3038098105a`

It replaces canonical manifest
`20eee19b0e864ad07a7b122da7544e385116fdd50d279e1fac1bfbbf03a697ad`
in A's `contract/vendor/rk-sim@1e5706e0ebfcc67c1a7333079a35b75f693e9963`.
The source is `187fe3b035bee9cbeae13b03c8b4ac6ef0ee276f`; input digest is
`27c6238d42e57dc4f2b1baf0c8846c11f1eec2968176dcefcdc463beb64bc80f`.

Approve the exact [binding patch](adoption-bindings.patch), SHA256
`55e476566b5c87a9f8329e05d5b3f5a413ae1a35d17b6b620ab128796dbdc228`,
including the proposed administrative review bytes, file SHA256
`58f0f04b55aa228c9831cc2427f0f86a4aa3c1ae8f9327eb3660ae160323300c`.
The patch changes three current-binding tests and adds a separate U3 adoption record;
it preserves all assertions, previous reviews and historical data. The complete candidate
changes only three artifact metadata paths. Together these are seven changed Git paths.

Reason: the reviewed additive RoPE implementation expands support from 87 to 97 files.
The human's two runs were identical. All 1,008 nominal rows and four real refusals are
byte-identical to the previous artifact. The [coordinator audit](README.md) and conditional
scratch placement checks passed (784 tests, 28 explicit protected-activation skips).

This acceptance authorizes the exact complete artifact selection and required binding updates.
It does not claim physical-v2 parity, prediction accuracy or new evidence eligibility.
Human placement/local commit will be prepared as a separate step following approval.
Protected-test activation, source push, runner/nightly, independent review and closure remain
separate. The proposed approval record has no authority until Javid actually accepts this
named decision. No live placement or adoption is claimed by this proposal.
