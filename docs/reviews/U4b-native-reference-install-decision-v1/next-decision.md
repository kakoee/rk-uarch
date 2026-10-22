# Install the independently reviewed U4b successor

Status: human-installed and committed as `36262735ba21cc75c9373216ed89153e6f31c2d6`; coordinator verification passed on 2026-10-22. Publication is authorized.

Approval: Javid replied “yes” to “Approve this exact installation, normal commit, and publication after receipt verification?” This covers the exact transition and normal publication after verifying the human commit receipt; no second publication vote is required.

## Exact action

Install the complete v2 transition from publication
`93a4df2fd0bdc4185874b8928ba2146b25519358`, make a normal local commit,
and publish normally after coordinator receipt verification. Apply neither v1
nor the separate correction patch in addition.

- Package: `docs/reviews/U4b-native-reference-implementation-v2/`.
- Patch SHA-256: `66a6721b64554f5f8ce92d8aab951249e81fb30a50c9392b791321ec6c53a57c`.
- Reviewed source tree: `6b186db2dd90c09f97ba86282dfaaadd234da7cd`.
- Complete transition: 42 paths.
- Expected staged tree on the exact publication:
  `ac36267b672cde611e588e95f5135b3c4855b7d1`.

The change installs the approved nominal TPU v5e reference model and 52-unit
workload implementation in the existing native engine, with the corrected
resource loader and dependency-readiness checker. Published STUB assumptions
remain STUBs. No performance optimization or new assurance framework is added.

## Review and limitations

The same independent reviewer resolved B1 and B2 in section 8 of
`../U4b-native-reference-independent-review-v1/README.md` and found no remaining
installation blocker. Earlier independent evidence and the author campaign are
reused with their original attribution. The reviewer independently exercised
packaging, replay, lawful boundaries and the new guard's removal/restoration.

F3 (non-memory arbitration checking), F4 (direct oversized /4 error code), and
F6 (critical-path adjacency) remain explicitly unresolved and non-blocking.
F5's staging-buffer serialization is disclosed in the v2 handoff and must remain
visible before any U5 prediction freeze. The narrower checker scope belongs in
a later interface revision; zip-import support is not required. Neither note
adds an installation gate or changes this accepted patch.

This is not TPU accuracy validation, U4 closure, a device measurement, a U5
prediction freeze, or resolution of human L1/U0024 obligations. Deferred runtime
optimization and compatibility cleanup are outside this installation.

## Coordinator verification

`checks.json` records independent temporary-index application on both the
recorded base and exact publication. The reviewed tree reproduces and all 42
postimages match on published main. The coordinator's real index, tracked
checkout and independent review were untouched. No tests, native builds or
campaigns were repeated.

## Human procedure, after approval

The existing `CLAUDE.md` instruction is: “Agents propose and stop on contract/,
tests/golden/expected/, CLAUDE.md, docs/decisions/.” The human applies and commits
this protected transition. Ordinary Git commands suffice; no new helper is needed.

Run from the coordinator checkout. Stop on any failed check, conflict or hook;
do not reset unrelated work or bypass hooks. Untracked review/decision files are
left out of the source commit.

```sh
cd /home/jjaff/AI-infra-simulation/rk-uarch
(
  set -eu
  test -z "$(git status --porcelain --untracked-files=no)"
  test "$(git branch --show-current)" = main
  git fetch origin main
  git merge-base --is-ancestor 93a4df2fd0bdc4185874b8928ba2146b25519358 origin/main
  git merge --ff-only 93a4df2fd0bdc4185874b8928ba2146b25519358
  test "$(git rev-parse HEAD)" = 93a4df2fd0bdc4185874b8928ba2146b25519358
  u4b_patch=docs/reviews/U4b-native-reference-implementation-v2/transition.patch
  echo "66a6721b64554f5f8ce92d8aab951249e81fb30a50c9392b791321ec6c53a57c  $u4b_patch" | sha256sum -c -
  git apply --check --index "$u4b_patch"
  git apply --index "$u4b_patch"
  test "$(git write-tree)" = ac36267b672cde611e588e95f5135b3c4855b7d1
  UARCH_HUMAN=1 git commit -m "feat(reference): install reviewed U4b native workloads and nominal model"
  git show -s --format='commit=%H%nparent=%P%ntree=%T' HEAD
  git status --short --untracked-files=no
)
```

Return the commit receipt for verification before publication. If main has
advanced beyond the pinned publication locally, stop for a bounded applicability
check instead of resetting history. Review/decision publication can follow
separately without changing executed evidence.

## Installed checkpoint

The human installed all 42 paths and committed with normal hooks. The complete
committed tree equals the approved installation tree exactly. `installed.json`
records verification. No test, campaign or native build was repeated because
the installed source is identical to the reviewed source. The independent
review remains unchanged and untracked in the coordinator checkout; this
record preserves its identity and adjudication without editing reviewer files.
Publication of the human commit and this installation record is covered by
the approval above. U4 closure is not claimed.
