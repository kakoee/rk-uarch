# Continue U4 Lane B — final M, fixture and CI reconciliation

Continue the existing Lane B session in `rk-uarch-u4-b`. Pull/integrate published main
normally, preserve peer history and read the kickoff workflow. This is the bounded follow-up
to your published `dd75b7c` handoff, not a new architecture review or implementation release.

## Exact inputs

- Final A subject: `111b24b0d8a41280431a35b9e3115d93630b6d24`.
- `docs/reviews/U4-A-M-package-v1/`: handoff, package.json, protected.patch,
  inventory, decisions and peer-reconciliation.
- Final M patch SHA256:
  `d392b24304a5f63fe69679ce991c5dbf2f742e95fee867a82dec2b0eef3a25e3`.
- Tool package `docs/reviews/U4-A-toolchain-v1/`, published at
  `83a9a14fd76a00b7858ddd140cc0e0589f80a267`.
- Existing selected repair `docs/reviews/U3-B-artifact-dependency-audit-v1/repair.patch`,
  SHA256 `c238574b284ebecb6f0f1253922ce01af87259f0187aad38bcda628757e8fe6b`.
- Your verification-inputs, native-ci and policy-transition packages; coordinator checks
  in `docs/reviews/U4-A-final-package-reconciliation-v1/`.

## Bounded work

1. **Final dependency audit.** Apply the exact M and repair proposals only in a disposable
   export. Recompute closure from final imports, initializers and data reads, including
   A's assumptions import and test-only reads. Explain differences from the historical
   early 56-file audit; do not assume that count. Exercise relevant closure/loader and
   shadow/isolation controls. Record strict refusal of the old adopted artifact and the
   remaining real human adoption case honestly. Preserve the selected policy and repair;
   propose a bounded delta only if a concrete defect requires it.

2. **Fixture and trust joins.** Check the clock_setup binding, nonempty positive control,
   caller-side full rehash refusal against the original host anchor and refusal ordering.
   Map your first-use cases to A's concrete carrier/profile/registry inputs. Preserve A's
   channels0/1/2 versus B C05's6/6/6, and resident C02 versus cold whole-job timing.
   Correct D02/D14: SRAM initialization must use a declared resident fixture or explicit
   producing jobs, never implicit preload under the common cold shorthand. Supply exact
   independent expectations and identities for the choice; do not change accepted model
   laws. Distinguish proposed host authority from actual human acceptance. List unresolved
   first-use fixture bindings precisely without turning the full later B/L1 corpus or
   unfilled human worksheets into a new K1 prerequisite.

3. **CI and tool reconciliation.** Validate exact pins, target, features/lock/checksums,
   cargo-deny command/config and the proposed licence scope against A's retained evidence;
   use primary sources for any fresh external verification. Do not accept licences on
   Javid's behalf. Reconcile your actual template with the fact that A's base/recipe has
   neither Python3 nor an offline dependency cache. Prefer running your stdlib guard on
   the hosted runner outside the native container if it preserves the required checks;
   otherwise propose an exact pinned Python-layer closure. Spell out file paths, logs,
   exit propagation and host/container tool identities so guards cannot validate the wrong
   installation. Preserve docs-only CI behavior and distinguish skipped jobs from passes.

   Deliver reviewable commands/recipe and inputs now. Keep the final built image digest,
   locked offline cache, discovery checks and real debug/release execution as explicit
   post-acceptance work. Do not substitute the base digest for a final builder, invent
   K1 test names, or count an empty workspace/selection as a native pass. Define where
   actual K1 test names/multiplicities and failure controls will be frozen with A after
   the tests exist. Do not build/run the image or implement/execute the native kernel
   under this preparation task.

4. **Return a compact decision-ready handoff.** State exact changes, observed versus
   inherited checks, final dependency inventory, CI construction dependencies, and the
   smallest remaining human M/trust/lifecycle and separate K1 pin/licence decisions.
   Keep K1's independence from M installation explicit. Do not request a new vote on
   accepted U3 architecture or make runner registration/full tables a correctness gate.

Use Git diffs and commits; no copied checkpoint trees. Tests must not mutate live source.
Run affected checks with explicit config/root and verified import origins in disposable
exports. Preserve prior evidence and peer bytes. Commit/push only your ordinary owned
proposal/docs/tests using normal main integration and hooks. No live protected install,
policy migration, generation/adoption, shared-server changes, native execution or gate
closure. Do not wait for hosted CI. Stop with the exact published handoff for coordinator
reconciliation; do not issue an independent-review verdict.
