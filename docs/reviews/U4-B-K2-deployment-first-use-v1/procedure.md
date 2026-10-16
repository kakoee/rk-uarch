# Guarded human deployment/run procedure — NOT EXECUTED

Only execute after the actual decision described in decision.md. Commands below are a
proposal, not an instruction released by this preparation task. Stop on any hash, ownership,
publication, preflight, namespace or semantic failure. Do not repair by installing packages,
changing security, rebuilding binaries, regenerating jobs or selecting another image.

## 1. Pin published preparation; reconstruct only existing bytes

Use a private export of this package's final published full commit, plus the existing source
paths in candidate-layout.json. Do not run helpers from a later mutable main accidentally.
Fetch/verify the ordinary publication normally before recording the package commit; never
poll CI. Missing old private candidate files are an explicit blocker, not permission to
rebuild or substitute paths. If relocation is needed, individually reconcile same-byte
source paths in a new owned receipt; preserve the frozen destination paths/hashes.

Run as the existing UID1000 user. The following function uses explicit helper imports,
not PYTHONPATH or an editable project; `PKG` is the private pinned package directory:

```bash
set -euo pipefail
PY=/home/jjaff/AI-infra-simulation/rk-uarch/.venv/bin/python
PKG=/tmp/u4-k2-approved-preparation/docs/reviews/U4-B-K2-deployment-first-use-v1
bprep() {
  env -u PYTHONPATH -u MYPYPATH -u VIRTUAL_ENV -u UARCH_HUMAN "$PY" -I -B -c \
    'import runpy,sys; from pathlib import Path; p=Path(sys.argv.pop(1)); sys.path.insert(0,str(p.parent)); runpy.run_path(str(p),run_name="__main__")' \
    "$PKG/$1" "${@:2}"
}
bprep inventory_runtime.py --output /tmp/u4-k2-approved-inventories
bprep materialize.py --inventories /tmp/u4-k2-approved-inventories \
  --output /tmp/u4-k2-approved-payload
```

Both output directories must be new; no authority is created. inventory_runtime.py derives
4532/152 entries from existing CPython/installed RECORD files and refuses changed inventory
hashes. materialize.py copies only declared members into fresh private trees, validates bytes
and confined Python symlinks, and requires the published five-file campaign manifest. The
original sources/cache/evidence remain unchanged; no Cargo/cache/tool execution occurs.

## 2. Human-only new root placement and seal

Exact root: `/var/lib/rkuarch/k2/candidate-04-first-use-v1`. It must **not already exist**.
The human verifies `/`, `/var`, `/var/lib` and any existing rkuarch/k2 ancestors are real
root-owned directories without group/world write. Stop on symlinks, nested mounts or existing
unexpected state; do not change an existing parent to make it pass. New rkuarch/k2 parents,
if absent, may be root-owned0755 under the explicit approval. Inspect `/proc/self/mountinfo`
and refuse a mount at/below the deployment root, including a nested mount in the private
payload. No shared-root alias, active writer or writable bind of the sealed tree is allowed.

After that inspection the human runs the following bounded copy/seal commands, never a
recursive operation on an inferred or empty path. Root can change readonly files; this
procedure relies on the human/Docker administrator holding these exact bytes unchanged
through the whole execution interval. It is not isolation from a malicious privileged host.

```bash
# Human root step, only after checks/approval above. Do not run the Python campaign as root.
sudo /bin/bash -eu -c '
  root=/var/lib/rkuarch/k2/candidate-04-first-use-v1
  payload=/tmp/u4-k2-approved-payload
  test ! -e "$root"
  test ! -L "$root"
  test -d "$payload"
  test ! -L "$payload"
  test "$(id -u)" = 0
  mkdir -m 0755 -p /var/lib/rkuarch/k2
  cp -a --no-preserve=ownership -- "$payload" "$root"
  chown -hR root:root -- "$root"
  find "$root" -type d -exec chmod 0555 {} +
  find "$root" -type f -exec chmod 0444 {} +
  chmod 0555 "$root/python/bin/python3.12" \
    "$root/candidate/targets/debug/debug/uarch-engine" \
    "$root/candidate/targets/release/release/uarch-engine"
'
```

Do not execute this shell block as a substitute for the preceding parent/mount inspection.
The launcher additionally refuses any non-root-owned or writable staged inode, symlink
escape, wrong candidate mode/hash or different helper manifest. Runtime guards require
single-link regular payload files and exact runtime membership. Copying separates original
user-owned inodes; there must be no hardlink/writable-alias path back to originals. Only
Python-distribution symlinks, confined to that distribution, are permitted. Do not supply
a writable mount alias in this or any other container. No immutable flag/security setting,
ldconfig, host-library replacement or host `/etc` installation is proposed.

## 3. Authority-free runtime preflight, then real publication

```bash
bprep launch.py preflight --output /tmp/u4-k2-approved-preflight
# The previous command only prints exact argv. Under the recorded approval:
bprep launch.py preflight --output /tmp/u4-k2-approved-preflight --execute-approved
```

The image is `sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523`,
--pull never, linux/amd64, network none, readonly root, UID1000:1000, cap-drop ALL,
no-new-privileges, existing default seccomp. /tmp is a64MiB nosuid/nodev/noexec tmpfs.
Only /receipts is a writable host bind; no Docker socket, host namespace, device, /home,
original cache or source tree is exposed. Input binds use readonly/rprivate. entrypoint
is `/usr/bin/env -i PATH=/usr/bin:/bin LC_ALL=C /python/bin/python3.12 -I -S -B ...`.
There is no LD_LIBRARY_PATH/LD_PRELOAD propagation or Python site/.pth activation.

