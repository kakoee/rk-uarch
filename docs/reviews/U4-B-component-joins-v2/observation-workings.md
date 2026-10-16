# Independent finite phase workings (proposal, no result)

These are scalar worksheets and identity requirements, not generated observations or native
receipts. B's binary edge search/Fraction arithmetic is independent of production timing.
Final carrier names must join the exact A /2 patch. All times below are ps, half-open.

* Resident C02: overhead[0,32000), X+W staging[32000,33000), WS wave[33000,546000),
  output drain[546000,547000). Matrix0 occupied over their union; overhead32000,
  compute515000. Useful210, issued393216, SRAM100/42B, accumulator84B.
* Resident C01: overhead0..32000, staging32000..168000, wave168000..694000,
  drain694000..702000. Useful2097152; SRAM139264/8192B; accumulator16384B.
* Cold A C05: X/W requests on channels0/1 have zero-hop outbound/return; latency0..48000,
  exact service48000..(48000+159744/71), publication50250. Port eligibility50250,
  first grant aligned51000, commits52000/53000. W is the tight compute predecessor.
  Compute53000..600000 (overhead32000, compute515000). Write payload port600000..601000,
  one-hop outbound601000..603000, latency603000..651000, exact channel end
  651000+159744/71 (publication653250), return aligned654000..656000, core ack656000.
  Critical totals compute515000/overhead32000/memory104250/noc4750 =656000.
* D01 remote read: outbound0..4000; DRAM latency4000..52000; rational service
  [52000,3851744/71), published54250; return alignment54250..55000 then hops55000..59000;
  port59000..60000. memory51250/noc8750. Channel occupied only rational service;
  the latency and alignments do not invent channel busy time.
* D10 remote read: clocks core800MHz/noc1200MHz/dram900MHz. Outbound0..3334;
  DRAM receiving alignment3334..4445, latency4445..56667; service56667..4183101/71,
  publication58917; return alignment58917..59167 then four NoC cycles..62500;
  core port62500..63750. memory56833/noc6917. A correct makespan with DRAM alignment
  relabelled NoC must fail. Each clock witness must identify this request and subphase.
* D08 port contention: both channel6/7 responses59000. r00 port59000..60000,
  r01 waits59000..60000 then occupies60000..61000. r01's port activity is tightly
  blocked by r00's port completion, not r00's whole DMA lifetime. Critical chain may
  traverse that resource predecessor; no busy interval is added for the wait.
* C09 overlap: matrix0[0,547000), independent DMA r00[0,60000). Makespan547000,
  matrix critical path unchanged; NoC0 latency and DMA inflight overlap legally.
  A global resource serialization to607000 fails.
* D14: b port60000..61000, zero-hop dependent c ready/start/end61000. c retains a
  zero-duration activity and dependency witness, no positive resource/critical interval,
  no extra NoC edge to61667. Terminal tie must follow the declared stable rule.

A rational service finish is used unrounded by the next channel request. D04 request12
ends5608928/71 →78999; rounding each prior finish gives79000 and must fail. Finite queue
areas use published integer membership endpoints, while channel exclusivity uses exact
ratios; these are distinct units/projections, not a contradictory channel clock.

Allocation identity binds buffer→space/core/channel owner→offset/size→producer and all
terminal consumers. C04 @2: acc[0,262144) live0..1182000; zacc[0,1024) live1182000..1855000.
Same address reuse is legal only after all final consumers. Distinct cores may overlap.
The historical C04 carrier retains separate persistent offsets and CapacityExceeded.

For every activity, bind declared job/request and exact typed mechanism; receiving clock
alignment is unoccupied. Resource rows are only occupied activities, queues bind exact
request/activity populations, transfers bind declared direction and fragment payload/256B
transaction. Critical intervals need a tight activity chain and mechanism/category match;
partition sums alone are insufficient. Runtime must emit actual dispatched/completed state,
with no reconstruction from these expected worksheets.
