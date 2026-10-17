# Independent Stage 2 workings

These are finite synthetic unit carriers and prospective arithmetic, never generated native
results. Historical [workings](../U4-B-component-joins-v2/observation-workings.md), 99 cells,
13 input files and all old evidence retain their bytes. No expectation is tuned to a forgery.

| Witness | Independent law and literal result |
| --- | --- |
| Resident C02 | 32 + ceil(100/1024) + (510+3) + ceil(42/1024) = 547 core cycles = 547000 ps. Useful 210, issued 393216, SRAM 100/42 B, accumulator 84 B. |
| D01 | Channel starts 52000; exact duration 159744/71 ps; end 3851744/71, published 54250. Response receives at 55000, ends 59000; 256 B port needs one cycle, completes 60000. M4b's 54500 is wrong even when its following alignment absorbs the error. |
| D10 read | Core/NoC/DRAM 0.8/1.2/0.9 GHz. Request 3334; DRAM receiving edge also 3334; latency ends 56667; exact channel end 4183101/71, published 58917; receiving NoC edge 59167; response 62500; port completes 63750. A claimed edge at 59000 is between valid receiving edges. |
| D08 | Both responses ready 59000. FIFO is r00 [59000,60000), r01 [60000,61000). Reversal keeps 61000 but is wrong. Nonoccupying ports overlapping [59000,60000) each are also wrong. Waiting is [59000,60000), not an occupied interval. |
| D05-two | Both channel requests ready 52000; second starts exact 3851744/71, ends 4011488/71 → 56500. Responses finish 59000/61000; ports complete 60000/62000. A fractionally early start with identical rounded endpoints still fails exact carry. |
| D05-one | Capacity one holds the first credit to port completion 60000. Second issues 60000, channel starts 112000, ends 8111744/71 → 114250; final commit 120000. The same delayed issue under capacity two has no exhausted-credit cause, even though its first/last endpoints are structurally eligible. |
| D14 | NoC is 1.2 GHz: request 3334, DRAM edge 4000, channel end 54250, response 58334. Core receives at 59000; ports commit 60000/61000. Dependent same-core unicast is ready/start/end 61000, no extra NoC edge or occupancy. |
| D13 barrier | Two same-channel reads commit 60000/62000. Only the terminal at 62000 is tight; 32 NoC cycles produce 94000. The earlier completion is a dependency, but not a tight cause at grant. |
| Historical C04 | Old capacity refusal and arithmetic-only 1855000 ps remain. Valid @2 representation: 262144 B live [0,1182000), 1024 B live [1182000,1855000), same offset, exact work/traffic unchanged. |
| New writer control | Two disjoint 84 B accumulators at offsets 0 and 256; two 547000 ps computes. Changing zacc's producer to c reaches the writer guard without alias or capacity masking. |
| New A1 control | Four uniform 256³ computes c,d,e,z: 4×1182000=4728000 ps. acc is live through BOTH d/e; zacc reuse must follow both. Naming only d as terminal while e is unordered with reuse is invalid. |
| New A3b/A3c | Two equal 262144 B users share acc. z before producer c, or z unordered with c, is invalid independently of footprint/capacity. Ordered c→z with terminal z is valid, 2364000 ps. |

The complete cause set is derived before choosing a critical path. Expanded sequence links
include zero-duration receiving alignments. At first activities, include tight terminal
completions of declared dependencies. Resource links occur only at acquisition: first
compute alignment (whole tile), port alignment or channel service, from the actual previous
other tile/request; a tied dependency/sequence cause is retained too. Credit causes require
actual capacity exhaustion before a delayed issue and a same-engine terminal release at
that issue. Equality of timestamps alone supplies no cause. The supplied set must equal
this complete eligible set, including off-chain activities.

The canonical critical path chooses the declared stable owner/job/request/phase/activity
order among tight eligible predecessors, retaining zero links but emitting only positive
intervals. It must cover the makespan and match categories, owners, and attribution totals.
NoC occupied rows describe overlapping router-attributed latency bookkeeping. They do not
serialize independent hops or DMA inflight. DRAM latency and receiving alignment remain
nonoccupying; channel service owns its exact rational interval.

The full declared activity/request inventory drives mechanism laws. Only afterward are
occupancy flags, mandatory rows, clocks and populations joined. Null-clock channel queues
and DMA inflight bind their exact channel/flattened-engine owner and request; ordinary
queues bind activity, owner, receiving domain and waiting/service interval. Transfer windows
start at the first phase's readiness, not a forged later service readiness. Job release is
zero, readiness is the maximum declared dependency completion, and endpoints summarize actual
first/last activities. Legacy scalar blocker/predecessor fields are explicitly empty/null
under /2; /1 is untouched.
