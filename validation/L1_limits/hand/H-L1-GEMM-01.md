# H-L1-GEMM-01 — approved assisted working

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

Javid personally supplied the first arithmetic: 4,096 output elements; 1,048,576 MACs;
X 8,192 bytes; W 131,072 bytes; Y 8,192 bytes; total input 139,264 bytes. Codex checked it.
At Javid's request, Codex calculated the later steps. Javid explicitly approved the main
702 ns timing, then the work/storage accounting, smaller-case interpretation and clock
scaling in separate replies. These later steps remain assistant-calculated and human-reviewed.

## Premises

Resident BF16 X/W/Y, two bytes per scalar; FP32 accumulator, four bytes per element.
M=16, K=256, N=256; 256 K rows by 256 N columns; core 1 GHz. X and W are initialized
in nonaliasing SRAM and Y is allocated. No HBM transfer occurs. Input staging transfers
1,024 bytes per core cycle; overhead is 32 cycles; wave is 255+M+255 cycles; drain transfers
1,024 bytes per cycle. These phases serialize. No weight retention across jobs is assumed.
Accumulator capacity is 262,144 bytes and SRAM capacity is 16,777,216 bytes.

## Work and storage

- Output elements: 16*256 = 4,096.
- Useful MACs: 16*256*256 = 1,048,576.
- Useful operations (two per MAC): 2,097,152.
- Issued operations under the model's physical K/N extent rule:
  2*16*256*256 = 2,097,152. K/N masking introduces no unused slots for this shape.
- X: 16*256*2 = 8,192 bytes; W: 256*256*2 = 131,072 bytes.
- Y: 16*256*2 = 8,192 bytes.
- SRAM payload reads: 139,264 bytes; writes: 8,192 bytes; total: 147,456 bytes (144 KiB).
- Logical accumulator: 16*256*4 = 16,384 bytes (16 KiB), within its separate 256 KiB capacity.

Slot 0 occupies [0,147456): X [0,8192), W [8192,139264), Y [139264,147456).
Unused slot 1 reserves [147456,294912), another 147,456 bytes. Thus SRAM allocation plus
reservation is 294,912 bytes (288 KiB), within 16 MiB. The unused reservation transfers
no payload and is not counted as traffic. Accumulator storage is a separate modeled space.

## Timing and necessary lower bound

| Phase | Calculation | Core cycles |
| --- | --- | ---: |
| Input staging | ceil(139264/1024) | 136 |
| Overhead | Given | 32 |
| Array wave | 255+16+255 | 526 |
| Output drain | ceil(8192/1024) | 8 |
| Total | 136+32+526+8 | 702 |

At 1 GHz, a core cycle is 1 ns = 1,000 ps. Duration is 702 ns = 702,000 ps.
The useful-work lower bound is 1,048,576/65,536 = 16 cycles = 16 ns. It omits staging,
fixed overhead, wave propagation and drain; it is a necessary bound, not the model's duration.
Pipeline propagation does not itself add useful arithmetic operations.

## Smaller M=3, K=5, N=7 control

Use separately aligned valid buffers. Alignment/reservations do not create payload traffic.

| Quantity | Calculation | Result |
| --- | --- | ---: |
| Output elements | 3*7 | 21 |
| Useful MACs | 3*5*7 | 105 |
| Useful operations | 2*105 | 210 |
| Issued operations | 2*3*256*256 | 393,216 |
| X bytes | 3*5*2 | 30 |
| W bytes | 5*7*2 | 70 |
| Y bytes | 3*7*2 | 42 |
| Accumulator bytes | 3*7*4 | 84 |

SRAM reads are 100 bytes and writes are 42 bytes. Unused K/N lanes are masked; no padded
zero matrices are loaded from memory. Issued operations count assigned full-array slots,
not useful mathematical work or a claim about physical switching activity.
Timing: ceil(100/1024)+32+(255+3+255)+ceil(42/1024) = 1+32+513+1 = 547 cycles,
or 547 ns = 547,000 ps. Duration comes from these phase laws, not issued operations divided
by peak throughput. Small useful work does not eliminate the array's propagation delay.

## Clock scaling

At 2 GHz the cycle is 0.5 ns. All four terms are core-cycle-valued, so unchanged cycle
counts give exactly 351 ns for the large case and 273.5 ns for the small case. Counts,
traffic and storage stay unchanged. This does not generalize to mixed queries: other clock
domains, byte-per-second bandwidth, dependencies, resource/credit waits and edge alignment
can scale differently or remain fixed. These are consequences of the worksheet's simulation
premises, not silicon measurements.
