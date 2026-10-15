# U4 B: approved private publication owner handoff

**Publication/access approval is settled; the exact owner handoff is ready.**
Javid will arrange owner involvement. Start with [owner UI steps and commands](owner-handoff.md).
The available `jjaffari` account has code-push permission but no repository administration
or package credential. No image publication, package ACL change, environment creation,
secret installation or executable native CI installation was performed.
[Observed access probes](access-observation.json) retain the actual 404s without treating
those responses as proof of private-resource absence. No token is recorded.

Approved subject: existing local image
`sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523`.
Destination: **private `ghcr.io/kakoee/rk-uarch-k1-builder:k1-892b9ee`**.
The inherited `rust-lang/docker-rust` source label is recorded for the owner's package-link
and ACL check; it is neither a final-builder identity nor observed registry access.
The actual GHCR RepoDigest is still unknown. The helper refuses a different local image,
non-private existing package, conflicting tag, wrong owner or excessive token scopes.

The [owner helper](owner-registry.py) accepts publisher/reader tokens only at a hidden
interactive terminal prompt, uses a temporary Docker configuration, and retains non-secret
commands/statuses. It does not change the image, namespace, repository credentials or billing.
Its publication/readback operations have **not** been executed; its refusal rules were tested
with synthetic inputs. The owner checks package ACLs in the UI because private visibility
alone does not establish the approved independent access configuration.

The uninstalled [CI template](../U4-B-final-reconciliation-v1/native-job.yml.in) now binds
the actual `.github/native-k1-tests.json` selection, trusted main pushes, environment
`native-k1-private`, a separate reader token and temporary pull authentication. The only
unresolved template field is the observed registry digest. Checkout credentials are not
persisted; pull credentials are cleaned before native execution. The live workflow and
Markdown scope classifier are unchanged. The executable review files in this handoff use
the existing full-CI fallback; only an entirely Markdown diff takes the short path.
Fork-PR native correctness is still an access
follow-up, not a skipped-pass claim.

Newly observed checks:

- The revised container script passed exact tools, full/selected dependency metadata, fmt,
  clippy, pinned cargo-deny and 19 actual native tests in **each** debug/release mode.
  Its six fresh-process replay payloads are nonempty and byte-identical, SHA256
  `30c1e07014f238784ba570a367db1584847134280b2e4190c91761b9b179094a`.
- The new CI result guard rejected the reviewed real release-only byte mutation even though
  its native test exited zero. Restored source, compiled in a separate target directory,
  reproduced the original bytes and passed the guard. Source bytes and mtimes were restored.
- 77 targeted Python checks passed, including fake-Docker private authentication/cleanup on
  success and failure, wrong-event/ref/destination refusal, minimal credential scopes,
  private visibility/tag conflicts and missing/empty/failed/ignored/different replay controls.
  These fake registry controls are not real authentication or hosted execution evidence.
- Repository Ruff, shell syntax, diff whitespace and live strict vendor currentness passed.

[Native execution](native-check.json), [actual fault/restoration](native-fault.json),
[tool/test/replay logs](native-results.json), and [check commands and limits](checks.md).
Native checks used an isolated export of published `bbf87c43ec8616d0bd60d9de06303b70bf8d8002`
with only the two B guard/container files overlaid; their observed hashes are recorded.
The native source remains A's accepted `892b9ee00c485718082e8ea9a765578cbd64d684` subject.
No live source was mutated, and the exact image had no network during native execution.

Inherited evidence remains at [the earlier image handoff](../U4-B-K1-environment-v1/README.md):
accepted recipe/cache construction, 27 crate archive/notice checks, installed OS inventory,
full native fault controls, human U0011 release `ab7d9e0ab81be02a7294d18aeab8bca5591cfda6`
and tool package `83a9a14fd76a00b7858ddd140cc0e0589f80a267`. Those checks are not recounted
as new executions here. Earlier template receipts describe the script revision tested then;
the new native receipts above cover this revision's replay additions.

Remaining: owner publication, actual private ACL and reader access, main-only environment
configuration and secure secret entry; then reconcile the actual digest, install only the
resolved job and obtain actual hosted evidence/review. No M/policy installation, artifact
generation/adoption, human-adoption skip resolution, new dependency/OS installation, shared
server change, spending, K2 work, native qualification or U4 closure is claimed.
