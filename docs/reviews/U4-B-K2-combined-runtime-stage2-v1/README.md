# Combined-runtime Stage 2 response — F1–F6

Corrected preparation only. Return to the **same independent reviewer for Stage 3** after
coordinator reconciliation. Applied below means implemented in this new proposal, not
accepted, installed or independently closed. H1–H4 and the runtime-copy arrangement remain
unapproved. No authority resolution/creation, root placement, actual preflight, native call,
restart, build, artifact lifecycle, component acceptance or U4 closure occurred.

The reviewed package remains `cbb0313e13abc0ca99311df323a0c64f4f7886c1`, helper publication
`2664c97bbf603843d756f78dd8d0d3e91762953c`, candidate
`sha256:932fe281632bac001f0fdb091089cfd5e09d0b141d74569f6d6b5281f06f9ee1`.
The reviewer report is `sha256:6949858ea0d24392497c93ca93d726e42af466b0ef015b00c972538b85208ff2`.
Its manifest matched on intake; its pending long polling run is not credited or resumed.
Starting B HEAD was `fd0a60b372b9a93410d736a39c8472a2c2764b1d`; normal integration reached
`f7ccd61259d427e461f2e56404b9330eefe566ea` before private preparation.

[publication.json](publication.json) pins the real new helper commit and candidate bytes;
[file-identities.json](file-identities.json) records every owned preparation/test/policy file
and its baseline difference. [checks.json](checks.json) separates executed from inherited
evidence. [reproduce.md](reproduce.md) gives explicit private roots, commands and limitations.
No old review, proposal or A postimage is rewritten.

| Finding | Stage 2 disposition and exact implementation | Discriminating evidence |
| --- | --- | --- |
| F1 blocking | APPLIED: `publication.py` observes the explicit expected remote main, fetches it into an isolated bare database, refuses races/unavailability, and reads only reachable immutable commits. Clean Git environment/config, replacements disabled; `prepare.py` also sanitizes private patch application. `launch.py` uses the same context. | Fabricated local tracking ref, replacement objects, GIT_DIR/work-tree/object/config redirects, missing remote and exact-content positive; actual remote observation separately recorded. Essential remote-read guard removed/restored. |
| F2 blocking | APPLIED: `receipt_checks.py`, `launch.run`, `runtime_entry.main` require matching complete campaign/exit-0 launch/operational/resources/workers, exact 798 outcomes, snapshots and component hashes; failure records refuse before replay transport/resolution. | Original campaign + exit -9/failure exploit; complete labelled synthetic receipt-shape set; missing/nonzero/incomplete/stale/contradictory inputs. Both host and runtime gates removed/restored. |
| F3 | APPLIED: `bindings.observed_payload`, `mount_observations`, `check_preflight` and `runtime_entry` separate expected root from actual mountinfo, inode seal and inventory checks. Private status changes cannot promote an unsealed export. | Saved old private preflight with only two flags changed refuses; actual private inode/mount parsing and explicitly synthetic production-observation shape controls. Essential seal guard removed/restored. |
| F4 | APPLIED: `launch.receipt_bytes` uses one lstat and tolerates only FileNotFoundError for a vanished entry. Surviving regular bytes count; symlinks, unexpected inodes and other errors refuse. | Deterministic actual `Store.json` pending-file unlink during the real launch polling path; persistent byte accounting, symlink and PermissionError controls. Removal reintroduces the actual race; restore passes. No soak. |
| F5 | APPLIED: `bindings.module_origins` records all loaded origins; `helper_origins` verifies every bound helper path and byte hash. Project imports remain separate and exact. | Earlier-path helper shadow refuses; bound helper positive; builtin/frozen/no-file categorization. Essential origin guard removed/restored. No total-module-count pin. |
| F6 | APPLIED: `bindings.check_decision` requires exact version-2 fields, untouched reply_verbatim plus explicit unconditional disposition, accepted boolean, empty conditions and exact candidate/decision/policy joins. | Affirmative wording variants preserved byte-for-byte; rejection, conditions, missing/extra fields and wrong identity refuse. Essential exact-schema guard removed/restored. All approval-shaped data are synthetic tests. |

All six baseline regressions were exercised before correction. Saved failure logs identify
actual assertions, not collection/import errors. F1 also has a separate replacement-only
baseline failure. Each essential correction has corrected pass / removed failure / exact
restoration pass. No claim that receipt-shape tests are real campaign results or consent.