Mounts: root/candidate→/candidate; root/python→/python; root/site→/site;
root/campaign→/campaign; root/manifests→/manifests. The preflight mounts **no selector**,
requires its absence, verifies all inputs, interpreter prefix and private module origins,
and imports the pinned host/runner/checker without resolving authority or running native code.
It is capped at120s. Failure stops before authority. Successful imports are the required
new ABI/relocation observation; static library-name/version availability alone is insufficient.

The coordinator then records the actual human reply and publishes four ordinary files at
`docs/reviews/U4-K2-first-use-authorization-v1/`:

| File | Exact construction / provenance |
| --- | --- |
| human-decision.json | Genuine decision only: format `uarch-k2-human-first-use-decision/1`, accepted_by `Javid (@jjaffari)`, reply `yes`, subject equal campaign-plan.json's seven fields. Record only after the actual approval. |
| HostRecord.json | Prior B candidate-04 HostRecord-proposal.json `proposed_fields`, plus exactly `decision: {path: <above path>, byte_hash: <actual decision SHA256>}`. No other field change. |
| deployment-approval.json | Genuine approval only: format `uarch-k2-deployment-approval/1`, accepted_by/reply as actually authorized, package_commit full published preparation commit, subject, runtime_hash, campaign_files_hash, plan_hash. Hashes are SHA256 of runtime.json, campaign-files.expected.json and campaign-plan.json respectively. |
| preflight.json | Exact actual successful /tmp/u4-k2-approved-preflight/preflight.json bytes, never a handwritten success record. Retain launch stdout/stderr/argv/exit receipt privately and link its hashes in the coordinator handoff. |

The approval binds source, actual ELF bytes, profile/corpus/jobs and this runtime/procedure;
no final binary/record/commit is hashed into its own upstream identity. The coordinator also
retains the actual human message/context; JSON shape is not authentication. Publication uses
normal hooks/main integration. No placeholders or future commit guesses are acceptable.

## 4. Verify publication; human places only verified authority

The human/coordinator independently records the full package and acceptance commits and
four published blob hashes (keys exactly the four filenames above, `sha256:` values) in
`/tmp/u4-k2-authority-hashes.json`. Set `PACKAGE_COMMIT`/`ACCEPTANCE_COMMIT` from those actual
published receipts, not from a branch alias. Run:

```bash
: "${PACKAGE_COMMIT:?actual full published preparation commit required}"
: "${ACCEPTANCE_COMMIT:?actual full published authority commit required}"
bprep verify_publication.py --repo /home/jjaff/AI-infra-simulation/rk-uarch-u4-b \
  --package-commit "$PACKAGE_COMMIT" --acceptance-commit "$ACCEPTANCE_COMMIT" \
  --hashes /tmp/u4-k2-authority-hashes.json > /tmp/u4-k2-verified-placement.json
```

This read-only verifier proves both commits are in fetched origin/main, verifies each
preparation blob against the pinned package, verifies all four authority blobs at the exact
commit, matches the original HostRecord fields plus only the genuine decision, and checks
actual preflight/helper/subject bindings. It prints downstream selector/runtime-release
objects; it does not install them. A missing receipt, extra record field, mutable source,
stale preflight or unapproved helper change refuses. No output is genuine authority merely
because this checker can parse it; human publication/provenance checks remain necessary.

Only then the human copies the **exact published** human-decision.json and HostRecord.json
bytes into the two reserved matching paths under root/candidate. Put exact actual
preflight.json into root/manifests/preflight.json. Serialize the verifier's selector object
to root/authority/k2-host-selector.json and runtime_release object to
root/manifests/runtime-release.json. These downstream files are human-installed only after
comparing the returned fields with publication. Use new files (no overwrite), root:root,
0444 and new containing directories0555; seal again and rehash. Refuse any placement beyond
these four files plus the selector. Publish no payload/binary distribution or private cache.

The selector's repository is `/candidate`, record_path is the exact published HostRecord
relative path, acceptance_commit is the real full publication commit and record_byte_hash
is the actual blob digest. The source selector resides under root/authority and binds
readonly to **container** `/etc/rkuarch/k2-host-selector.json`; host `/etc/rkuarch` is untouched.
The final runtime-release binds actual preflight, package/helper/plan/runtime hashes and
published record/decision authority. The resolver's commit field is declarative; the external
publication check above is mandatory. Directory modes/open descriptors alone do not prove it.

## 5. Finite public campaign and fresh-container replay

```bash
bprep launch.py campaign --output /tmp/u4-k2-approved-campaign
# After all genuine authority, publication and seal checks:
bprep launch.py campaign --output /tmp/u4-k2-approved-campaign --execute-approved
bprep launch.py replay --output /tmp/u4-k2-approved-campaign --execute-approved
```

Output paths are exact fresh private UID1000 directories; replay alone consumes the completed
campaign directory and refuses existing replay evidence. Each container mounts the independently
installed selector, resolves debug/release hosts and executes the verified ELF directly by fd.
Per invocation:30s, stdin/stdout64MiB each, stderr1MiB. Entire campaign/replay launcher:7200s,
2GiB receipt cap; limits are operational, not performance. Each container is uniquely named;
on limit/failure kill only that owned container/process group, retain evidence, and stop.
Never kill shared processes or loosen caps to turn incomplete output into success.

Afterward the coordinator checks campaign.json's full798 entries and exact membership,
780/18 outcomes, six-way exact replay, both saved replay/restoration receipts, before/after
input/runtime hashes and real launch records. Publish compact actual identities/counts,
refusals/failures and receipt hashes; keep bulk raw outputs private. Do not infer success from
an exit code or empty selection. Any ordinary helper correction is versioned/rechecked and
rebound to the genuine scope; preserve prior failed outputs. A production/security/dependency
change returns for its exact decision. Successful first use still does not qualify C3,
performance, components, remote CI, human L1 or U4 closure.
