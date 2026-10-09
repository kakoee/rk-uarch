# RC-P1 shared-validation checkpoint — coordinator recheck

RC-P1 is implemented and ready for coordinator recheck. Full report completion
remains partial: package/write/load and default-hidden HTML/Markdown completed;
B-owned repeated recipe scans block the remaining full opt-in/repeat exercise.
No freeze or human generation is authorized by this checkpoint.

Only `contract/uarch_contract/hashing.py` and `report_context.py` advance in
production. The added focused test file is `tests/unit/test_u2_a_resolution_session.py`.
Everything else authored here is checkpoint evidence. Existing A CLI, runtime loader,
producer, engine, hardware, B report/proof, schemas and policies are unchanged.

The entry receipt verifies all 530 A4 payloads against manifest
`438676cc3cdf51f2e14e680f7eafeb418294c099a4eabaa3d5425f3341e2cee2` and records
834 received tracked/untracked files. HEAD remains
`1e9e794a84c5173812c23a1cf2fc04b85e6f6831`. Only the two authorized source files
change among those received files. Historical handoffs, manifests, logs and inputs
remain identifiable and untouched. New hashes identify uncommitted bytes, not Git
history protection.

## Private ownership and unchanged checks

Each public dependency/context validation creates a private resolution session.
The context entry shares its own session with its private dependency-validation
helper; a separate public dependency call always authenticates independently.
The declared-closure walk similarly creates its own session. No session, mutable
cached artifact, caller verified flag or persistent/global cache is exposed.

The session supports the existing lazy A loader. Each requested value is detached
before admission, then authenticated using the existing artifact identity and
self-field checks; raw bytes use the existing SHA256 check. Structural copies own
JSON containers without invoking caller `__deepcopy__` hooks. Tuple/list semantics
stay distinct. Only a top-level BaseModel is serialized, matching the existing
resolver; an invalid model nested in an untyped dictionary still refuses. No
canonicalization, identity algorithm or new wire representation was introduced.

This is a synchronous private ownership invariant: internal validators only read
owned cached values; they do not mutate them, hand them to caller callbacks, or
return them from public validation. Lazy unresolved inputs must authenticate when
first requested. A later public invocation creates a new session and sees changed
or missing bytes; it cannot reuse a previous success.

Authenticated ComparisonArtifact and ReferenceInventory models, and the inventory's
checked unique fixture-index map, are parsed/built once per identity in the session.
Every ratio still performs its actual/reference source, model, component, precision,
query, TP, projection, channel, purpose and declaration joins. `_validate_actual_source`
still runs for every ratio, including every known quantity. Recursive recipe visits,
source-purpose/model/scope checks, review closure, pointer checks and cycle behavior
remain operative. Invalid numeric identity refuses; genuine numeric failures remain
data. The closure walk keeps all individual selector-pointer checks and raw child
traversal. The ordinary public resolver still authenticates and returns its caller
value as before; only private session inputs use private cached resolution.

`preservation-and-api-final.json` records exact old/new source hashes, unchanged
public signatures and identity-function ASTs, unchanged production schema bytes,
and the preserved entry audit. There is no callable or loader-field delta for B.

## Tests-first, mutations and cost evidence

The first tests were run before production edits. `before-v2.txt` isolates three
expected ownership/authentication failures; an earlier test selected the wrong
assumption artifact and is retained in `before.txt`, not reported as a product defect.
Later failing tests exposed a dictionary copy hook retaining caller ownership and
an accidental nested-model normalization; both red snapshots/logs and fixes are
preserved. The final focused file has 14 passing tests.

Coverage includes one authentication/model parse per session identity with ALL ratio
source checks, detached nested containers, caller mutation during a call, changed
nested bytes on later calls, missing/tampered raw bytes, every pointer check, duplicate
fixture IDs, rehashed comparison-index substitution, ordinary resolver behavior and
malformed nested models. Existing shared/A/B tests retain fresh-review wrong-source,
equal-value substitution, wrong model/purpose/deviation, recipe cycles, raw file
closure, disk-loader mutation and report-capability refusals.

The small preserved fixture has identical context and terminal-selector result hashes
before/after. Genuine context authentication calls fall from 1,042 to 10 and each
comparison/inventory model parse count from 60 to 1; all 60 actual-source checks
remain. Standalone dependency authentication calls fall from 860 to 9 and each model
parse count from 30 to 1; all 30 source checks remain. `counts-before.json` and
`counts-final.json` contain exact source hashes and local timings. These are bounded
measurements, not a full-report timing claim or a flaky threshold test.

