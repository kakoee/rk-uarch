# U4 B — make the first-use campaign practical with parallel case execution

Continue the existing B session and pull published main normally. Javid stopped the
sequential first-use run and requested a faster approach, including use of available
CPU cores. Read this package's README, stopped-run.json, diagnostic.json/profile.txt
when published, and the original approved deployment package at
f2b270aa55204a6bf43ff8d3b7fdeb902db30c0f.

Deliver one consolidated, tested replacement harness and exact deployment delta.
Work independently through routine corrections and affected tests. Do not bounce
individual implementation details back through the coordinator. Do not restart the
full public campaign during preparation.

## Preserve the meaning of the check

The current run stopped at Javid's request: 88 fully checked calls and 89 transport
receipts, not a pass. Preserve all original evidence at
/tmp/u4-k2-approved-campaign. The accepted source is
24fa36803081e5077d5977baa91441a2c8534ec8; candidate-04 binaries, dependencies,
133-case inventory, authority subject, expected refusals and production validators
remain unchanged. Do not rebuild the engine, regenerate inputs, relax a validator
or claim that local throughput is performance qualification.

For the initial replacement retain all 798 slots (133 cases, both modes, three fresh
native processes per case/mode). Parallelize independent cases, not the simulator's
internal scheduling. If you recommend reducing repetition, separate that proposal
and its coverage rationale from the initial implementation; do not silently reduce
case membership or claim three repetitions are a statistical confidence estimate.

## Implementation and bounded verification

Use worker processes for Python CPU work. Select the effective available CPUs using
affinity and container CPU quota, and account for memory. The observed host exposes
16 logical CPUs; do not hardcode that as universal or oversubscribe a quota. Record
actual worker count and resource assumptions. Compare 1-worker and parallel execution
on a small fixed workload before claiming a speedup.

Initialize and verify immutable runtime inputs once before worker startup. Keep the
real production resolver as the authority source; do not manufacture AcceptedHostBinding
objects, bypass __post_init__, substitute the private resolver or turn a cached caller
object into authority. Forking already verified parent state is a possible approach,
provided no active threads or executable descriptors are inherited unsafely and each
native launch retains the existing exact-file descriptor verification. Explain the
actual process and ownership model in the handoff.

Every call must still use the production runner and the independent result checker.
Maintain fresh native subprocesses, per-call private working directories, canonical
framing, exact executable hashes and timeout/output caps. Do not replace the public
call with direct binary invocation just to obtain faster numbers.

Make receipt writing concurrency-safe: unique slot receipts, atomic hash-addressed
blob publication, exact membership/multiplicity, deterministic final ordering, and
six-way byte comparison after collection. No completed campaign receipt before every
required slot is verified. Worker exceptions, hangs, missing/duplicate slots, blob
collisions with different bytes, result drift and output-budget violations must fail
closed and preserve partial evidence. Clean up only the run's own workers/native
processes/container. Retain full before/after sealed-input checks and the saved-result
replay/corruption/restoration obligations.

Use prior actual saved outputs as correctness controls, not invented native successes.
Test worker scheduling, atomic receipts, deterministic assembly and failure propagation
without native execution where possible. Include tests that fail if each essential
parallel guard is removed. Keep the unit/host selections bounded; no unrelated full
suite or repeated construction/fault campaign is needed when its source is unchanged.

The profiling hotspot in contract/uarch_contract/hardware.py is a separate possible
optimization. Do not modify protected carriers or bypass repeated validation in this
harness task. A narrowly equivalent validation optimization would need its own exact
patch, tests and normal protected-source handling; it is not required to parallelize.

## Deployment and handoff

The original sealed deployment and published approval remain immutable. Prepare an
exact new helper manifest/runtime-release binding and minimal human placement sequence
for the replacement harness, reusing verified runtime/binary bytes where safe. Reuse
the genuine engine approval; do not invent a new human decision or install root-owned
files yourself. Name any actual additional authority requirement precisely. Do not
request another engine/dependency/licence decision for unchanged inputs.

Publish owned preparation work with normal hooks/main integration. Return one handoff
with the exact delta, bounded executed checks, serial/parallel diagnostic results,
worker/failure behavior, deployment postimages, and a concrete command sequence. The
coordinator will review and arrange the necessary human placement before restarting
the full campaign. No CI polling, remote infrastructure work or K2/U4 closure claim.
