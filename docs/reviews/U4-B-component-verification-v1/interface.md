# A/B interface and findings

Actual joined A APIs: `mapping.component.map_component`, `workload.component.component_point`
and `prepare_component_bundle`, `workload.mapped.export_component_bundle` and
`load_component_bundle`. Published input revision is recorded in inputs.json. B tests actual
small/tail/full-row mapping, coverage, useful work, payload, striping and relocated replay
with mapper/workload producers disabled. A's existing full mapper tests are an additional
integrated selection; B's tests are separate. Alternative valid SRAM placement is admitted
and changes identity. Equal useful work does not establish equal transfers or timing.

A's cold C02 carrier uses channels0/1/2. Independent E4 calculation: reads both have latency
end48000, per-channel end50250, no NoC return hops; shared port commits52000 then53000.
Compute completes600000 (53000+547000). Y write: port601000, one-hop arrival603000,
latency651000, channel653250, return656000, acknowledgement656000. Total **656000 ps**.
B C05 channels6/6/6: commits60000/62000, compute609000, write669000. Total **669000 ps**.
These answers are independent of A implementation and remain native not_run.

## F-B-01 — old C04 is arithmetic, not an admitted native positive

The old C04 selects m256 and m1 on one core, with separate live buffers. Installed
`validate_resources` requires accumulator.size_bytes == 4*M*N for each job, giving262144
and1024 bytes. Disjoint placement exceeds262144. Overlapping distinct buffers requires a
legal lifetime order, but accumulator final_consumer_ids cannot name compute jobs under the
current readers enumeration. Sharing one larger buffer violates exact-size equality for
the tail. Keep the1855000ps old arithmetic, not a passing fixture. The concrete C04-carrier
input reaches CapacityExceeded in the resource validator. C04-control uses two m3,k5,n7
operators sharing the same84-byte accumulator, independent disjoint SRAM, same matrix owner:
1094000ps. It verifies serialization without pretending to discharge old unequal-size reuse.
A/coordinator must decide the actual reuse representation before that first use. No protected
patch is applied and no model law is retuned.

## F-B-02 — negative profile admission short-circuits resource tests

`admit` rejects profile.expected_outcome != success with TestVariantNotAdmitted before
resource validation. C04/C06/C07 resource negatives therefore have two distinct observations:
actual Python resource refusal and expected profile-admission refusal, neither a native pass.
A future approved positive-context semantic mutation or separately released refusal path
must reach the intended resource guard. A synthetically rehashed trust anchor is permissible
only in the visibly labelled schema unit test, never as actual first-use approval.

## F-B-03 — worksheet authoring error preserved

The first new arithmetic test typed A cold total636000 although its addends were
53000+547000+56000=656000. The test failed and the literal was corrected before freeze.
This was an agent arithmetic transcription error, not an A/model discrepancy or measurement.
No executed counterexample was erased or reclassified as a native pass.

## Observation join still required before B execution

Current public runner exposes fixed-delay only. `assert_case` is ready against the installed
job/result carriers; it does not claim a new execution API. Actual component output must
supply all mandatory observations and a reviewed naming contract: resource activity/category,
allocation owner, transfer boundaries, waiting/service/inflight queue identities, rational
channel service and per-domain clock crossings. Freeze that contract independently of result
bytes. The checker currently requires causal service spans to have represented resource
witnesses; if A represents alignment/waits differently, reconcile explicit witnesses before
release, without weakening causal category or receiving-domain assertions.

Prospective native selection demands three debug and three release bytes for every positive
case, then input/result/literal checks. Future real runner/refusal/mutant/transport calls,
producer-disabled native replay and two qualifying relation replays remain required. All
calls and discovery/shrink/control failures need immutable retained input/output and budget
ledgers. The current synthetic checker mutations do not discharge engine mutant obligations.

No protected change is proposed as ready to install: resolving accumulator reuse, four-MXU
TPU representation or unknown numeric fields requires an exact separately reviewed proposal
before dependent work. This interface note identifies gaps and valid alternatives; it grants
no architecture change, fixture acceptance, engine/build release or independent verdict.

## Published final A join at 6d30e36

A's final handoff arrived during B validation and was fast-forwarded through Git. Its
3f54861 full-job operand-access precondition is joined and covered by the affected mapper/
loader tests. Four published A fixtures now have separate independent B input/arithmetic
joins: A-C01 resident702000ps, A-C02 resident547000ps, A-C03 resident1182000ps and
A-C02 cold656000ps. Synthetic author profiles remain explicitly unauthoritative.
Their bytes/hashes and proposal hashes are in peer-join.json; they do not replace B inputs.

A independently identified the same accumulator lifetime gap. Exact unapplied proposals:
[accumulator lifetimes](../U4-A-component-mapper-v1/accumulator-lifetime.proposed.patch) and
[nonclocked queues](../U4-A-component-mapper-v1/nonclocked-queues.proposed.patch).
Both pass read-only `git apply --check` against installed protected source; neither is
applied or accepted here. A's proposed U0011 text is retained in
[protected-gaps.md](../U4-A-component-mapper-v1/protected-gaps.md).

The installed parser still rejects null queue domains for component results. B now has
prospective independent queue checks with an explicit default-off allow_nonclocked_queues
option in the frozen observation contract. Null-domain channel_service/dma_inflight records
must bind the exact declared request/channel/engine/owner and permitted population. Synthetic
positive, wrong-owner, wrong-request and wrong-population tests run; enabling this checker
option cannot bypass the installed parser or provide human acceptance. Genuine first use
requires the reviewed protected change. Rational service must not acquire a fictitious
DRAM-edge alignment just to satisfy current parsing.

A's proposed activity encoding dram_service:<request_id> and dma_port:<request_id>, exact
transfer boundary naming, and tight subphase/request causal links still need freezing.
General string carriers do not prove request/subphase causality. Until that join is complete,
this observer remains a prepared checker with explicit limitations, not qualified attribution.
The valid alternative SRAM relocation in B's test preserves A's HBM routes, matrix/core ports
and counts, so its separate E4 expectation is also656000ps under NoC0/bank-unrepresented laws;
this equality is premise-specific, not required of arbitrary equivalent-work mappings.

## Retained verification setup/correction history

The first sandboxed shell could not start because of the WSLg mount configuration; commands
used the authorized escalated fallback in the explicitly requested B clone. An initial
`uv run --no-sync pytest` created an empty ignored B venv and failed because pytest was not
installed there. No dependency installation followed; existing pinned main-clone packages
were used with actual B module origins recorded. Scoped lint/types found author formatting
and local annotations, corrected before freeze. The initial integrated support-origin failure
was caused by PYTHONPATH being set; its full log remains and the unset-env rerun passes.
The generic checker initially treated all owner intervals as exclusive; before release it
was corrected to preserve overlapping NoC0 latency and DMA inflight intervals. A synthetic
NoC0 union control now passes; only matrix/core-port and rational channel service are checked
for exclusive service. None of these author/setup findings is native model evidence.