A fresh full baseline completed candidate execution and then was interrupted at the
explicit 120-second total bound during package validation. It is NOT a completed
baseline; the coordinator/B 4.38-hour extrapolation is still not an executed time.
The original shared source hashes and interruption are in `baseline-observations.json`.
A separate 90-second cProfile sample is also explicitly interrupted diagnostic evidence.
It identifies remaining ordinary closure/hardware validation, serialization and B YAML
assembly costs; it does not bypass checks or authorize changes outside these two files.
Intermediate full runs stopped for the two ownership refinements remain marked
interrupted and are not final report acceptance evidence.

## Isolated current consumer and final checks

`staging-receipt.json` identifies 500 inherited integration files under a fresh `/tmp`
root, including the nine exact RC transfer paths. Only required src, contract, scripts,
tests, hardware/config/package files and explicit immutable fixture paths were copied.
The multi-gigabyte review history was not copied. Integration's proof, adapter and A2
export fixture path adaptations remain byte-identical. The staged overlays identify
only A's two shared files and its added test; inherited B implementation is not A authorship.
The preserved B handoff/manifest envelope hashes verify against the supplied hashes.

Fresh explicit synthetic inputs are rebuilt from each staged source revision; frozen
support verification remains enabled. No old frozen candidate or intermediate
unverified assembly is used as acceptance evidence. Reference scaffolding is explicit;
upstream source bytes are copied as data and no upstream oracle is executed.

Final source checks are recorded under `final-checks-v2/` with exact argv, cwd,
environment, tested hashes, exits and timings. Earlier run directories are historical
attempts, not additive totals. A/shared:184 passed; current B refresh:29 passed;
combined report/proof/consumer/shared:163 passed. The 14 new focused tests occur in
both the A and combined selections; these counts are not summed into a false distinct
total. All these selections have zero skips. Snapshot gates separately remain
4 passed /2 active failures (generator/oracle fingerprints and missing new upstream
source copies). Neither failure is waived or relabelled.

A mypy checks 49 files and combined mypy checks 62; focused Ruff and both schema
freshness checks pass. No dependency installation was needed. The main existing
Python3.12.14 environment is used with bytecode disabled and pytest cacheprovider off;
combined work is under `/tmp`. Both mypy checks were also repeated with an
explicit `/tmp` cache directory (`typing-cache-check.json`); prior caches are preserved.

## Remaining authority and handoff

See the completed/remaining full-operation evidence below. Full-report completion
is not asserted.
No engineering-hour estimate is revised from validation timing alone. Synthetic
references/reviews confer no positive real evidence eligibility; energy quantities
remain unproduced and no proof interpretation or policy was changed. B's separate
report completion/reconciliation, reviewed source freeze, human created/verified pair,
strict semantic audit, explicit adoption, final independent review and publication/
closure remain separate.

Proposed checkpoint message (not committed):
`perf(u2): reuse detached authenticated artifacts within shared validation calls`

No staging, commit, push, tag, human flag, oracle generation/adoption, dependency
installation, agents/messages, cleanup or other-worktree edits. Stop for coordinator
recheck after the final checkpoint inventory is written.

## Exact source delta and proposed checkpoint files

- `contract/uarch_contract/hashing.py`: `139be8778b494e003365a537efe2eef5334c3e87324bef424fe15dcf84b8fd4f` → `ee8eac838b6a76b9cda0d0cc3d392ad0d6795d8b27e33b23582b4c1467fee9cc`.
- `contract/uarch_contract/report_context.py`: `58fbf61d90e80d53ef9eb2c101a8211d8269400531927f591680880b1eaad168` → `62b7e47fe2b63fc420b042031fc66295358c0940cdb8d098b5f3627b49ba7e55`.

The exact patch is `U2-A-RC-P1/source-delta.patch`. Proposed code/test files are the
two paths above and `tests/unit/test_u2_a_resolution_session.py`; proposed checkpoint
documentation is this handoff and `docs/reviews/U2-A-RC-P1/**`. No inherited B
implementation belongs in A's production commit. Source files copied inside fresh
synthetic input fixtures remain identified test data, not A-authored B changes.
`changes-from-A4.json` lists the full before/after payload delta and new files;
`SHA256SUMS` covers the full changed-path package including historical payloads and
new execution evidence. The current manifest excludes only itself; its entry count
and SHA256 are returned separately to avoid a self-referential hash. Prior manifest
and delta envelopes remain included and unchanged. The receipt audit covers all 834
entry files, including unchanged baseline files beyond the changed-path package.

