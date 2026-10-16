# Stop the sequential campaign; parallelize the test harness

Javid requested stopping the run and making it faster, either by reducing execution
count or using the available cores. The coordinator stopped only the owned campaign
container. **88 calls completed all checks; 89 transport receipts exist.** Exit 137
is the requested stop, not a semantic failure. Elapsed wall time was 1,382.7 seconds.
There is no complete campaign receipt, replay was not run, and no qualification follows.
All completed stream hashes and all 5,325 sealed deployment entries were rechecked;
the deployed inputs/authority remain unchanged. See [stopped-run.json](stopped-run.json).
Bulk partial evidence remains private at `/tmp/u4-k2-approved-campaign`.

## Measured cause and available improvement

The saved requests total 281,479,193 bytes across 133 cases. The production resolver
validates every request independently for each build mode. During each public call,
`run_fixed_delay`/`encode_request`/`parse_response` admit the request three times; the
harness additionally reparses it for its independent result checker. This is visible
in source, and the Python-only diagnostic reproduces those operations on genuine
saved requests/results without resolving authority or launching the engine.

The profile of one sample made 42,187,056 function calls (including recursive calls),
including 2,014 hardware coherence validations and 3,381,506 regex fullmatch calls.
`hardware_unit_rule` constructs and matches rule expressions repeatedly. The
profiled 15.4-second duration includes profiler overhead and is not a clean timing
measurement. See [profile.txt](profile.txt).

Separate unprofiled batches used the same four genuine saved cases repeated four
times, for 16 Python checks per configuration. All revalidated requests/results
matched their original bytes and independent expectations:

| Worker processes | Checks | Wall seconds | Relative throughput |
| --- | ---: | ---: | ---: |
| 1 | 16 | 124.37 | 1.00× |
| 8 | 16 | 20.67 | 6.02× |
| 16 | 16 | 16.55 | 7.51× |

The container exposes 16 affinity CPUs and no cgroup CPU quota. Largest worker RSS
in these batches was approximately 139 MiB. This does not measure full-campaign
peak memory. Each configuration was measured once on local WSL2; these are diagnostic
observations, not stable engine-performance qualification or a promise of the same
speedup for startup, native execution or the entire campaign. The serial admission
and checker reparse stages consumed about 121 of 124 seconds. Native execution was
blocked, and no new native job ran. [diagnostic.json](diagnostic.json),
[comparison.json](comparison.json) and [diagnostic-launch.json](diagnostic-launch.json)
record actual results and the command. The existing accepted image and mounted
runtime were used read-only, offline, without capabilities or security changes.

## Recommended next action

Use **process parallelism across independent test cases**, initially retaining all
133 cases, both modes and all three repetitions. This preserves the existing coverage
and deterministic byte comparisons while addressing the measured bottleneck. It does
not multithread the simulator. Do not assume 16× speedup just because 16 CPUs exist.

The 798 count comes from a chosen repetition policy, not 798 distinct behaviors.
Reducing repetitions is possible as a separate explicit coverage decision, but the
measured 7.5× improvement makes dropping cases unnecessary as the first response.
The hardware-rule/repeated-validation hotspot is a second optimization opportunity;
it must not be addressed by blindly trusting mutable caller objects or skipping
checks. Contract changes would require the normal protected-source handling.

[Give the existing B session this consolidated task](lane-B-prompt.md). It covers
parallel scheduling, actual CPU/memory limits, genuine host resolution, atomic
receipts, deterministic final assembly, failure cleanup, bounded discriminating
checks and the minimal revised deployment binding. It avoids another series of
single-issue handoffs. The original runtime remains sealed. No full campaign restart,
new native execution, protected edit or authority installation is performed by this
package; the revised harness must be checked and placed before restarting.

## Complementary Lane A work

[The A task](lane-A-prompt.md) investigates and implements a private, tested candidate
for per-call admission reuse and separately evaluates the hardware-rule hotspot.
B continues harness parallelism against its unchanged source pin. A publishes an
unapplied candidate so production/support/authority identities do not change under
B's active work. The coordinator reconciles both complete handoffs once, including
any protected-source and deployment implications; neither task restarts the campaign.

Javid subsequently asked to share setup across repeats of one case. The
[shared A/B addendum](shared-case-reuse-addendum.md) explicitly extends A's original
per-call reuse proposal to a bounded case-scoped interface and assigns B case-group
scheduling. It retains six fresh executions and complete per-output validation;
grouping by itself does not authorize skipping admission or reusing results.
