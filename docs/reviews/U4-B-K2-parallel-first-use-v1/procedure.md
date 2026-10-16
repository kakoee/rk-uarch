# Guarded placement and complete first-use procedure

**Preparation only. Do not execute placement or restart the campaign from this package.**
This is the exact baseline scheduler replacement. A's case/startup/protected candidate
remains unapplied and needs one combined source/runtime reconciliation before selecting
what to place. Do not install this baseline and then silently overlay A's changed imports.
The original sealed root and stopped evidence stay untouched.

Original root: /var/lib/rkuarch/k2/candidate-04-first-use-v1.
Proposed distinct root: /var/lib/rkuarch/k2/candidate-04-parallel-v1.
The accepted image already supplies the native loader/DSOs. The unchanged mounted Python
and five site packages supply the host resolver/checker; the image is not assumed to
contain Python or pytest. Docker is only the isolated runtime: the real runner opens and
hashes the actual candidate ELF descriptor for each fresh native process. No Docker
wrapper replaces that executable identity.

The baseline delta places exactly seven files: four helpers under helpers/; under
authority/, helper-manifest.json, actual parallel-preflight.json and runtime-release.json.
All regular files root:root0444; new directories0555. No original inode, engine HostRecord,
selector, library, corpus, source, support/artifact or workflow is replaced. All original
mounts remain read-only. The selector remains the existing root-owned file mounted at
/etc/rkuarch/k2-host-selector.json inside the container; no host /etc change.

1. Coordinator reviews the exact published helper commit and decides the combined A/B
   source/runtime route. A's proposed host/runner/protected bytes cannot pass the old
   BuildInputs rehash by relabelling them. New source/support/runtime decisions, if needed,
   must have their actual provenance and lifecycle; this helper creates no authority.
2. For the exact selected baseline helper bytes, publish the coordinator-owned record at
   docs/reviews/U4-K2-parallel-placement-v1/placement.json. Required fields are enforced in
   prepare_placement.py: status=reconciled-for-human-placement, full helper publication
   commit, helper_manifest_hash, policy_hash and original_runtime_release_hash. It does
   not repeat the already accepted engine/dependency/licence vote. A combined-source
   candidate requires its own exact bindings; do not use this baseline record for it.
3. In the normal B clone, with clean published proposal bytes, run prepare_placement.py
   --repo /home/jjaff/AI-infra-simulation/rk-uarch-u4-b --helper-commit FULL_SELECTED_COMMIT
   --output /tmp/u4-k2-parallel-placement-stage1-new. It verifies Git ancestry/blob hashes,
   original release and root-owned nonwritable ancestors, then writes literal commands
   and postimages only. Read the generated human-stage.sh. Human root placement is a
   separate explicit action; the helper never calls sudo/root or writes authority itself.
   Stop if any target already exists, any hash differs, or the selected candidate changed.
4. After human placement of the first five files, run the displayed import-only command:
   python3 launch.py preflight --output /tmp/u4-k2-parallel-preflight-new.
   Only the explicit --execute-placed switch executes it. It checks original/new immutable
   trees, image libraries and private origins, with no selector, resolver or native call.
   Nonzero exit or wrong hash stops; preserve evidence. No preflight is invented here.
5. Prepare stage2 with the same repo/helper-commit, a new output directory, --preflight
   /tmp/u4-k2-parallel-preflight-new/parallel-preflight.json, and --placement-commit the
   actual full published coordinator record commit. The helper verifies actual receipt
   bytes and emits two literal files: saved preflight and bound release. Human review and
   root placement remain separate. There is no placeholder release in this package.
6. Independently compare seven actual installed postimages, ownership/modes, original
   identities, original acceptance publication and the coordinator Git blob. Verify normal
   published history contains both pinned records. Runtime declarations do not authenticate
   themselves. No writable alias of sealed inputs may be changed by a trusted administrator
   during execution. Capability or security changes are not a fallback.
7. Only after the coordinated restart decision, print/review and then explicitly execute:
   python3 launch.py campaign --output /tmp/u4-k2-parallel-campaign-new --execute-placed.
   This future command uses genuine parent host resolution and dynamic case workers,
   all798 calls, fresh processes, full per-output validation and exact deterministic
   collection. Actual affinity/quota/memory select workers at launch; no hardcoded16.
   Startup/case/total times and worker RSS are separate.2GiB receipts/7200s outer cap;
  600s case cap, original production per-call limits. Any loss/error stops and preserves
   partial receipts; do not reuse old output or skip previously checked slots.
8. Require launch exit0, final campaign.json complete798 with all780 successes/18 expected
   refusals, matching full before/after input snapshots and exact original-plan comparison.
   Then run launch.py replay against that same output with --execute-placed. Require
   replay exit0, original K06-02/S08 fault/restoration evidence and matching additional
   parallel-replay-inputs.json. A replays.json alone is insufficient if later postchecks
   fail. A coordinator independently reviews actual results; no automatic qualification.

All commands above are future human/coordinator steps. FULL_SELECTED_COMMIT and the
placement commit are deliberately required external identities, not invented pins or
executable CI placeholders. prepare_placement refuses absent/unpublished/mismatched values.
The current proposal can be inspected/printed now; no root stage or full campaign ran.

Applicable public V01–V28 mapping and all pending/private distinctions remain exactly
../U4-B-K2-deployment-first-use-v1/validation.md. The100 private Wheel schedules are not
public observations; no human L1/component/performance credit is manufactured. U0024,
read-closure limitations and later first-use/component/C3/U4 gates remain unchanged.