## Complete composition and preserved execution obligations

[candidate.json](candidate.json) retains the exact 31 project files from A
`d9a22f047d4410aab4abb75e1fc780a51d7a8f6b`, combined scheduler from
`4684cb9eccc5b5186824a8705cf4d1b44f88af42`, original native source
`24fa36803081e5077d5977baa91441a2c8534ec8`, original BuildInputs/HostRecord, native approval
`cc91e5489a58e06addb2f43e45a0e4e71cb66aa1`, native selectors/binaries and accepted image,
Python/site/library inventories. No additional project import or generator-support change.

The proposed **new** root is `/var/lib/rkuarch/k2/candidate-04-combined-runtime-v2`.
Payload: 31 project files + seven helper files + two record files = **40 files**.
The sole extra runtime file over the reviewed 39-file package is `helpers/receipt_checks.py`,
shared by host and runtime replay admission. Existing bindings/runtime_entry are corrected;
parallel_entrypoint, parallel_core, resource_limits and parallel-policy bytes are unchanged.
Host-only `publication.py` verifies remote Git; `freeze_candidate.py` reconstructs metadata.
Neither adds a container dependency. Full helper paths/hashes include original entrypoint,
deployment and first_use_checks auxiliary reads, explicitly separate from project closure.

`/candidate` is original native build/source/data validation; imports use `/project/src` and
`/project/contract`. Original sealed root `/var/lib/rkuarch/k2/candidate-04-first-use-v1`
remains read-only. Python host is the accepted mounted CPython 3.12.14/site inventory,
not assumed image Python. The resolver opens the real verified ELF, not a Docker wrapper.
Exact image `sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523`,
network none, --pull never, UID1000, cap-drop ALL, no-new-privileges, existing tmpfs and clean
environment remain. No new package, dependency, image or security configuration.

All 133 cases retain six fresh processes (debug/release × three repetitions), **798 slots:
780 success and 18 expected TimeOverflow refusals**, six-way comparisons, per-result native
and independent B validation, exact saved membership, relocated replay and original
corruption/restoration controls. CPU/quota/memory worker limits, one case per worker task,
no nested pool, failure cleanup and quick-profile refusal are unchanged. No historic 88/89
slots count in the fresh campaign. Startup/processing/total/RSS remain operational evidence,
not modelled timing or a performance claim. The outer 7,200-second timer governs even while
the inner timer starts later; exact limits and proposed retry wording are in policy-choices.
[Existing public obligations](../U4-B-K2-deployment-first-use-v1/validation.md) and private
Wheel/Arena separation remain mandatory. The unchanged genuine session/case/fork/native
receipts are inherited, not rerun; new checks cover only packaging/origin/receipt boundaries.

## Trust, policy and remaining steps

Actual-remote checks establish publication under trusted Git/TLS/DNS/host-tool assumptions,
not consent. Coordinator must preserve the genuine human reply and independently record
its disposition; no helper interprets English or turns a test boolean into approval.
Observed preflight records actual mounted inode checks and kernel mountinfo. JSON is not
host attestation: authentic published coordinator reconciliation, trusted reviewed tools,
human root placement and absence of a concurrent privileged attacker remain premises.
Builtin/frozen/no-file origins are explicitly recorded; they cannot stand in for required
file-backed helpers. Existing Python/site/image inventories cover their runtime inputs.

[policy-choices.md](policy-choices.md) proposes H1 actual remote; H2 bounded U0011 rule plus
minimal unapplied U0002 cross-reference; H3 current stop-on-failure and a separately confirmed,
one-additional-operational-attempt option; H4 unchanged inclusive outer limit. Both protected
patches are **unapplied**. The old artifact never validates the altered hardware runtime copy;
canonical currentness and the later canonical source/artifact lifecycle remain unchanged.

[decision-and-procedure.md](decision-and-procedure.md) gives the updated exact question,
version-2 decision schema and record/placement order. It is a future decision draft, not an
approval request in this Stage 2 handoff. No execution-ready release exists. Next: coordinator
reconciliation, the same reviewer's Stage 3, then the exact human policy/coexistence decision
and separately observed human placement/preflight/publication/binding before any restart.
U0024 and all public/component/qualification gates remain unchanged.
