# Audit of A's first published exact M package

Peer commit: `bad9a125d82bbf723675465c9291fb37fa82f799` (integrated on Lane B main).
Protected patch SHA256:
`3e47b970de619b013b8d46d754e9451c604d010b2763e5a0cfce9ff9d755a63b`.
Source: [A inventory](../U4-A-M-package-v1/inventory.md), confirmed against actual patched
files in the disposable combined export. This is an author dependency audit, not an
independent-review verdict or M acceptance. Later revisions require delta reconciliation.

## Actual import, initializer and non-import boundaries

All19 paths are additive: mapped.py, generate_mapped.py, one admission test module,
11 schema mirrors,5 fixtures. Existing root initializer, shared validators, old schema
generator/hash dispatch, hardware export/derive/protocol and staging source are untouched.

mapped.py imports stdlib fractions/typing, Pydantic and local common/hardware/hashing/
prepared/rotary_v2/table. Its function-local math.gcd is included in the audit. No
TYPE_CHECKING, plugin/importlib/eval/exec, file/environment/network access is present in
this module. Profile, registry, hardware and bundle are supplied objects. Parent
uarch_contract/__init__.py still executes; it was already retained, and its bytes do
not change. The reached prepared validator's local comparison import is still included.
The import from mapped to rotary_v2 is **not** a reverse reachability edge from nominal
staging. No already reached module imports either new M module at this pin.

generate_mapped.py imports mapped.SCHEMA_ROOTS plus argparse/json/pathlib. Its explicit
read family is contract/schema/mapped/*.json, including unexpected files for freshness;
its non-check mode writes that same output directory. This audit invokes no generation.
Tests read exactly component/kernel/kernel-job/profile/registry JSON and mirrors via
check mode, with drift probes in tmp_path. These read families are not existing nominal
staging families. There is no automatic schema registration or new registry search.

The actual nominal path remains scripts/u2_inputs → uarch_contract.exports and
rkuarch.hw.export → hw.derive → engines.protocol, including all parent initializers.
Existing policy data include pyproject/uv.lock/npu-l4, precision/execution inputs,
a2-export JSON/YAML/PIN, canonical model shapes and retained provenance. M adds no file
inside these families and changes no family bytes. Profile/registry/schema fixture data
are therefore not reached from nominal generation at this exact pin. If a future loader,
common validator or initializer reads them, register/audit that read before freezing.
M does not exempt them by filename or by being a schema output.

## Measured proposed closure

Using the actual reviewed support walker/public controls, not a target count:

| Export | Broad enumeration | Proposed closure |
| --- | ---: | ---: |
| Installed baseline | 97 | not installed |
| Exact repair | 99 (two new scripts) | 56 |
| Exact M + repair | 101 (two M modules plus two scripts) | 56 |

All56 path/digest pairs are identical between repair-only and M+repair. Added/removed/
changed proposed support edges due to this M patch are empty. The unchanged97→56 policy
delta retains39, removes58 and adds17; [closure-delta.json](closure-delta.json) names them.
This result applies only to these bytes. Actual mapped producer/importer, hardware
resolver, protocol mirror, native runner, test-spec registry/bootstrap and B product
consumers are not implemented in this A patch. Their real imports/reads must be audited
when published; proposed direct imports do not certify future absence of cycles.

Under still-live broad U0002, M alone would change97→99 and refuse old support, regardless
of reachability. Under the proposed policy M's additions are unrelated to this generator,
but installing the repair itself still changes full vendor/source fingerprints and
requires human migration. A zero M delta is not permission to use the current artifact
with repaired sources. Strict combined refusal is recorded in m-2.log.

## Exact fixture joins received; remaining joins

A's kernel fixture is exactly B K01: a3000ps/owner0, b5000ps/owner1, c2000ps/owner0
with edges a→c,b→c. Its expected7000ps/critical path b→c is independent B arithmetic;
A supplies input identity only, no native execution/result.

| Object | Exact content identity in the published proposal |
| --- | --- |
| kernel graph | sha256:6d8c371a4863af025f829ebd3325e385f89625579ba633cb993c66c1ca12e15c |
| kernel point | sha256:3a6a4d450ff2e3f0fe5688ec6d1dd6a07467843f0cfab5840110f91e20d667de |
| kernel bundle | sha256:71d197fa3abb6604c322d786c048f142f3ca8b7d44ad8efbf4bb3bafc5827c23 |
| profile | sha256:183120d056b6345f6a41e8bd7434da7dfbffc7aa0b6e61311976d7d32e8a8a12 |
| registry | sha256:86be9e61f32c89b52baa09785f2e3f98320bb185ba6cbf6793bbafd930a58ee2 |
| kernel job | sha256:9a38750b9022492caa2f76954a8ae37fb67cffd6d82ee54e01ed4e9516963bf7 |
| cold m3/k5/n7 component bundle | sha256:9982d42389eb6db3cc25cb300b080bcd23e4eca5db16f424191f11d56bf61f2b |

Profile semantics_revision=U0011-stage2/1, case_id=E1-input,
selection=A-schema-input/1, owner explicitly says schema prototype/B freeze pending.
All clocks1GHz, ratio1, seed0, fixed_delay only, K2/fixture_cold/priming0/success.
Registry has zero synthetic specs and explicitly excludes production baseline from its
future test-only set. This is not a qualifying B-catalogue profile, signed human approval
or blanket clock/credit permission. Job engine/compiler hashes are unbuilt placeholders.

The cold component matches B C02/C05 **work**: useful210/issued393216 ops,
100/42 payload and512/256 transaction bytes,3 DMA requests. Its addresses route to
channels0/1/2, whereas B C05 proposes6/6/6. Do not reuse either whole-job timing or identity
across that placement difference. C02's547000ps remains resident compute duration, not
cold end-to-end time. No exact B C05 graph/profile join is claimed.

Concrete remaining input joins for A/coordinator:

- Publish/review full B catalogue profiles and registry/specs; only K01's input shape is
  supplied here. Remaining E2/E4/C08 variants must receive exact full hardware/graph/point
  entries and named refusals. Preserve proposed-design provenance and production refusal.
- ClockSetup lives inside MappedEngineJob; profile currently binds point/graph but not
  clock_setup. Before K06/K07 qualification, freeze those job-only start/domain/cycle
  fields in the approved case/job manifest and define the trusted manifest check. Do not
  let one selected case silently vary them while retaining the same profile entry.
- Resolve approval/signing and trusted registry/profile/bootstrap identity explicitly;
  hash integrity of caller-supplied objects alone is not approval. A already marks this
  pending. B does not invent a signer or accept an empty registry as future coverage.
- Reconcile precise refusal layers: current admit compares the profile tuple before
  state validation, so an unlisted state mutation yields TestVariantNotAdmitted; testing
  UnsupportedInitialState requires a matching profile tuple that reaches that layer.
  Host/admission mismatch is AdmissionMismatch. Fixture mutations must name the intended
  layer and reseal the appropriate identities, not assert an error from another layer.
- Complete A's stated M controls and actual loader/producer boundaries. The executed22
  M prototype tests are not all R01–R21/public runtime or result-observation qualification.

No M fixtures or schema were installed. No source producer, oracle or native runtime
was called. New published bytes supersede only this audit's prospective join, not U3 history.
