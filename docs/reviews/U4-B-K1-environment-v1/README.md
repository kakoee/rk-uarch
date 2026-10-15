# U4 B K1 environment and CI handoff

**The exact accepted image is built and locally verified.** Real component/cache checks,
19 tests in each mode, six fresh-process replays, native faults/restorations and the corrected
CI script/host guards pass. Hosted access and native CI installation remain pending separate
private-image publication/access authorization; nothing was distributed or qualified.

Local tag: `rk-uarch-k1-builder:u4-b-e9f69f414983`.
Exact local image ID:
`sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523`.
[Image inspection](image-inspection.json), [build identity](image-construction.json),
[verification](image-verified.json), [faults](image-fault-controls.json),
[exact CI-template result](template-results.json). This is not a published registry RepoDigest.

Human U0011 release: ab7d9e0ab81be02a7294d18aeab8bca5591cfda6;
installed SHA256 f452e2263b9e64a837e0a9fccaae73c7a5b01bd601a5f7cee141e06a7ca23a8f.
Accepted tool package remains 83a9a14fd76a00b7858ddd140cc0e0589f80a267. No repeated vote.
A subject: **892b9ee00c485718082e8ea9a765578cbd64d684**, native bytes identical to
357dea8ee43ae098c284c672a44e6a6cf8482d27. Coordinator 2deb9a3 is integrated; its later prose
changes no native/image input. Earlier B coordination is 07eb628d8478f9c0d753eb9d42b9931108501ccd.

Owned changes:

- Exact disposable construction, 27 archive/notice checks, full versions and tool binary
  identities, 131 installed OS packages/113 copyrights, source isolation and real native
  failure/replay controllers. Accepted recipe/cache fragment are unchanged; no added OS
  package/dependency or host toolchain installation.
- [.github/native-k1-tests.json](../../../.github/native-k1-tests.json) freezes the actual
  uarch_engine library target, 19 names each once in both modes, and A's private replay sink.
  It is verified in the exact local image; hosted CI is explicitly pending.
- B metadata guards now check the full 27-crate lock/cache and exact 26-crate Linux graph
  separately. Full test output uses --show-output to preserve status lines. Restored native
  controls use a separate Cargo target directory so mutated artifacts cannot be reused.
- Live CI's numbered-patch placeholder now checks exact patch/preimage/postimage through
  isolated reverse/forward application. Unknown patches and byte drift refuse. Native job
  replacement remains uninstalled; the Markdown classifier/skip condition is unchanged.

[Checks](checks.md) distinguish actual image execution, earlier existing-host checks,
controller failures/recovery, inherited A evidence and unexecuted hosted work. Initial Docker
unavailability was resolved by a normal start of the installed Desktop application; no
settings or update command was issued. The observed transport version change and transient
disconnect are recorded, and image ID/layers were reverified unchanged after recovery.

All disposable filesystem source/target/tool/cache directories are removed. The named local
image and Docker's normal build cache remain available; no global prune or daemon stop was
performed. No M carriers, policy repair, generation/adoption, human-adoption skip resolution,
K2 work, shared server change, image publication, spending, qualification or sprint closure.

[Construction and exact private-publication proposal](construction.md) gives the remaining
action: publish this verified image to private `ghcr.io/kakoee/rk-uarch-k1-builder:k1-892b9ee`,
with controlled main-only pull access, only after separate authorization. No public-repository
package-access grant, credentials or environment configuration was created. Hosted pull,
actual registry digest, PR access design and CI execution remain explicit next dependencies;
no new pin/licence vote or full later B/human L1 prerequisite is introduced.
