# Two human L1 workings requested

Javid or a designated human: please commit your own derivation, name, date and input revision
to `validation/L1_limits/hand/H-L1-DMA-01.md` and `H-L1-GEMM-01.md`.
Full input-only questions remain [in the preserved worksheet](../U4-B-verification-inputs-v1/human-worksheet-inputs.md).
Do not copy the separate agent answer key or merely approve an agent's calculation.

- **DMA:** one engine,256B read requests, addresses1536+2048*j, channel6/two hops each way;
  core/NoC/DRAM1GHz, router2cycles/hop, DRAM latency48cycles, chip bandwidth10^12B/s,
  eight channels, refresh350/3900, shared core port256B/cycle. Work exact rational service,
  every named-domain edge, credit release at commit, one versus two credits and a valid
  repeated whole-cycle latency-bound window/rate. No compute overhead or final-byte pooling.
- **GEMM:** resident BF16 m16,k256,n256, FP32 accumulator,256×256 WS array,1GHz;
  staging ceil((X+W)/1024), overhead32, wave255+m+255, drain ceil(Y/1024).
  Work useful/issued/MAC counts, SRAM traffic, capacity/reserved slots, every timing term,
  necessary lower bound and smaller3×5×7 control. SRAM X0,W8192,Y139264; slot1 begins147456.

D02's write needs resident SRAM. D14 uses the actual producer chain in
[final reconciliation](../U4-B-final-reconciliation-v1/fixtures.md), not an external835ps
start. These corrections do not change the two worksheet questions' resident/read premises.
Both workings are currently unassigned/unfilled: named skips and applicable L1 blocked.
Independent corpus/checker preparation proceeds. Presence tests alone cannot accept the
working, replace its review or claim an actual native L1 pass. No human signature is invented.
