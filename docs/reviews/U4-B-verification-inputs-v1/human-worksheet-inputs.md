# Human L1 worksheets — INPUTS ONLY

Prepared by the Lane B agent for Javid or a designated human; **assignee unassigned**.
No human working/approval exists. Both worksheets currently skip with their IDs.
Do not copy the separate agent answer key as human work. Record the human author's name,
date, input revision, full working and interpretation in their eventual hand artifact.
Accepted model laws are simulation premises, not measured chip properties.

## H-L1-DMA-01 — latency-bound one-credit read stream

One engine, one outstanding request, 256 payload and transaction bytes per read;
all addresses1536+2048*j bytes map to channel6, controller3, two XY hops each way.
All three domains1,000,000,000Hz; router2 cycles/hop; DRAM tRP/tRCD/tCL each16 cycles;
8 channels; chip bandwidth1,000,000,000,000 bytes/s; refresh tRFC350/tREFI3900 cycles.
Channel bandwidth is chip bandwidth*(1−tRFC/tREFI)/8. Bandwidth service is rational
picoseconds with ceil only when publishing completion; cycle phases use next_edge.
Read issue consumes no core-port cycle. SRAM commit uses the shared256-byte/core-cycle
port. Credit release is at SRAM commit; no generic compute overhead. Each next request
is ready immediately on release, no other traffic; buffers fit and never alias.

Questions for the human:

1. Derive channel rate, exact request service and each named-domain timestamp for the
   first request, including outgoing hops, DRAM latency, return alignment and commit.
2. Work the second request with one credit. Compare two credits and explain precisely
   where overlap is permitted. What observation detects a credit released at memory finish?
3. Derive the one-credit steady payload rate and identify the limiting term against
   channel capacity. State bytes/s and ps, showing unit conversion. Explain startup/drain
   and a window that contains whole cycles of the proposed repeating stream.
4. State why this cannot be a physical DRAM queue or silicon-accuracy claim. Explain
   why a cap32 short burst is not by itself a saturated-channel limit test.

Status: unfilled / SKIP H-L1-DMA-01. Intended checkpoint B applicable U-P8 L1.

## H-L1-GEMM-01 — resident weight-stationary tile

One q_projection, m16,k256,n256; X/W/Y BF16 (2 bytes/scalar), accumulator FP32
(4 bytes/scalar); array256 K rows×256 N columns; core1,000,000,000Hz.
X/W initially resident in nonaliasing initialized SRAM, Y allocated; no HBM transfers.
Operand staging combines X+W and costs ceil(bytes/1024) core cycles; overhead32 cycles;
wave255+m+255 cycles; output drain ceil(Y_bytes/1024) cycles. These phases serialize
on the matrix owner; no weight retention across jobs. Accumulator262144B, SRAM16777216B.
Slot0 X offset0,W8192,Y139264; unused slot1 reservation begins147456, size147456 bytes.

Questions for the human:

1. Derive MACs, useful versus issued matrix operations, SRAM reads/writes and accumulator
   footprint. Distinguish a reserved slot from transferred bytes.
2. Derive each timing term and total ps. Compute a necessary useful-work lower bound
   from65536 MACs/core cycle and explain why it is smaller than the modeled interval.
3. Repeat the arithmetic for m3,k5,n7 with separately aligned valid buffers. Explain
   masked lanes, useful work and why traffic does not include padded zeros.
4. If core doubles and every cycle-valued compute term scales, does this resident case
   halve exactly? Explain why the same statement is not a general mixed-query law.

Status: unfilled / SKIP H-L1-GEMM-01. Intended checkpoint B applicable U-P8 L1.
