# Combined runtime placement and first-use package

Proposal only. No human coexistence decision, new immutable placement, authority binding or
restart has occurred. This package completes the separate Python-runtime route requested
by the coordinator at `490d90b4d9d3d5ce035388c987488660b2976ea7` (B starting HEAD after normal
fast-forward from `4684cb9eccc5b5186824a8705cf4d1b44f88af42`). Construction/corpus review is
reused; no new compatibility/native campaign is claimed.

[candidate.json](candidate.json) binds the exact 31 project files from A
`d9a22f047d4410aab4abb75e1fc780a51d7a8f6b`, B's exact combined helper at `4684cb9`,
original native source `24fa36803081e5077d5977baa91441a2c8534ec8`, original BuildInputs,
HostRecord and genuine native approval `cc91e5489a58e06addb2f43e45a0e4e71cb66aa1`, and all
accepted image/Python/site/library inventories. It is a candidate descriptor, not authority.

## Exact composition

The new fixed root is `/var/lib/rkuarch/k2/candidate-04-combined-runtime-v1`, with:

| Root member | Content / purpose |
| --- | --- |
| `project/` | Exactly 31 reviewed project postimages; no extra project module |
| `helpers/` | Exact combined `parallel_entrypoint.py`, unchanged `parallel_core.py`, `resource_limits.py`, `parallel-policy.json`; new `bindings.py` and `runtime_entry.py` |
| `record/` | Exact candidate descriptor plus actual helper-publication commit/hash |
| `authority/` | Initially empty. Later five root-owned files: original published decision and placement records, actual preflight, derived release and external selector |

The two new runtime helpers are necessary to enforce the separate import root and external
runtime-approval joins. They do not change A's files, construct host acceptance tokens or
replace native transport. `prepare.py` and `launch.py` are separately hashed host preparation
and launcher tools; they run from the exact published package, not from an editable project
import. No baseline seven-file overlay is installed.

Reuse the original sealed root `/var/lib/rkuarch/k2/candidate-04-first-use-v1` read-only:
`candidate` → `/candidate`, `python` → `/python`, `site` → `/site`, `campaign` → `/campaign`,
`manifests` → `/manifests`. New mounts are `/project`, `/combined`, `/combined-record` and,
only after authorization, `/combined-authority`. Original native selector stays root-owned
at the original root's `authority/k2-host-selector.json`, mounted at the existing container
`/etc/rkuarch/k2-host-selector.json`; no host `/etc` placement or copied token is involved.

`/candidate` is exclusively original native validation/data/helper source. Project Python
imports use `/project/src` and `/project/contract` only. The original `entrypoint.py`,
`deployment.py` and independent `first_use_checks.py` remain mounted from their recorded
original locations; all are already included in original sealed helper/layout inventories.
They are explicit auxiliary runtime reads, not silently omitted project-closure members.
No old project source is on sys.path. All actual rkuarch/uarch_contract module origins are
checked. Original layout, tools, jobs, native release and native authority checks remain.

The container image is exactly `sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523`.
The actual mounted CPython 3.12.14 and accepted site packages provide the Python host;
there is no assumption of image Python and no Docker wrapper substituted for an ELF.
The native resolver still opens verified real debug/release executables. `--pull never`,
network none, read-only mounts/root, UID1000, cap-drop ALL, no-new-privileges, existing tmpfs,
clean environment and no LD_LIBRARY_PATH remain exact. No new package/image/security change.

## Runtime adapter and identities

The new entrypoint calls the unchanged combined scheduler directly, replacing only its
packaging hooks (`verify_helpers`, `verify_release`, `input_snapshot`) with stronger
combined-runtime checks and `Store` with a receipt-binding subclass. It explicitly replaces
original `common()` with the separate-root importer, preserving original `authority()` and
`replay()` code. `dump` adds the new binding to replay receipts. No run_fixed_delay,
resolution_session, admitted_case, parser, result constructor or acceptance token is patched.

The release binds native subject/source, old release, separate Python closure, exact helpers,
candidate descriptor, helper publication, actual decision/placement publications and real
preflight. Campaign/resources/worker-summary, operational, replay and outer-launch receipts
carry these distinct bindings. Replay requires that same new-runtime campaign binding.
Original per-slot native receipts/transport are unchanged and belong to that bound campaign.

`prepare payload` renders a preview that immediately exits 1. `prepare placement` requires
the exact future published Javid decision before producing a human-only script. `prepare
binding` requires the actual later coordinator placement publication and preflight. The
launcher verifies both Git blobs against published main and root-owned placed copies before
runtime authority/native execution. A rehashed manifest alone cannot pass the independent
selector/decision/publication binding. The trusted premises remain reviewed published helpers,
authentic human/coordinator Git records, human root placement and no concurrent privileged
attacker; SHA256 cannot itself authenticate a person's consent.

No execution-ready release is supplied here. Future commit/hash fields are unresolved by
design, and absence refuses. Private test receipts have a different status and cannot satisfy
actual immutable-root preflight. The production launcher exposes no private mode.

## Protected decision and complete human sequence

[decision-and-procedure.md](decision-and-procedure.md) is the exact approval question and
staging/placement/preflight/binding/restart sequence. [normative-addendum.txt](normative-addendum.txt)
is the exact proposed prospective U0011 addendum, also supplied as an **unapplied** patch.
This explicitly authorizes only the protected runtime-copy coexistence if Javid accepts it;
it is a policy dependency, not a previously granted exemption. U0002 currentness remains
unchanged and the old artifact does not validate the altered hardware copy. Canonical source
installation and long-term developer-source adoption require their own lifecycle.

## Complete campaign and evidence reuse

Exactly 133 cases × debug/release × repetitions 0/1/2 = 798 fresh processes, 780 success and
18 TimeOverflow refusals. One worker owns each case's six calls, enters separate mode case
contexts after fork, retains full per-result parsing and independent B checks, and runs no
nested pool. CPU affinity/cgroup quota and memory reserve/per-worker limits still determine
worker count. Failures stop dispatch and reap/kill owned children; no partial completion.
No quick profile can create complete campaign evidence. A fresh output path is required;
the historical 88 checked / 89 transport stopped run is never resumed or credited.

Unchanged six-way comparison, exact call/transport membership, byte preservation, original
K06-02 and S08 producer-disabled relocated replay and all original corruption/restoration
controls remain mandatory. Existing [public validation obligations](../U4-B-K2-deployment-first-use-v1/validation.md)
and candidate-04 B independent answers remain applicable, including private Wheel/Arena
separation and pending human/component gates. Startup, authority resolution, processing,
final checks, total and worker RSS are retained in worker-summary; parent peak RSS and total
are in operational receipts and outer container timing/exit in launch receipts. These are
operational diagnostics, not modelled timing or performance qualification.

New packaging checks and exact provenance are recorded in checks.json. Inherited evidence:
coordinator 44 fast tests; B's final genuine shared-session/case/read-drift join; original
scheduler/fork/failure controls, 14 bound-read refusals, ten guard-removal discriminators,
A's accepted result-validation/cache tests and candidate-04 native audit. None is labelled
rerun. No public native calls, new authority or artifact lifecycle occurred here. U0024,
remote qualification, component/C3, public qualification and U4 closure remain unchanged.
