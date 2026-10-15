# Candidate audit and draft adoption proposal — AD-M1 pending

The human generated 49 files and verified them identical in a second process. Candidate
manifest: `b19016be07307ed987037d8a079f85af0366eab018b1132c2668394acd756bcc`.
[Generation receipt](human-generation-receipt.json) and the two saved status lines preserve
that execution; the coordinator did not rerun the oracle.

[Read-only audit](audit.py) checks the unchanged frozen source and environments, human run
bindings, complete candidate manifests, source/member/input-copy attribution, strict new-policy
currentness and the full nominal matrix/refusals through the real consumer audit. Input
preparation and oracle entry points are disabled during this audit. [Results](audit.json)
record all changed members and receipt hashes. All 1,008 nominal rows and four precision
refusals are byte-identical to the current snapshot. Decode write counts remain null;
vector counts are still absent. This establishes reference reproducibility, not physical,
native or silicon validation.

The member delta is four changed metadata files plus one new policy file. The embedded oracle
program and locked oracle environment are unchanged; GENERATOR.json changes only its whole-
script fingerprint. Frozen input copies match exactly, including the two outer component/model
copy sets. A remains clean at the exact human source commit. The existing artifact remains
stale against that source until the separately approved placement happens.

[Next decision](next-decision.md) and [placement plan](placement-plan.json) describe nine
changed paths. The patch updates only current test bindings and introduces a new U4 review;
old U2/U3 records remain intact. The prospective administrative review is stored as `.json.txt`
and is explicitly not active authority. No live protected file was edited.

Conditional verification uses a disposable Git archive of the exact source, the saved real
candidate and the exact proposed patch. It does not generate an artifact. See
[verification](verification.json) for executed checks, the corrected test-launch environment,
results and limitations. Scratch success is not a live adoption receipt. No full-suite,
native qualification, hosted CI, K2 implementation or closure is claimed.

## AD-M1: adoption control assumes permanent staleness

The installed B test `test_fresh_direct_valid_controls` asserts that a fresh direct
`vendor_rk.py --check` always exits 1 with `input support inventory changed`. In the
conditional candidate copy it correctly exits 0. This is a prospective test-state
defect, not an oracle mismatch. The strict implementation remains unchanged.
[B follow-up](lane-B-adoption-control-followup.txt) requests a bounded test correction
with genuine compatible and stale controls. No adoption approval is being requested
until the correction and final placement scope are reconciled.
