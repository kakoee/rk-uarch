# U4 A — approved C1 resolution attempt and lock-gate refusal

**Stopped at the mandatory full-lock gate.** Pinned Cargo completed the targeted root
update, but selected two unpermitted versions. No archive download or downstream C1
operation followed. This is actual rejected resolver output, not an accepted dependency
closure or evidence that the requested pins are unsatisfiable.

| Package | Exact permitted version | Actual selected version |
| --- | --- | --- |
| crypto-common | 0.1.6 | 0.1.7 |
| typenum | 1.19.0 | 1.20.1 |

All **28 existing package identities** retain their version/source/checksum tuples. Eight
packages were added; six match the exact allowlist and two do not. The full identities,
including unexpected checksums, are in [lock-gate.json](lock-gate.json). The resolver
command exited 0; the independent gate refused its output. No precise update, version
substitution, allowlist change, lock hand-edit or constraint crate was attempted after
that refusal, following this task's explicit stop-on-extra-version requirement.

## Authorized subject and verified tools

Javid's committed [approval](../U4-K2-approved-release-v1/acceptance.json), “yes, both”,
releases C1 independently of semantic installation. No dependency-experiment vote was
repeated. Main was integrated normally from 1a52fa8 to
535b8346d6209e11a50daaa06f8bcf08d8a0d254, preserving peer history. The actual disposable
export is the required **0718955cc0656e5bac4688d4696abbd547cb4186**, not the newer main.

Verified before resolution:

- Machine plan SHA256: 4a5cbb16f5f249234d8ffc0a0e01476c89f4769a57ab96f422ff3c10093eebd5.
- Starting Cargo.lock SHA256: 3df872c1e8c445b179dd8162430a5265fa770a62bcfa009009dae49d878bf084.
- Actual local Linux/amd64 image:
  sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523.
- Actual Rust/Cargo 1.99.0, compiler b940084d7eb6a299eb4bfeb8e34901bc051e7ac4,
  cargo-deny 0.20.2, and accepted rustfmt/clippy versions. Version checks ran in that
  exact image with networking disabled and absolute tool paths; full outputs are retained.

[Preflight](preflight.json) includes every image/tool command, explicit environment,
exit code and output hash. The image was already present. No pull, upgrade, install,
image build/distribution, remote host work or infrastructure restoration occurred.

## Actual execution and returned artifacts

Fresh private root: /tmp/u4-k2-c1.zq99i8mm. Source came from Git archive; Cargo home and
Docker config started empty, and Cargo target was private. No accepted cache was copied
or live cache mounted. The image filesystem was read-only. No credentials or inherited
Cargo environment/configuration were supplied; source/parent config checks passed.

Only the scratch crate manifest changed: add arbitrary_precision to the existing exact
serde_json pin and add exact sha2 0.10.9 with defaults disabled and std/force-soft. The
[manifest diff](scratch-manifest.diff) is complete. Pinned Cargo then ran exactly
**cargo update -p uarch-engine**, with no broad update or build. [Command](resolve-command.json)
and [outcome](resolve-result.json) retain the actual container invocation and status.

- [Starting lock](starting.Cargo.lock), [actual rejected lock](after-root-update.Cargo.lock)
  and [lock diff](candidate-lock.diff). The rejected lock SHA256 is
  d2b744a9045a124c5edb097c821d2b69e9f0dd5e734554542fdfee6b5a4c6211.
- [Actual lock dependency graph](candidate-lock-graph.json), explicitly not a Cargo
  metadata or unified-feature report; [requested features and downstream status](features-and-licences.json).
- [Network inventory](network.json), [proxy events](resolve-network.tsv) and
  [compact Cargo log](resolve.filtered.log). All 35 index GETs returned HTTP 200.
  Only index.crates.io was connected; no archive host was enabled during resolution.
  The index config's API URL was not contacted. TLS verification remained enabled.
- [Private cache inventory](cache-inventory.json): 38 index/administrative files,
  zero crate archives and zero extracted crate sources. Bulk cache and raw 2,676,399-byte
  trace remain outside Git with exact paths/hashes. Compact log omits curl body dumps and
  removes trailing whitespace; the original raw trace is unchanged and still retained.
- [Preservation](preservation.json): only the scratch manifest and lock changed; all other
  exported file bytes/mtimes are preserved. No tracked live file changed. Target contains
  only Cargo's .rustc_info.json with rustc -vV output, no executable/object/build output.

The [local CONNECT proxy](connect-proxy.pl) and [stage script](resolve.sh) are retained as
executed controls, not a newly installed tool or a recipe authorizing another experiment.
The accepted Cargo process used the explicit loopback proxy, which permitted only
index.crates.io:443 during this stage. Docker used normal bridge networking; this is an
application-level allowlist with recorded requests, not a claimed packet firewall.

## Checks and boundaries

[Offline evidence verifier](verify_receipts.py) checks the source/plan/lock hashes, every
old identity, exact two-version drift, actual tool outputs, network/cache hashes and all
ten uninstalled semantic preimages. It also imports B's unchanged published predicate
from the pinned export: a synthetic allowlist control passes, the **actual resolver lock
refuses**, and the control passes again. The synthetic vector is never serialized as a
lock, graph, HostRecord or authority. [Validation](validation.json) records this check,
repository Ruff and manifest apply-check; these are host evidence checks, not native tests.

The full/Linux metadata, unified feature graph, archive fetch/checksums, actual archive
licence/notice inspection, offline metadata/fetch repeats and cargo-deny licence/bans/
sources checks are all **not_run**, because their prerequisite lock gate failed. No
advisory fetch, build script, compilation, probe or engine execution occurred. No scalar/
no-SIMD result is claimed. The combined semantic candidate remains uninstalled; original
proposals, historical evidence, source, dependencies and artifacts are preserved.

Return this failure to the coordinator to reconcile the actual drift and select any
subsequent bounded action. Nothing here widens the permitted versions or accepts this
lock. Exact dependency acceptance, remaining C1 evidence, C2 and final binary/host authority
remain later work. U0024 is unchanged. Stop for coordinator reconciliation.