## Full operation: completed evidence and explicit remaining blocker

`full-report-final-v2/observations.json` and `full-after-final-v2.txt` describe final
source bytes. All40320 ratios pass through the genuine B `refresh.report_package`
and A public build/write, disk load and memory verification paths. Counters wrap and
forward the real functions; no success is monkeypatched. There are 1008 fixtures per
track, 46,296 render recipes, 14,904 source recipes, 24 table rows and 7 raw blobs. H1
executes 96 fixtures, 48 produce explicit WeightCapacityExceeded failures, and 864
physical fixtures remain not_run. The nominal test-only candidate executes; this is
not an upstream oracle run. No energy quantities or positive evidence eligibility
are invented.

| Completed phase | Seconds |
| --- | ---: |
| Fresh synthetic references | 0.228 |
| Complete candidate capture | 35.349 |
| Full report package | 120.731 |
| Public table write | 118.235 |
| Public disk loader, producers disabled | 138.719 |
| Public memory loader | 134.647 |
| Default-hidden HTML/Markdown render | 987.485 |

Each of package/write/disk/memory/hidden performs 131,040 actual-source checks,
including 52,104 known-quantity checks (multiple public validations legitimately
repeat all ratio checks). Multiple public sessions explain the 10 comparison/5
inventory model parses per operation; no cross-public-call cache is used. Individual
session count invariants are independently tested. Counts/timings are local observed
runs, with concurrent diagnostic activity possible, not an isolated benchmark or
promised performance ratio.

Fresh test input digest:
`fb61c39206abc2764c543896f81ae59e2dde914b7b8f38bf54618c3ce87068ad`.
This identifies synthetic test inputs from final shared sources, not a final source
freeze or an accepted oracle/reference artifact. The table content identity is
`sha256:22b87d37efb5faf027b3506d56231d459176e39de9ad2d016673de6ed97cb0d1`.
The complete table/artifact/output file hashes and independently inspected hidden
coverage are in `partial-output-inspection.json`.

- `hidden.html`: SHA256 `504b5df51faf492c2ac76d3fdcdcbb9c85d48ff62d3a8738846784f98f3d2e77`, 136,608,559 bytes, all40,320 ratio paths.
- `hidden.md`: SHA256 `b082fae5c853ff07aaa53a3380fe801838976a5e2e4010381b62cc2bddc4aefe`, 135,184,748 bytes, all40,320 ratio paths.

Hidden comparison numbers were asserted absent by the genuine driver before files
were written. Both output files independently contain the exact complete ratio path
set. Explicit STUB rendering was interrupted after 200.008 seconds, total run 1,736.691
seconds; its traceback lands in B's repeated recipe scan. Full opt-in output,
repeat hidden/STUB bytes, full replay package/write/render byte comparison and the
full-size capability mutation phase remain unexecuted/incomplete. Smaller existing
STUB/determinism/capability regressions passed; they do not substitute for those full
exits. `inspect-full-output.py.txt` is an unexecuted completion checker, not a passed
check. The partial inspector initially used an incorrect table dictionary key;
changing it to the existing `table_hash` field completed inspection without changing
any runtime or output bytes.

`remaining-renderer-proposal.md` locates the B-owned cost, includes the actual
Evaluator profile and interruption, and proposes only a private declaration index
plus focused tests. It preserves ambiguity/duplicate behavior, all contributors,
all source/proof rules and every validation. Nothing in B was modified. The completed
hidden render is 987.485 seconds; the before full operation was interrupted and thus
there is no fabricated completed before/after speedup ratio.

Saved prepared-input replay completed independently in `full-replay-results.json`:
a new complete capture took 32.759 seconds, saved physical-input replay 12.010 seconds.
Physical prepare/producer/engine entry points were trapped; the actual nominal
candidate continued to execute. `replay-byte-check.json` repeats that saved replay
and verifies exact bytes of all 3,307 artifact files and nominal/physical/inventory
JSON in 12.486 seconds. This supplemental check uses bytes, not Python numeric
mapping equality. Both tracks retain 1008 fixtures and the same 96/48/864 physical
outcomes. This proves prepared-input replay and comparison artifact determinism,
not completed full rendered-package determinism.

Reproduction commands/environments are in `commands.md`, the phase observations and
`final-checks-v2/checks.json`. Earlier `full-report/`, `full-report-final/`, `checks.json`
and `final-checks/` refer to earlier source revisions and stay identifiable. No old
log is presented as a final-source execution. This is a bounded original-author
checkpoint, not the later independent review or a closure of all U-P3/report exits.
