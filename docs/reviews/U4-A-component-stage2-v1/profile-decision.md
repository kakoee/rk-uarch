# F11 — bounded human choice, not an accepted profile promise

A reproduced the legacy behavior with B's D01 transport fixture and synthetic profile:
changing only bundle.mapping_policy.version from 1 to 2 preserves graph/point/profile bytes
and passes admission after recomputing the bundle hash. This is honest profile/1 behavior.
The changed outer request/job hash does not make the independently anchored profile promise
mapping version. No historical fixture/profile/selection bytes are rewritten.

Recommended option P2: permit `uarch-native-test-profile/2`, whose entries extend the exact
existing ProfileEntry with required `mapping_policy: {name, version, buffer_depth}`. Require
checkpoint B and component OR transport_fixture scope; do not narrow the accepted transport
component tests. Require the policy tuple to equal the bundle before other profile variant
checks, refusing `TestVariantNotAdmitted: profile mapping policy`. Format/entry mixing refuses
`TestProfileMismatch: profile policy format`. Profile/1 serialization and promises stay intact.
P2 can explicitly bind @1 or @2 in a NEW reviewed profile. The prototype's eight tests pass.

The concrete implementation is PolicyProfileEntry plus a format/entry validation rule in
NativeTestProfile and a policy equality in admit. Exact mirrors affected are NativeTestProfile
and its MappedEngineJob embedding; MappedBundle and MappedPoint shapes do not change. New
profile hashes flow into bundle/job hashes and future external authority. Graph/point hashes
need not change. No old K2 authority, sealed mapped.py or optimized project is changed.

The parser supports both formats and cannot infer whether authority was newly approved.
If P2 is chosen, the future NEW component authority/selection must explicitly require profile/2
and bind its hash, without fallback; legacy /1 remains allowed only in its existing reviewed
contexts. Unit synthetic anchors are not such authority. New B proposal fixture profiles may
remain /1 while the choice is pending, but cannot be represented as version-bound admissions.
Their separate immutable selection may bind whole bundle inputs, a DIFFERENT promise.

Alternative P1: retain graph/point-only profile/1, and explicitly put the policy tuple and
whole-bundle digest into the separately authenticated execution selection. This avoids profile
schema changes but every public first-use consumer must enforce that additional selection;
ordinary profile-only admission will still allow the reproduced relabel. It is a valid bounded
choice if that is the intended promise. Neither a repository file nor caller-supplied digest
is an external trust anchor.

A's combined proposal will include P2 support as the recommended, unaccepted option. Javid's
choice is needed for protected installation and future profile/authority freeze, not for
continued mapper/checker preparation or B's independent arithmetic. If P1 is chosen, remove
the isolated P2 model/admission changes and their mirror deltas/tests before acceptance; freeze
that exact alternative and recheck affected schemas/admission. No hidden fallback is proposed.
