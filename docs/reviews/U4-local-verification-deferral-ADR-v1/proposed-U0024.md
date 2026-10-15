# U0024 — Temporary local verification and deferred native CI infrastructure

**Status:** direction and interim-development exception approved by Javid; effective on
human installation. No fixed sprint expiry. Revisit at each sprint handoff and resume only
on Javid's instruction. This may span several sprints; elapsed time is never a test pass.

## Context and purpose

Private K1 is implemented. A and B recorded local debug/release tests, deterministic
replays and discriminating fault/restoration controls. B constructed a pinned Linux
container locally. These are useful local results; they are not hosted CI, self-hosted
nightly, controlled-host performance or silicon validation.

The remote infrastructure requires people/access currently unavailable. Reza administers
the designated Linux server; the actual owner of `kakoee/rk-uarch` must perform owner-only
GitHub setup. Those roles need not belong to the same person. Code-push permission and
Linux root access do not confer GitHub ownership. See the preserved
[host record](../reviews/U3-preparation-v1/host-access.json) and
[owner handoff](../reviews/U4-B-K1-private-ci-v1/owner-handoff.md).

Two separate facilities are deferred:

| Facility | Purpose | What it is not |
| --- | --- | --- |
| Self-hosted GitHub Actions runner on the Linux server | Executes selected commit-specific jobs, retains reviewed tools/caches, supports real nightly automation and a controlled measurement environment when allocated | Not merely a Docker image; registration alone proves neither tests nor performance |
| Private container registry and CI pull access | Makes the exact compiler/dependency image available to temporary hosted runners or other approved machines | Not a source repository, simulator result or mandatory part of every server-runner arrangement |

GitHub orchestrates a self-hosted job while compilation happens on our server. A persistent
server may retain the image and valid build caches; each run must still build/test the
requested commit. Hosted machines generally need to pull the image again. Neither a cache
hit nor reuse of a previous executable replaces that run's checks. The image supplies tools
and cached dependencies; current source is checked out and built separately.

## Temporary decision: local correctness may support interim development

Javid explicitly confirmed: successful local checks and independent review may permit later
development stages to proceed while remote CI, performance qualification and final project
closure remain pending. Apply this to native verification from U4 onward during the deferral.
It is not a blanket implementation release; each task retains its approved scope and other
prerequisites. In particular, K2 still needs installed mapped carriers, actual authority/input
bindings and reviewed K1 correctness; B/R/T retain their semantic, data and contract gates.

For each claimed local milestone:

1. Test the exact published commit in a fresh local clone/export, with its current accepted
   pins, lock and image/tool identities. Record OS/kernel/WSL/container details and actual
   module/binary origins. No untracked peer files or stale build products establish evidence.
2. Execute the applicable real suites, fmt/clippy/licence/static/schema checks, debug/release
   tests, required replay/determinism and fault/restoration checks. Run applicable integrated
   regressions at handoffs; do not demand every expensive suite for every doc edit. Missing,
   failed, skipped, unsupported and not-run cases remain distinct. A no-test exit is not a pass.
3. Independent review evaluates the current implementation and discriminating checks. Author
   receipts alone do not substitute for the required independent review. WSL2/local Linux
   container correctness is an interim environment, not an independent hosted-machine result.
4. Record the stage as **locally verified for interim development; remote qualification
   pending**, with the exact commit, evidence pointers and remaining remote obligations.
   Subsequent development may rely on that scoped reviewed correctness, not on a claimed
   hosted pass. Local findings must be corrected; infrastructure delay excuses no failing test.
5. At each sprint boundary carry the open infrastructure items and their owners forward.
   Interim sprint handoffs may progress; any human-approved sprint tag must disclose this
   exception and cannot assert full remote qualification. Final project closure stays blocked.

Other working GitHub jobs, including Python/contracts/licences, remain active. This is not
permission to ignore their failures. The live native job stays explicitly skipped; the
self-hosted schedule stays disabled. No empty or skipped job counts as a successful native
run. Human installation, U0002 generation/adoption, prediction-before-measurement discipline,
human L1 work, fidelity/badge/error/energy rules and hardware-access decisions are unchanged.

## Exact supersession and limits

During this deferral only, this ADR replaces the remote native correctness execution as a
**development-entry** prerequisite in U0011's K1/K2 verification and real-Linux-CI clauses,
U0023's hosted correctness/fresh-checkout clauses, build-spec §6/§8 and the corresponding
execution-plan/prompt gates. The local procedure above substitutes for the native hosted
portion of an interim sprint handoff; it does not reinterpret historical U1–U3 evidence.
The earlier U4-native-CI-deferral-v1 note's prohibition on later development based solely on
missing native CI is superseded by this explicit local-verification exception.

Full G5 (including performance and automation), U9 entry, simulator-performance/scaling
claims and final project closure still require the applicable controlled-host measurements
and executed self-hosted nightly under U0023. This ADR grants no performance exception,
silicon-validation result, changed numerical tolerance or automatic stage acceptance.
It does not authorize a new dependency, image distribution destination, paid resource,
server modification or remote job now. Earlier publication approval remains on hold.

## Deferred actions: Reza, GitHub owner and Lane B

These are future steps, not commands to execute during the deferral. Recheck then-current
GitHub instructions, server allocation, image/tool pins and ownership; do not blindly reuse
old tokens, the U3 fork runbook or an old K1-only test inventory several sprints later.

### A. Register and qualify the server runner

1. **Reza: inspect and allocate.** Reconfirm the designated Debian x86_64 host and approved
   account from the host record. Record CPU/RAM/disk/OS, usage/noise constraints and maintenance
   responsibility. The U3 receipts found rootless Podman and Python/uv/Rust, but those old
   inventories do not prove current readiness. Choose an unprivileged runner/service account
   and separate runner checkout/cache directories, not a developer's working clone.
