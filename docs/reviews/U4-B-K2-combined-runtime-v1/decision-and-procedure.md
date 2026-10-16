# Proposed exact human decision and guarded sequence

Approve only after coordinator review of the exact published candidate.json and this
package's executed checks. No decision is already implied by preparation authorization.

**Approval question:** Do you approve the exact published U4-B-K2-combined-runtime-v1
candidate and its normative-addendum.txt: the separately bound protected hardware.py runtime
copy coexisting with unchanged canonical generator/support and original native build source;
human placement into the new immutable combined root; authority-free preflight; coordinator
publication of the actual placement/preflight binding; human installation of only that exact
runtime approval selector/release; and a fresh complete 798-call campaign followed by the
original six-way and relocated corruption/restoration replay, under the unchanged accepted
local image/security/resource limits, with no canonical installation, artifact lifecycle,
performance/qualification claim or change to U0024?

The governing U0011 M/host mechanism requires separately reviewed published human authority.
U0002 distinguishes artifact integrity from current compatibility and binds the actual
reachable generator/support closure; hardware.py is reached there. U0024 does not waive
protected installation or lifecycle requirements. Therefore the precise prospective U0011
text in normative-addendum.txt is a required decision dependency. Its unapplied patch is
provided; B has not installed it. Acceptance must expressly cover this narrow runtime copy,
not claim that it is current under the old artifact. If the coordinator/human requires a
unified native build/runtime source identity instead, stop: that is a different decision
requiring new native BuildInputs/binaries/jobs/authority and a canonical support lifecycle.
No such reconstruction is proposed here.

## Record order (no circular hashes)

1. Publish this candidate/helper package; record its real full commit and candidate byte hash.
2. Javid's exact response is recorded in a later published
   `docs/reviews/U4-K2-combined-runtime-authorization-v1/decision.json`. Required fields:
   `format=uarch-k2-combined-human-decision/1`, `accepted_by=Javid (@jjaffari)`, actual `reply`,
   `scope=isolated-protected-runtime-placement-preflight-and-798-call-restart`,
   `amendment_hash` from candidate.json, `binding` from bindings.identity(candidate bytes),
   and `publication={helper_commit: actual package commit, candidate_hash: actual hash}`.
   Coordinator records the genuine response only; do not populate yes speculatively.
3. Human places payload, runs authority-free immutable preflight and preserves its full output.
4. Coordinator verifies the actual placed file/mode/owner inventory, command, mount restrictions,
   exact imports and native_calls=0, then publishes `placement.json` beside decision.json:
   `status=actual-placement-and-preflight-reconciled`, same `binding` and `publication`,
   actual `decision_commit`, `decision_hash`, `preflight_hash`. Retain actual observations
   and receipts; declaring that status is not a substitute for them.
5. The binding renderer checks those actual published blobs and preflight, then renders the
   five-file authority placement. Selector binds hashes of decision, placement, preflight and
   release plus actual decision/placement commits. Release binds candidate + original native
   identities and all predecessor hashes. Selector is external to the runtime payload.
   The human places it root-owned/read-only. No self-referential package/build/profile hash.
6. Launcher independently rechecks Git publication, actual immutable files, native bindings
   and approvals before campaign/replay; only production resolution creates capabilities.

## Exact commands and stop points

Use the accepted existing host interpreter and a clean checkout of the **actual helper
publication**. The symbols below are required future inputs, not literal fake SHA values:
`REPO` is that normal checkout, `PUB` its full published helper commit, `DECISION` the real
human decision publication, `PLACEMENT` the later actual coordinator receipt publication.
`PKG=$REPO/docs/reviews/U4-B-K2-combined-runtime-v1`.
Use `env -u PYTHONPATH -u MYPYPATH -u VIRTUAL_ENV -u UARCH_HUMAN` and the accepted host Python
with `-I -B -c` to insert **only PKG for these stdlib helpers**, then run the named script;
there are no project imports in the host tools. For example:

```sh
/home/jjaff/AI-infra-simulation/rk-uarch/.venv/bin/python -I -B -c \
 'import runpy,sys; p=sys.argv.pop(1); sys.path.insert(0,p); runpy.run_path(p+"/prepare.py",run_name="__main__")' \
 "$PKG" payload --repo "$REPO" --publication "$PUB" \
 --output /tmp/u4-k2-combined-payload-v1
```

This writes a complete 39-file payload and exact postimages plus a deliberately disabled
placement preview. It runs no sudo/container/authority. Never use a live-tree overlay.
After actual human approval, run the same tool with `placement --decision-commit "$DECISION"`
and a new output `/tmp/u4-k2-combined-placement-v1`. It rereads the exact published source,
patches and helpers; verifies all postimages; embeds all39 files in `human-place.sh`.
Inspect the script/postimages and compare their hashes with the coordinator's publication
before the human executes it as root. B never invokes it. The root must not exist; directories
are0555/files0444, no symlinks, no overwrite, no extra file. The original deployment is only
read. Stop on any mismatch. Human-only root placement is the sole privilege step.

Render launch command by the analogous runpy invocation of `launch.py`:

```text
preflight --repo "$REPO" --publication "$PUB" --output /tmp/u4-k2-combined-preflight-v1
```

Inspect it, then after approved placement add `--execute-placed`. This starts only the accepted
local container with all original/new input mounts read-only. Both selectors are absent; process
execution is blocked inside the preflight. It verifies mounted Python/site/image DSOs, exact
project origins, native source/data and helper inventories. Do not substitute private-test
preflight. Preserve stdout/stderr, preflight.json, operational and launch receipts. Failed or
partial preflight stops; do not append authority or rerun into an occupied output.

After actual placement/preflight publication, render binding with:

```text
prepare.py binding --repo "$REPO" --publication "$PUB" --decision-commit "$DECISION"
 --placement-commit "$PLACEMENT" --preflight /tmp/u4-k2-combined-preflight-v1/preflight.json
 --output /tmp/u4-k2-combined-binding-v1
```

The tool refuses missing/mismatched/unpublished decisions, incomplete/private preflight and
nonempty authority target. Human verifies and executes only this new exact script; it adds
five files under the previously empty authority directory. It never copies an acceptance
token and does not replace the old native selector. Actual root-owned selector placement is
verified independently by launcher and container. No host/security setting changes occur.

Render, review, then explicitly execute-placed `launch.py campaign` with the same repo/PUB
and **fresh** `/tmp/u4-k2-combined-campaign-v1`. If that path exists choose a new reviewed fresh
path; never delete/reuse old evidence. Only after full success run `launch.py replay` with
that same new campaign output. It requires the matching complete798-call record, uses saved
real outputs, blocks process/producer calls and records corruption/refusal/restoration.
No calls from `/tmp/u4-k2-approved-campaign` are counted. No broad/native rerun is preparation.

## Interrupted placement and recovery

Scripts use no-clobber and exact absent-target checks. An interrupted payload or authority
placement is intentionally not resumable. Preserve its script/logs/postimages and root;
launcher rejects incomplete membership before imports/authority/native. Have the coordinator
inspect the partial state. A human may quarantine it by a separately recorded rename to an
unused sibling path, retaining every inode and log; never overwrite, merge, chmod an old
receipt into acceptance or silently delete it. Re-render from the same publication/approval
only after the exact intended target is absent, or obtain a newly bound decision for a
changed target. A partial authority directory likewise needs recorded human quarantine and
fresh placement/preflight reconciliation. Original deployment and stopped evidence remain
untouched. Runtime failures preserve all outputs and require a new output; no completion
credit carries across failed attempts.
