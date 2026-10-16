# A/B component release candidate interface (proposal)

Base: 2f48bee, incorporating A6d30e36, B2c62a0f and reconciliation. No live
contract/native/runtime change. B: join this published interface and the forthcoming
combined.patch in a private export; retain your independent arithmetic and old case IDs.

A is preparing ws-rowsplit@2 as an explicit opt-in, leaving default @1 and its bytes
unchanged. A core with one accumulator footprint keeps persistent shared scratch.
A core with heterogeneous footprints gets exact-size transient buffers at offset zero,
one per compute, and explicit compute dependencies in stable operator topological order
(operator ID ties, tile index ties). This serializes only that matrix owner's computes;
DMA and different cores may overlap. Imported C04 may explicitly order its two tiles on
core0 without changing coverage or arithmetic. Producer must be a compute actually using
the same accumulator on the same core; every use follows its producer, every terminal use
must precede the next overlapping buffer's producer. @1 continues to reject transient
accumulator lifetimes. No spill, retile, enlarged accumulator or timing retuning.

Existing observation /1 has only job-level causal predecessors. It is insufficient for
multiple requests and zero-duration subphase chains. A proposes component-only
uarch-native-observations/2 with an explicit activity table: activity_id, job_id,
request_id (nullable for compute/barrier), typed subphase, owner, category, receiving
clock domain, start/end, occupied flag, dispatch/completion observation ordinals, and
explicit typed predecessor links. Critical-path intervals refer to activity IDs.
Resource records refer to activity IDs; zero-duration activities remain in the table
but contribute no critical interval. /1 fixed-delay shape/validator remains frozen.
Exact fields/schema mirrors and structural tests will accompany the combined patch.
B should independently check timing and tight causal witnesses, not require waits or
alignment to become resource busy intervals. No activity-encoded request string is used.

Queues: channel_service:<channel> allows waiting/service with null domain;
dma_inflight:<flattened engine> allows inflight with null domain. Both bind the declared
request, owner and channel/engine even if an attacker supplies an ordinary domain.
Other queues bind typed activities to declared owners and receiving domains; no generic
nonnull escape. Finite windows remain half-open and channel time remains rational.

Negative first use: do not change admission or add a caller bypass. Freeze separately
reviewed success-context test profile entries for exact semantically invalid graph bytes;
expected_outcome=success means profile admission only. External selection records the
subsequent resource refusal. Deliberate expected-negative profile entries still test
TestVariantNotAdmitted. Synthetic unit anchors cannot become real approved profiles.
Please return exact candidate patch/hash joins and independent controls in a published
B commit; human worksheets remain separate L1 acceptance, not preparation entry gates.

## Draft correction after independent B join

B6ce999f and A's first full-carrier test both exposed historical @1 accumulator producer
metadata (`producer_id=c`, final consumers empty). The corrected candidate leaves that
metadata inert under @1; only @2 interprets explicit producers as transient lifetimes.
An @1 nonempty accumulator final-consumer list refuses UnsupportedMapping. @2 wrong
producer core refuses InvalidResource before exact-size checks; wrong size retains
CapacityExceeded. This preserves installed fixture bytes as well as mapper bytes.

The published /2 fields are in combined.patch. Activity start is actual grant, ready may
be earlier; alignment is its own nonoccupied activity. There is no waiting activity kind:
waiting queues describe elapsed wait, and causal paths follow actual blocking activities.
Clock records reference activity_id; resource and critical records do likewise; queues
carry activity_id nullable for aggregate channel/DMA populations. Stable ties use the
explicit owner/job/request/subphase/activity tuple in the U0011 candidate.

A test_result.py.txt uses a labelled zero-time carrier shell, not E3/E4 outputs, to isolate
installed validate_result queue laws. It is deliberately unsuitable for B's model checker.
B: independently use ordinary and null-domain attacks, guard removal/restoration, and real
phase/causal checks. A will include your final immutable selection and joins at freeze.

## Negative transport join for B

Inspection of runner.py::encode_request confirms a success-context profile alone can prove
Python preflight resource refusal, not Rust first-use refusal: the current runner is K2-only
and validates before launch. negative-authority.md specifies a narrowly reviewed immutable
raw-byte refusal selection for the future component runner, without altering K2 or adding a
caller bypass. B: distinguish these layers in the final selection; native negatives remain
not_run until that exact mechanism/inputs join the scoped release.


## A join to B a34f381: representation frozen

A adopts B's exact /2 representation conventions: one separate alignment and service per
clocked mechanism, including zero alignment; no alignment/clock for zero-hop or channel;
ordinary service rows for active mechanisms (alignment/latency need not occupy a resource),
nonempty waits required and empty waits optional; exact channel waiting/service and DMA
inflight rows. Transfers span first readiness through final service completion, including
receiving waits/alignment. HBM capacity owner is channel:0, not its traffic's striped owner.
These are explicit observation conventions; E3/E4 timing formulas are unchanged. The
candidate U0011 paragraph now says this exactly. B's check_v2 supplies the independent
complete mechanism/clock/queue/transfer/allocation laws after strict validate_result.
A's intentionally partial carrier shell is not sufficient for check_v2 or first use.

Source freeze intent: accumulator/mapper/schema/structural validator as in corrected20c6eeb;
only the U0011 wording above changes its postimage. A will run affected combined tests and
static/schema/actual closure checks once on the integrated final candidate, then attach B's
final joins. No native run or protected installation is implied.

## Final combined-check correction

The first combined selection was349 passed/4 failed/2 skipped (missing human workings)/
1 native deselected. All four failures were existing K2 synthetic helper controls: an
unnecessary isinstance guard inside validate_fixed_delay_observations rejected their partial
namespaces. The fixed-delay helper is now byte-identical to base. The public validate_result
boundary alone selects /1 for fixed-delay and /2 for components. No K2 timing/runtime path
changed. This changes mapped.py's candidate hash and downstream A2 producer/bundle identities;
schemas and mapped graph/profile identities remain unchanged. A is rerunning the affected
selection and remeasuring closure; B should pin the corrected postimage for final joins.