2. **GitHub owner: register.** In `kakoee/rk-uarch` use Settings → Actions → Runners → New
   self-hosted runner → Linux/x64. Check for an existing suitable runner first. Use the
   current UI's download/checksum/configuration instructions on the server. Retain default
   `self-hosted`, `linux`, `x64` labels and add `uarch` to match the current nightly selector.
   Registration uses a short-lived token; never commit or paste it into a review/chat.
   [GitHub registration instructions](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/add-runners).
3. **Reza: service.** After registration, verify the runner's unprivileged identity, PATH,
   uv/Python and accepted native tools/runtime under the service environment, not only an
   interactive shell. On this systemd host, from the registered runner directory, use
   `sudo ./svc.sh install <RUNNER_USER>`, `sudo ./svc.sh start`, and `sudo ./svc.sh status`
   after approving the actual account/service setup. Confirm GitHub shows it online and
   it survives an intended restart. [Official service setup](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/configure-the-application).
4. **B with Reza: runtime and isolation.** The existing B scripts use Docker. Historical
   rootless Podman availability does not prove Docker-script/Actions compatibility. Verify
   a supported exact invocation or review a narrow adapter; do not install a privileged
   daemon or grant Docker-group/root privileges by implication. Use clean per-job source,
   isolated mutable outputs and identity-keyed caches. Public fork/PR code must not run on
   this shared server; review trusted-main/manual/schedule routing before registration is
   exposed to jobs. No secrets-enabled pull_request_target shortcut. GitHub explicitly
   warns about public-repository self-hosted runner exposure in its registration guidance.
5. **B: manual real jobs before schedule.** Update the then-current nightly to pinned tools
   and actual applicable suites. The recorded workflow permits pytest exit 5 and has old
   no-source/no-op wording: remove those loopholes before claiming qualification. Inspect
   collection, failures, debug/release/replay/fault results and exact commit/environment.
   Run a trusted-main manual job first; then enable the agreed schedule. An online runner
   or green empty job does not establish G5-automation. Do not run old fork-tool tasks.
6. **Coordinator: acceptance receipts.** Retain runner/account/labels, service status,
   runtime/tool/image identities, job URLs and tested commits, real counts and dispositions.
   Performance work separately freezes workload/budget/noise/allocation before measurement;
   a shared server is not automatically an acceptable performance host. It is not NPU silicon.

### B. Publish and consume the compilation image, if this distribution route is retained

1. **Confirm the route.** Hosted correctness can use GHCR; a persistent server can instead
   retain or receive an approved image through a separately agreed path. Registry setup is
   not intrinsically required just to register a runner. Choose deliberately on resumption.
2. **Reconcile current image.** The historical verified local K1 ID is
   `sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523`
   (about 1.36 GB uncompressed). Its then-approved destination was
   `ghcr.io/kakoee/rk-uarch-k1-builder:k1-892b9ee`. The later question about `jjaffari`
   did not authorize switching destination. If namespace, toolchain or cache needs change,
   review the exact new identity; do not reuse this tag for changed bytes. Preserve notices.
3. **Owner: publisher access.** Follow B's linked owner handoff only if its inputs still
   match. On the workstation containing the verified image, its helper prompts privately
   for a narrowly scoped expiring classic publisher token, verifies owner/image/private
   visibility and pushes/readbacks the exact approved tag. Inspect independent package ACLs
   and source-link inheritance. Keep publisher credentials out of CI/chat/Git. A failed
   readback does not prove no publication occurred. [GHCR authentication and digest pulls](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry).
4. **Repository owner: restricted reader.** For the retained private-GHCR design, create
   `native-k1-private` under repository Settings → Environments, allow branch `main` only
   (no wildcard/tag/PR rule), and set environment secret `K1_GHCR_READ_TOKEN` using a separate
   expiring classic read:packages token with package access. Do not substitute a publisher
   token or repository-wide grant. Package owner and repository owner may differ; placing
   the image under jjaffari would not confer environment administration in kakoee/rk-uarch.
   [Environment setup and owner permissions](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments).
5. **B: activate exact job.** Verify private reader pull and ACL/environment receipts, record
   actual registry RepoDigest (not local image ID or base digest), resolve all placeholders,
   and install the native job for trusted main. Remove temporary pull credentials before
   executing code; preserve docs-only skipping. Refresh tests for the current stage rather
   than freezing the historical 19 K1 tests forever. Fork-PR access remains separately scoped.
6. **Retain non-secret records.** Package visibility/ACL observation, immutable registry
   identity, reader expiry, environment branch rules/secret name, successful pull and actual
   hosted job results are required. No token, Docker credential file or secret value belongs
   in the repository. Revoke one-time publishing credentials and assign reader rotation.

## Resumption, catch-up and consequences

Revisit this ADR at every sprint handoff; no arbitrary calendar or sprint count forces
resumption. When Reza/access is available, Javid explicitly resumes the selected work.
B first rechecks current source, dependencies and prepared workflows. Execute all currently
applicable deferred correctness and automation suites on the exact chosen published commit
with the required fresh checkout(s); retain both local and remote receipts. Investigate
any discrepancy before declaring remote qualification. A current run does not retroactively
prove hosted passes for earlier tags. Remove the native skip only with the operational,
reviewed replacement; update the workflow guard tests, plan and evidence ledger together.

Reza and the GitHub owner provide infrastructure; B verifies/activates jobs; the coordinator
tracks outstanding gates; Javid controls resumption, exact protected decisions and closure.
Independent review is still required. Until catch-up succeeds, report remote verification
and automation as pending. This trades immediate automation/platform-independence evidence
for continued reviewed local development, while retaining the final verification debt.
