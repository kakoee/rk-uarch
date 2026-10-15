# Exact constructed image and remaining access action

The human release and five native installation hashes pass. `construct.py build` exported
published A subject 892b9ee00c485718082e8ea9a765578cbd64d684 into a new disposable directory,
then composed A's exact accepted Dockerfile plus B's unchanged offline-cache fragment.
Only native Git bytes, Dockerfile and native-inputs.sha256 entered the build context.
No .git, local caches, credentials, arbitrary packages or copied checkpoint tree were sent.
[Construction identity](image-construction.json) binds recipe hash and native Git tree.

Actual local image/tag:

```text
sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523
rk-uarch-k1-builder:u4-b-e9f69f414983
```

The accepted base manifest ba81bc3e... is a different input, not the final image.
[Full inspection](image-inspection.json) retains platform/config/layer identity. The local
image has not been pushed; no hosted registry RepoDigest/access is asserted. The image and
Docker's normal build cache remain in the existing local daemon; all filesystem scratch
exports, tool downloads and Cargo target directories were removed.

## Actual construction, checks and operational corrections

Initial [Docker probes](availability.json) and [construction attempt](construction-attempt.json)
failed because the local runtime was stopped. A normal `docker.exe desktop start --timeout 30`
succeeded and restored the existing Linux/WSL endpoint without an integration-settings edit.
During recovery the reported transport changed from Docker 29.2.1/Desktop 4.62.0 to
29.8.2/4.95.0. No update command was issued; the cause of that version change was not
established. A transient disconnect was rejected as an unrelated control failure. The exact
image ID and RootFS layers were reverified unchanged afterward. [Runtime receipt](image-desktop-start-and-recovery.json).

Real containers use this local ID, Linux amd64, --pull never, --network none, invoking uid/gid,
readonly same-path exported source and isolated writable targets/receipts. Host Python 3.12.3
is the stdlib controller only; actual Cargo/Rust tools run inside the image at
/usr/local/cargo and /usr/local/rustup. All accepted versions, rustup discovery/target and
actual binary hashes were observed. All 27 cached archives and notices match accepted
checksums. No Python layer, apt step or tool substitution was needed.

Full metadata verifies all 27 locked crates/features; Linux-filtered metadata independently
verifies the exact 26 selected crates/features. UEFI-only r-efi 6.0.0 is the sole difference.
The first local guard wrongly compared those graphs and refused; it was corrected without
weakening full lock/cache checks. Cargo documents target filtering in its
[metadata reference](https://doc.rust-lang.org/cargo/commands/cargo-metadata.html).

Real debug/release discovery freezes all 19 names/multiplicities. Full suites use
--show-output so emitted replay data cannot corrupt libtest status lines. Six fresh test
processes read A's UARCH_K1_REPLAY_OUT file sink; their exact private bytes match. The
stdout prefix remains available and appears in captured logs; no public K2 interface exists.
The exact corrected native-container.sh inspect/checks stages and hosted Python metadata/
results guards also passed against this image in a fresh export. The host registry-pull
script is not executed because no registry publication/access is authorized.

Fault controls exercise missing source, deliberate compile/test errors, empty/ignored/
filtered selections, absent offline cache, nonexistent toolchain without auto-install,
current Unicode-policy refusal, A's three semantic faults in both modes, restored positives
and a release-only canonical-byte mutation. An early attempt reused a mutated Cargo target
for a later selection control; the unexpected failure was retained and the controller fixed
to use the already verified restored target. The complete corrected sequence passed.
No unrelated failure was credited. [Checks and receipts](checks.md) give statuses and limits.

Reproduction, using a new work directory and the existing daemon, with no distribution:

```sh
package=docs/reviews/U4-B-K1-environment-v1
subject=892b9ee00c485718082e8ea9a765578cbd64d684
work="$PWD/$package/scratch-next-image"
python3 -B "$package/construct.py" build "$PWD" "$subject" "$work"
python3 -B "$package/construct.py" verify "$work" \
  --replay-test tests::canonical_replay_private_bytes
python3 -B "$package/controls.py" "$work" \
  --mutations docs/reviews/U4-A-K1-v1/fault-anchors.json
```

A rebuild must record its own actual identity; Dockerfile equivalence does not guarantee
byte-identical build metadata. The already verified image above is the publication subject.

## Concrete private publication/access proposal — approval still required

Publish exactly the verified local image ID above to
**`ghcr.io/kakoee/rk-uarch-k1-builder:k1-892b9ee`**, initially private, with existing notices
and no added layers. Before any push, use an authorized publisher to establish whether the
package/tag exists; refuse a public package or a different existing tag. After the approved
push, verify private visibility and capture the actual RepoDigest for immutable CI pulls.
Do not enable billing or proceed if this requires spending outside existing no-charge access.
The destination, credential/environment changes and push have not been executed. The
[read-only package probe](registry-access-probe.json) returned 404; it does not prove a
private package is absent or establish publication access.

Publication uses Javid-controlled classic write:packages credentials, without repo/delete
scopes. GHCR defaults a new package to private. Keep independent granular package ACLs;
**do not grant this public repository general Actions package access**. GitHub warns that
such access can also expose a private package to forks. [Registry authentication/publication](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry),
[package visibility/access](https://docs.github.com/en/packages/learn-github-packages/configuring-a-packages-access-control-and-visibility).

Concrete initial CI access proposal: create environment `native-k1-private` in
kakoee/rk-uarch with selected deployment **branch main only**, no tag/PR rule. Store a
separate expiring, account-level classic read:packages token as environment secret
`K1_GHCR_READ_TOKEN`; no write/delete/repo scope. Javid supplies it through the secure
GitHub environment UI, not chat. A trusted push-to-main native job references that
environment, uses contents:read, logs into GHCR only for the pull with password-stdin and
a temporary DOCKER_CONFIG, then removes credentials before native code executes. No
publisher token enters CI. Environment restrictions bind to the run ref, and secrets are
available only to jobs using that environment. [GitHub environment controls](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments).

This proposed main-only access does not settle qualifying fork-PR execution; that path
remains an explicit access dependency, never a skipped-pass assertion or a declaration
that S-CI is complete. No secrets-enabled pull_request_target shortcut is proposed. Once
publication/access is separately authorized and observed, reconcile the exact digest,
plan path, environment/trigger scope and pull authentication before installing the native
job. Preserve the existing docs-only classifier; no job with placeholders is installed.
Tool/licence acceptance is settled. Distribution/access is the only new permission sought;
full later corpus, human L1, M migration and runner registration are not prerequisites here.
