# Final M plus unchanged selected repair — observed dependency audit

Audit export: published main 95c1774ac15b6de11c7a9cc6d13e18a8a9da7c17.
Final A subject 111b24b0d8a41280431a35b9e3115d93630b6d24; M patch SHA256
**d392b24304a5f63fe69679ce991c5dbf2f742e95fee867a82dec2b0eef3a25e3**.
Unchanged selected repair SHA256
**c238574b284ebecb6f0f1253922ce01af87259f0187aad38bcda628757e8fe6b**.
[setup.json](setup.json) binds the export and verifies every one of A's 26 postimages.
Only disposable Git-export sources received either patch; no live source or artifact changed.

## Final closure and non-import reads

[Observed inventory/origins](audit-1.log), [delta](closure-delta.json): **56 entries**,
zero added/removed/digest-changed versus the historical early M+repair audit. This is a new
measurement, not inheritance of 56 as a target. Combined broad enumeration is 101 (baseline 97,
two policy modules, two M modules). M-only broad policy would still bind its two new modules;
current source/support enforcement is not waived by narrower reachability.

The new mapped.py→assumptions.AssumptionSet edge points to an already retained, unchanged
file. M also imports common/hardware/hashing/prepared/rotary_v2/table, stdlib fractions/
typing and local math; no nominal root/initializer gains a reverse edge to mapped.py.
Parent uarch_contract and rkuarch/hw/engines/scripts initializers remain covered. The final
patch changes none of the pre-existing initializers, canonical helpers, hardware exporter/
derive/protocol, staging/generator, old schema dispatch or lock. All reached files bind
whole bytes, including function-local and conditional imports, regardless of use at runtime.

The final generator still reads its explicit contract/schema/mapped/*.json family in check
mode, now 12 roots including MappedAssumptions. The 11 fixture files are in the separate
contract/fixtures/mapped family. mapped.py itself has no file/environment/network/dynamic
read; registry/profile/full hardware/assumptions are explicit inputs. None of these new
read families enters the existing nominal staging closure at this exact patch.

Test-only dynamic path: contract/tests/mapped/test_admission.py uses runpy.run_path on the
literal contract/tests/rotary_v2_cases.py. That synthetic helper reads its own source bytes
for author identity and contract/tests/fixtures/u2/independent-bundle.json; the admission test also
reads that existing v1 input directly, plus named mapped fixtures/canonical vectors and
schema mirrors. The helper imports only stdlib and contract hashing, not preparation,
counting, a timing engine or an oracle. This is not hidden production dynamic loading.
The policy walker is not asked to bless runpy in a reached nominal module: doing that would
still refuse under its existing dynamic-dependency controls. These tests remain outside the
generator closure and require their own evidence binding to the exact patch.

B's D02/D14 proposal JSON and test-host anchor inputs are also outside nominal staging.
No test-only hardware/profile registry is installed. The future authority loader's actual
Git-acceptance record read, registry/profile reads, resolver/importer/producer/runner and
any new root re-export still need their own audit when real code is published. A plan for
direct imports is not proof of future closure. No source exclusion or repair delta is needed
for the inspected final bytes. The accepted six-file repair scope is preserved exactly.

## Executed controls, expected refusal and limits

[audit-checks.json](audit-checks.json): **173 passed, 1 skipped** in 45.76s, comprising all
existing repair-policy/vendor-entry controls plus 65 final M tests. This newly executes the
nonempty clock-setup control and both altered-job and full caller-rehash refusals against
the original host anchor. It also executes existing public-loader drift/policy/legacy,
__future__/transitive file/package shadow prevention, direct/module/library bootstrap,
source-write denial, origin, annotation and valid/restored-input controls. No new runtime
fault campaign, native engine or image runs are claimed.

The sole skip is real new-policy human generation/adoption, still absent. Synthetic rehashed
loader inputs forbid producers and never establish provenance/current adoption. Combined
strict vendor check exits 1 with `input support inventory changed`, as expected. It is a
refusal, not a successful currentness check. The selected repair changes full vendor-script
fingerprint; unchanged oracle program remains
bca579505e96e3f105d4442e7b6c52c3cbe87316edde3ea896692abceb90993b.
No --historical fallback substitutes for currentness.

Existing CPython 3.12.14 interpreter from coordinator .venv, but scratch/root/src/contract
module precedence and asserted origins. PYTHONPATH/MYPYPATH/VIRTUAL_ENV/UARCH_HUMAN removed;
bytecode and pytest cache disabled; explicit config/root and external-to-export temporary
roots. Complete export file bytes/mtime snapshots before/after normal runs are identical;
only the counts and assertion are retained, not source-wide manifests. Actual support
inventory is retained solely for artifact-policy provenance. Scratch exports are deleted
before publication, never copied as a checkpoint package.

The [existing concrete transition sequence](../U4-B-policy-transition-v1/transition.md)
remains operative with these final M identities: human exact installation release; local
source commit held from push; complete frozen inputs; two human generations; full semantic/
provenance audit; separate complete adoption; integrated tests; publish compatible tip only.
No generation/adoption, staging, policy migration or protected source commit occurred here.
K1 private work after pin/licence acceptance remains independent of M installation.
