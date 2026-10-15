# U4-M-policy-artifact-adoption-v1

**DRAFT / NOT READY FOR ADOPTION APPROVAL: AD-M1 test correction pending.** Generation was authorized and executed
by Javid. Its candidate has not been installed in the canonical artifact directory.

After AD-M1 reconciliation, the proposed decision is exact administrative adoption of candidate manifest
`b19016be07307ed987037d8a079f85af0366eab018b1132c2668394acd756bcc`, generated from source
`0cf24d91eeca5cc45182eb6fb03202677fd97dcb` and frozen input manifest
`368c7e44dedd8586f2957f9e27030ce61573d3b9675f2f0df27e70c111abf32a`.

The [placement plan](placement-plan.json) binds all nine changed paths and the exact
[unapplied test/review patch](adoption-bindings.patch). Placement targets only the frozen
A checkout, preserving its HEAD and index, and leaves the changes unstaged/uncommitted:

- Replace four artifact metadata members: GENERATOR.json, MANIFEST.json,
  u2-inputs/SHA256SUMS and u2-inputs/support-files.json.
- Add u2-inputs/support-policy.json. All 44 other candidate members remain unchanged.
- Update three current-adoption test bindings, including the protected historical-snapshot
  test's current manifest/review pointer and its descriptive 48→49 member count.
- Add a new U4 administrative review record. Preserve prior U2/U3 review records and all
  historical snapshots unchanged.

The [proposed review bytes](proposed-adoption-review.json.txt) have no authority until this
exact decision is approved. Their `independent` field is the existing administrative
human-adoption carrier requirement, not a claim of a new independent technical review,
measurement, or accuracy validation. Scratch tests exercise the conditional future state;
they do not establish live adoption or close the current real-adoption skip.

The audit found zero numerical changes: all 1,008 nominal rows (queries, counts, timings,
unknowns, stipulations and provenance) and all four real precision refusals are byte-identical.
The generator's sole changed metadata field is its whole-script fingerprint; its embedded
oracle, environment, upstream pin and numerical outputs are unchanged. The selected source
policy and input inventory were accepted earlier; this decision adopts their generated
artifact, not a new policy.

After approval, the coordinator prepares a commit-pinned, human-only placement command with
read-only preflight, exact old/new member checks and strict verification. No oracle or input
staging runs again. A's source remains held locally until the combined compatible state is
checked and separately committed/published. Adoption does not release K2 or resolve K1's
review findings. Commit, push, infrastructure and sprint closure remain separate.

AD-M1: the prospective policy direct-entry control still unconditionally expects stale
currentness. Actual strict currentness succeeds with this candidate, so the control fails.
B must correct and discriminate this transition; the final path selection will be revised
and verified before asking Javid to approve adoption. The current nine-path plan is a draft.
