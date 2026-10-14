# Agent-derived answer key — not human working

Author: Lane B agent; independently derived from accepted model premises. These values
are proposal inputs only and do not satisfy either human worksheet.

H-L1-DMA-01: refresh fraction71/78; channel4437500000000/39 bytes/s;
service159744/71ps. First read: issue0, arrival4000, latency end52000,
exact service end3851744/71ps, published54250, NoC return59000, SRAM commit60000.
One credit makes second issue60000 and completion120000; two credits allow issue0/0
and completions60000/62000. One-credit repeating rate256*10^12/60000 =
12800000000/3 bytes/s, below channel capacity. A finite window [0,N*60000) with initial
inventory before t0 includes N issues but only N−1 completions; terminal request remains
inflight at the excluded end event. Do not divide that censored completion count by the
window and call it the asymptotic rate without the boundary term. Credit release before
commit violates recorded acquire/release/population independently of a masked duration.

H-L1-GEMM-01: MACs1048576, useful/issued2097152 ops; X8192,W131072,Y8192 bytes;
accumulator16384B; SRAM reservation294912B including slot1. Staging136,overhead32,
wave526,drain8 cycles,total702 cycles=702000ps. Necessary useful-work bound16 cycles=
16000ps. At2GHz total351000ps. Small m3,k5,n7:105 MACs,210 useful,393216 issued ops;
X30,W70,Y42 bytes;84B accumulator; stage1+overhead32+wave513+drain1=547 cycles.
At2GHz273500ps. No resident HBM payload/transaction bytes. These are model laws, not
validated array behavior and not a whole-model U-C0 API.
