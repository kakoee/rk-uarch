# H-L1-DMA-01 — approved assisted working

Human reviewer: Javid. Review date: 2026-10-22.
Calculation assistance: Codex, in the coordinator conversation.
Inputs: [original input-only worksheet](../../../docs/reviews/U4-B-verification-inputs-v1/human-worksheet-inputs.md),
last changed at `698c8cdb01d2296a254964ad50c7b6e22bec6660`.

Status: accepted by Javid as human-validated L1 working, with disclosed AI assistance.
After approving every step, Javid clarified: “Human review was beyond just a review.
It validated them too. Used AI as assistant.” This explicit decision accepts this method
for these two worksheets and supersedes their earlier assisted-only pending status.
The calculation attribution below is preserved; no unaided human derivation is claimed.
No native simulation or physical measurement was executed for this record. Document
presence alone is not a native L1 verification result, and no U4 closure is claimed.

## Attribution and approval

Codex calculated each step and Javid approved each in sequence: channel rate/service,
first-read timeline, second-read/two-credit comparison, and sustained throughput/limitations.
These are assistant-calculated and human-reviewed results; no unaided human derivation is claimed.

## Premises

One engine, initially one credit, 256 payload/transaction bytes per read. Addresses
1536+2048*j map to channel 6/controller 3, two XY hops each way. Core, NoC and DRAM are
all 1 GHz; each hop costs two NoC cycles. DRAM tRP/tRCD/tCL are 16 cycles each. Chip
bandwidth is 10^12 bytes/s across eight channels, refresh tRFC/tREFI=350/3900.
Read issue consumes no core-port cycle. SRAM commit uses 256 bytes per core cycle.
Credit releases only at completed SRAM commit. Buffers fit, never alias and other traffic
is absent. The next queued request has no extra preparation delay. All resources are free
at time zero. Cycle phases align to the first edge at or after readiness.

## Channel rate and exact service

Available fraction: 1-350/3900 = 71/78.
Channel rate: 10^12*(71/78)/8 = 71*10^12/624 bytes/s
= approximately 113,782,051,282.051 bytes/s (113.782 GB/s, decimal).
A 256-byte service takes 256/(71*10^12/624) seconds
= 159744/71 ps = approximately 2,249.915493 ps = 2.249915493 ns.
Keep the rational value internally. Round only published completion to integer ps and
apply clock alignment separately; do not round every internal service term.

## One credit: first and second reads

| Phase | Request 1 (ns) | Request 2 (ns) |
| --- | --- | --- |
| Issue | 0 | 60 |
| Outgoing network: two 2-cycle hops | 0 to 4 | 60 to 64 |
| DRAM latency: 16+16+16 cycles | 4 to 52 | 64 to 112 |
| Channel service | 52 to 54.249915... | 112 to 114.249915... |
| Published channel finish (ps) | 54,250 | 114,250 |
| Aligned return start | 55 | 115 |
| Return network: two 2-cycle hops | 55 to 59 | 115 to 119 |
| SRAM commit: one cycle | 59 to 60 | 119 to 120 |
| Completion and credit release | 60 | 120 |

The first read finishes at 60,000 ps. The second cannot issue before that credit release,
and finishes at 120,000 ps. There is no extra issue-port cycle or generic compute overhead.
Arrival at 59 ns is already a core edge, so commit needs no extra alignment cycle.

## Two credits: overlap and shared resources

For this comparison both reads are queued at time zero. They can both acquire a credit
and issue at zero. NoC0 models travel latency without network contention, so their
network intervals overlap. Channel service and the SRAM port are contended resources.

| Phase | Request 1 (ns) | Request 2 (ns) |
| --- | --- | --- |
| Issue | 0 | 0 |
| Outgoing network | 0 to 4 | 0 to 4 |
| DRAM latency | 4 to 52 | 4 to 52 |
| Channel service | 52 to 54.249915... | 54.249915... to 56.499830... |
| Return network after alignment | 55 to 59 | 57 to 61 |
| SRAM commit | 59 to 60 | 61 to 62 |

The latency intervals overlap because the fixed DRAM latency phase does not occupy the
bandwidth-service owner. Contended service phases remain serialized. Completions are 60
and 62 ns; this two-request example does not assert a sustained two-credit rate.
**Correction approved on 2026-10-22:** the earlier assisted answer was 60/64 ns,
incorrectly serializing the NoC0 route. After the coordinator explained the error, Javid
answered: “Approve the corrected 60/62 ns result”. This replaces only that two-credit
comparison; GEMM and one-credit calculations are unchanged. The second exact channel
finish is 52,000 + 2*(159744/71) ps; its rounded observation is 56,500 ps.

To detect premature credit release, inspect the second issue with one credit: any issue
before the first SRAM commit at 60 ns violates the rule, even if a later resource blocks it.
Channel finish at about 54.25 ns is not credit release.

## Steady payload rate and finite windows

One-credit period is 60 ns = 60,000 ps = 60*10^-9 s.
Payload rate = 256/(60*10^-9) = 12,800,000,000/3 bytes/s
= approximately 4.267 GB/s. This is about 3.75% of channel capacity; the single-credit
end-to-end latency, not peak channel service, limits this stream.

A window from first issue at zero through tenth completion at 600 ns contains ten complete
cycles and 2,560 bytes. Rate is 2,560/(600*10^-9), the same value. Counting completions
between the first completion at 60 ns and tenth at 600 ns gives nine additional payloads,
not ten: 2,304 bytes over 540 ns. Counting ten in that shorter interval would overstate rate.

A finite stream must count the initial wait and final drain consistently. One credit
prevents inter-request overlap; a multi-credit burst also fills and drains a pipeline.
A short cap32 burst alone does not establish steady channel saturation. Sustained demand,
a suitable whole-cycle observation window and confirmation of the active bottleneck are
needed; SRAM service or another modeled contended resource can limit throughput even when more
credits are available. No network contention is modeled by this NoC0 example.

## Interpretation

These fixed-latency, refresh-derated service laws do not model all physical DRAM bank,
row-buffer or controller-scheduling effects. Agreement verifies the chosen premises;
it establishes neither a physical DRAM queue model nor silicon accuracy.
