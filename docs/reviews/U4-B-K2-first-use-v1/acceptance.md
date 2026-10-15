# K2 first-use candidate and authority joins

This is a Lane B agent proposal, not an acceptance record. All 113 saved bundles and
one finite profile are actual installed-carrier JSON. Every entry is K2/test,
kernel_fixture, fixture_cold, priming0, seed0, ratio1, fixed_delay only; engine fidelity
and precision are null. No component, DMA, transport or model fixture enters this set.
The exact per-case graph/point/bundle/spec/clock hashes and file SHA256s are in
[fixtures/identity.json](fixtures/identity.json). The profile repeats each full hardware
spec because the installed ProfileEntry requires it; no external mutable spec lookup occurs.

| Selection | Membership | Profile/registry binding | Execution disposition |
| --- | --- | --- | --- |
| Kernel | K01, K02, K03-owner, K04, K05, K05-chain (6) | Common exact profile/registry in identity.json; each distinct point/graph | Not run; normal positive controls |
| K06 | K06-00 through K06-04 (5) | Core1.2GHz; other domains1GHz; five exact clock_setup hashes | Not run; ends2500,834,1667,2500,833333333334ps |
| K07 | K07-{800000000,900000000,1000000000,1200000000}-{00..24} (100) | Explicit entries, no wildcard admission; ratio1; other domains1GHz | Not run; frozen edge/end ceil(k*10^12/f) |
| K08 | K08-clock-overflow, K08-add-overflow (2) | Structurally admitted inputs; execution expected TimeOverflow | Not run; no successful result may be emitted |
| Host refusals | Exact named mutations in test_inputs.py | Original synthetic test-host anchors retained except within caller attack | Executed host carrier controls, not native faults |
| Private K03 | K03-schedule-000 through099 (100), literal tie vector | Separate private Wheel API input, not NativeTestProfile entries | Arithmetic checked; Rust execution and public linkage pending |

The three non-baseline clock specs are dedicated proposed designs. Their ID/core frequency
and rationale differ from the installed baseline; registry.json binds their exact hashes.
Baseline 1GHz npu-l4 stays outside test-only_specs. No specs have been installed under hw/.
Registry acceptance must prevent these exact synthetic hashes from entering ordinary
preparation, product tables or reports, including when copied or renamed.

ProfileEntry.expected_outcome is `success` for all 113 *admission* entries: installed
admit explicitly refuses a non-success entry. The independent answer key separately binds
the two expected runtime TimeOverflow refusals. This is not permission to turn overflow
into success. Zero frequency, negative time/cycles, bool coercion, missing/cyclic dependency,
unknown fields and empty jobs are malformed/admission probes against a valid control;
they do not become approved positive profiles. Remaining R01–R21 obligations retain their
applicable structural or later component scope in coverage.md.

## Concrete proposed host record

Proposed location: `docs/reviews/U4-K2-first-use-acceptance-v1/acceptance.json`, installed
only by the coordinator/human following the exact first-use decision. A reviewed host
configuration must select an exact acceptance commit **and record blob hash**, not a
working-directory search or caller-provided path. The host loads that pinned blob, checks
its own expected digest, and supplies authority separately to A's loader. A caller cannot
replace it with a rehashed profile or a self-authored record. This package creates no record
at that location and names no fabricated approver/signature.

The record must bind: decision/accepted scope, corpus revision and identity-file SHA256,
profile and registry content hashes AND byte SHA256s, exact allowed case IDs, seed/clock
hashes, expected refusal map, author/review source commits, accepted semantics, loader
source closure, expected NativeEngineIdentity, compiler/lock/feature manifest, and separate
mode→executable SHA256/target bindings. It must cite the actual decision and review; null
engine/build/decision fields are pending, never defaults. `acceptance-proposal.json` supplies
the already concrete inputs and marks the rest pending. Changing any selected input needs
new review; this is no mutable discovery allowlist.

## Initial acyclic build and replay sketch (reconciled below)

1. Freeze ordinary K2 implementation source closure (Rust kernel, binary writer/parser,
   canonicalization, dependency lock/features, Python loader/runner and installed semantic
   carrier hashes) at real published commits. No fixture/profile or acceptance-record hash
   is compiled into that closure. Code receives explicit authority at runtime.
2. Compute `engine.implementation_hash` from a reviewed canonical build-input manifest;
   `engine.model.implementation_hash` from the fixed-delay semantic source closure;
   `engine.compiler_lock_hash` from the exact accepted tool/target/lock/feature manifest.
   Pin the manifest construction and enumerate actual paths after A publishes the build.
   These are proposed constructions, not invented current identities.
3. Build debug/release offline with accepted tools; bind each actual binary SHA256 and origin
   in the host record separately. The logical engine identity is shared only where the
   reviewed build manifest deliberately admits both modes. Putting distinct binary hashes
   directly into result engine identity would conflict with byte-identical debug/release
   EngineResults; the separate launch binding avoids that conflict without ignoring either
   executable. A must reconcile this with its actual construction before first use.
4. Profile binds points/specs/clocks without job/engine hashes. Then build the job with the
   chosen engine, bundle/profile and registry; its hash binds the entire closure. Final
   acceptance record binds everything after build. It is outside compiled build inputs,
   avoiding profile↔job or build↔acceptance cycles.

A's saved-input loader API is now checked on821dc90. The actual K2 source/binary identity,
public runner invocation and host authority adapter remain pending. The accepted K1 library commit is not a K2 executable identity. Synthetic engine
objects in test_inputs.py deliberately hash labels such as `no-compiler-was-executed`;
they exist only in test memory and confer no public launch permission.

Actual peer reconciliation: [peer-reconciliation.md](peer-reconciliation.md) supersedes the
initial omission of profile trust content from build inputs. Freeze profiles first, then
bind the independent finite trust set in A's build manifest; keep final acceptance/binary
digests out of their own embedded input identity. The actual loader API is now tested.
K06-02 and all nonempty-clock public semantics remain held; expected engine remains pending.
