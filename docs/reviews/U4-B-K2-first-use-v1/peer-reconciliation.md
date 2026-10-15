# Published A loader reconciliation and exact open semantics

After independent fixture bytes were frozen locally, A published loader
`f213317ec61622c91e74c9f42e95578e80432588` and handoff
`821dc908a3735ef3225f16b56172e802095d77f0`. B fast-forwarded main normally and exported
821dc90 privately. The original 4f3be8f fixture inputs/answers remain unchanged; this is
additional actual-peer evidence, not a rewrite of independent expectations.

## Actual API and executed controls

`rkuarch.workload.mapped.{loads_fixed_delay_job,load_fixed_delay_job,
export_fixed_delay_job}` consumes an exact full installed MappedEngineJob. B constructs
those jobs from the committed finite bundles/profile/registry/clock tuples using explicitly
synthetic engine identity in test memory. These APIs accept bytes or one explicit path,
return the installed carrier, and require separate trusted_registry_hash,
trusted_profile_hash and expected_engine. Export reparses current content before exclusive
file creation; it never remaps or regenerates.

`test_peer_loader.py` executes17 representative positives covering every base kernel case,
all five K06 rows, all four clock variants and both admitted overflow inputs; the latter
are input admission only, never successful native execution. Six actual-loader mutation
controls test changed nonempty clock, wrong case, wrong source-bound synthetic identity,
wrong engine, rehashed registry and full caller graph→point→profile→bundle→job rehash
with changed seed/clock. The fully rehashed attack is internally valid under a separate
attacker-only synthetic host anchor, but refuses against the unchanged original anchor.
Export refusal leaves no output; each attack has a restored valid control.

The 24th check exports K04, runs three fresh isolated Python loader/export processes
(original source once, relocated source twice), and compares all canonical bytes. The
relocated source copies only the actually imported consumer module closure from the pinned
peer export, independently of generator support. Every local module origin is checked.
Producer, mapper, rotary producer, engine and scripts/vendor imports are denied, with six
explicit positive denial probes; subprocess/system spawning is forbidden during loading.
Deleting the relocated mapped loader gives ModuleNotFoundError and no output, demonstrating
that the source guard cannot fall through to the live/editable installation. Saved bytes
and the copied sources remain identical throughout the positive controls; deletion occurs
only in the final private negative control. No live source or artifact is mutated.

`peer-audit.json` is newly executed B evidence: runtime and conservative AST local closure
both contain26 files including all parent initializers. The sole file opened during actual
loading is the explicitly supplied saved input. Host authority arrives as explicit arguments;
no Git acceptance file, registry search, home directory or environment read creates authority.
The synthetic host anchor is separately frozen by the harness, not inferred by the loader
from the caller. Generator support remains56 entries with the same canonical inventory hash
and strict currentness passes. The new loader and workload initializer are outside nominal
roots; no initializer changed or reverse edge was added. No lifecycle is required for this
actual additive delta. The future real host-record resolver and build reads remain unaudited.

## K06-02: retain the discrepancy; do not authorize its public mapping

The frozen row projects raw `next_edge(core=1.2GHz,start=835,n=0)` into a clock job and
expects1667ps. A's proposed convention and installed K1 zero-cycle handling complete at
the actual grant,835ps. B's explicit a-wait produces that grant at835, so the difference
is832ps and is not an identity/import issue. K06-01 starts on an edge and K07's100 rows
all start on edges, so they do **not** discriminate this conflict. K06-03 uses one cycle
and independently expects2500ps under either zero-cycle convention. B did not adjust K06-02
to make A agree; its bundle/profile/answer bytes are retained for coordinator review.

The raw primitive answer1667 is correct. Treating it as the result of a zero-cycle owned
job is the unresolved projection; this is not a discovered defect in A's non-executing
loader. Preserve both obligations: the primitive's never-early n0 alignment and the
owned zero-job inline/owner-grant law. Smallest reconciliation proposal is to explicitly
separate the raw primitive check from the zero-cycle public job check, retaining both,
and resolve how the primitive is observed at K2's public boundary. Do not silently drop
K06-02, relax its expected answer, change K1's reviewed zero semantics or invent event
injection fields. If new public clock semantics/carriers are chosen, return an exact
protected delta and re-review the affected profile; no such delta is installed here.
All nonempty-clock public execution remains held pending the exact first-use convention.

A also proposes start_ps as earliest release and n>0 conversion from actual grant, with
fixed duration0 for clocked jobs. B's explicit wait jobs are visible frozen input, not hidden
adapter-generated delays, and make grant/start joins checkable without new release behavior.
The general release convention, arbitrary future release events and attribution of initial
idle time still need exact reconciliation; the existing loader only validates their hashes.
A's partial event-kinds patch adds DEPENDENCY_READY/OWNER_GRANT but not TASK_RELEASE.
The installed enum genuinely lacks the two actual K1 dispatch kinds. Keep A's patch
unapplied; full release vocabulary, queue-domain representation and all-zero result convention
remain explicit protected/semantic joins before native result construction.

## Causality and build identity

A's proposed observation-derived tight predecessors agree with B K01 and K04 intervals:
K01 c is blocked by b, not early a; K04 z is blocked by owner a, not early dependency p.
A's FIFO F case ends6000 and is a different graph from B K02's10000; neither replaces the
other. A's idle-owner and equal-cause cases add needed discriminators, not executed evidence.
Canonical tie and zero-partition rules must be bound before accepting result bytes. Only
actual dispatch/grant/completion records can establish causality; no K1 predecessor-list
copy or independent arithmetic may fabricate missing runtime evidence.

Reconcile the initial B build sketch in acceptance.md with A's concrete direct-Rust trust
requirement: freeze profile/registry first, then include a separately reviewed finite trust
set in the build-input manifest. Because profiles contain no engine/job/binary/final-record
hash, this remains acyclic. The *final acceptance record and executable digests* stay out of
the embedded identity's own inputs. This supersedes B's preliminary suggestion to omit
profiles from build inputs; it is a construction proposal, not new source or acceptance.
One logical engine identity may bind separate exact debug/release executable digests in the
host record, preserving byte-identical result identity while checking both actual binaries.
The actual K2 implementation/model/compiler manifest hashes and binary hashes remain absent.

A's exact sha2/numeric-feature proposal, resolved Cargo lock/feature/target/checksum/cache
extension, Python↔Rust canonical float/u128 parity and framing remain separate construction
joins. Existing K1 choices stay accepted. B installed no dependency, built no image, executed
no Rust and gives no new licence/feature acceptance. Use A's published proposal for that
bounded extension; no substitute hash implementation or fake result generator is authorized.

Read-only apply check of A's exact protected event patch passes at821dc90; patch SHA256
6dd4ebdfd9c4e6be8a5c36ebc98cb117bfdbf745980827957aa0ba98c6c2c76c. No file was patched.
