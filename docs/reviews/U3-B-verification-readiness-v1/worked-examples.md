# Independently worked candidate checks

B authored these calculations from accepted mathematics, without production count,
rate, timing or preparation helpers. They are synthetic test designs, not hardware facts
or executed engine evidence. They do **not** fulfill U-P8's requirement that a human work
at least two committed hand fixtures (including a latency-bound stream). A human must
supply/review that working separately; do not label these agent calculations human work.

## Analytic v1: accounting, bound changes and mode order

A BF16 projection with M=2, K=3, N=4 performs 2*3*4=24 MACs, hence **48 matrix ops**.
X has 6 scalars (12 bytes); W has 12 (24 bytes); Y has 8 (16 bytes).
Reads=36, writes=16, total traffic=52 bytes. At 12 matrix ops/ns and 4 bytes/ns,
compute demand=4 ns and memory demand=13 ns: isolated duration=max(4,13)=13 ns.
Double bandwidth: max(4,6.5)=6.5 ns. Double only compute clock: max(2,13)=13 ns.
This is an isolated algebraic operator example; a future test must construct a legal,
authenticated public input rather than bypass full-model admission and call it admitted.
Faults: count MAC as one op; omit output writes; read bandwidth from compute rate;
scale DRAM with core. Require the intended arithmetic assertion, not a setup exception.

For two unchanged operators with compute demands (8,0) ns and memory demands (2,6) ns:
aggregate=max(8,8)=8 ns; per_op=max(8,2)+max(0,6)=14 ns. Doubling the compute clock
gives aggregate=max(4,8)=8 ns and per_op=4+6=10 ns, **not** 7 ns. The second operator
is memory-only; this is a concrete counterexample to unconditional per_op reciprocal
clock scaling. It also distinguishes `sum(max)` from `max(sum)` and clock changes from
bandwidth changes. These demands describe the roofline algebra, not a new imported graph.

## RoPE v2: new partial-tail and repeat example

One rank, B=2, S=2 (prefill), local Hq=3, Hkv=1, D=6, R=4, three decoder layers,
BF16 X/Y/KV, explicit precomputed FP32 coefficients with 17 rows. Assume these resolved
shapes are admitted, no extra rotary padding, no reuse across Q/K/layers, and group.repeat
applied once. M=B*S=4. Q rotates 4*3*4=48 scalars; K rotates 4*1*4=16.
Each scalar costs 3 arithmetic ops + 2 casts: Q=240 and K=80 vectors/layer.
Across three layers: **Q=720, K=240; vector total=960; matrix delta=0**.

All D coordinates transfer, including the two unrotated tail coordinates:
Q activation read/write each=2*4*3*6=144 bytes; K each=2*4*1*6=48.
Each node reads cos+sin once/token, shared across its heads: 4*M*R=64 bytes.
Q reads=208, K reads=112; together **reads=960 and writes=576 bytes** over three
layers. Coefficient allocation=8*17*(4/2)=**272 bytes**, once shared across Q/K/layers,
not 272*6. Known storage is not total activation peak. Parameters do not increase.

Change only R to 2: vector total=480, reads=768, writes=576, coefficient allocation=136.
Tail transfers stay fixed. Change only format to FP32 with R=4: casts disappear,
vectors=576, reads=1,536, writes=1,152, allocation=272. Pairing and finite coefficient
values change authenticated inputs but not these abstract counts; identity coefficients
must not remove work. Causal versus full-square attention leaves this RoPE delta unchanged.

Proposed discriminators at the future public v2 verification boundary: omitted casts
predict 576 instead of 960; rereading coefficients per head predicts 1,344 rather than
960 read bytes; dropped tail transfers predict 384 rather than 576 writes; multiplying
repeat twice predicts 2,880 vector ops. Replacing Hkv=1 by Hq=3 gives K=720 instead of
240 vectors. Use fully joined inputs and matched controls so hash/admission failures
cannot masquerade as these arithmetic kills. Separately test refusal faults (stale table,
wrong position/dependency/version), which legitimately fail admission.

For decode B=2, S=1 at C=17 or C=33, this same local geometry yields 480 vectors,
480 read bytes and 288 writes across three layers. Only new K is rotated, not C keys;
positions are [16] or [32] per sequence. Sufficient explicit table rows are required;
coefficient allocation changes with table size, and attention/KV traffic can change.
Do not demand whole-query count/duration equality or reuse an undersized 17-row table.

## Future native: conditional literal expectations

These are mechanism expectations pending A's declared stage assumptions and approved
mapped boundary, not native schemas or runnable cases.

- **Edges:** at 1.2 GHz, ceil(k*10^12/1.2e9) yields k=0..4 at
  0, 834, 1,667, 2,500, 3,334 ps. next_edge(834,0)=834;
  next_edge(835,0)=1,667; next_edge(835,2)=3,334. At 10^9 cycles the edge is
  833,333,333,334 ps. Rounding the period to 833 accumulates error; an extra cycle
  or a floored edge must fail a literal assertion. Native integer range/overflow and
  clock-domain conversion tests require A's boundary decision, not float epsilons.
- **Dependencies/overlap:** ready at t=0, A lasts 3 ns, B lasts 5 ns, C depends on
  both and lasts 2 ns. With independent A/B resources, finish=max(3,5)+2=7 ns.
  On one exclusive resource, A+B+C=10 ns. Missing B→C can finish at 5 ns;
  accidental serialization gives 10 instead of 7. Require actual admitted resource
  and completion observations before credit; analytic per-op rows are not event traces.
- **Transfer:** with precisely two forwarding delays of 3 ns, 64-byte payload and
  16 bytes/ns serialization, no contention and serialization charged once, finish=10 ns.
  Store-and-forward or head/tail semantics may differ; A must select the model first.
  An extra hop delay gives 13 ns; router latency set to 1 ns gives 6 ns.
- **Latency-bound DMA:** fixed round trip 8 ns, 64-byte requests, at most two in flight,
  peak 64 bytes/ns gives min(64,2*64/8)=16 bytes/ns. One outstanding gives 8.
  For a finite empty-start experiment of eight independent requests with completions
  exactly 8 ns after issue and immediate slot reuse, two-wide takes 32 ns (512/32=16),
  one-wide 64 ns. No contention/extra injection delay; otherwise derive that model's
  bound, not this duration. Ignoring the limit or dropping a request must fail. Separately,
  a 100-byte/ns stream with t_rfc/t_refi=1/10 has a 90-byte/ns refresh limit;
  a level-0 peak-only model lacking refresh cannot be credited with that check.
- **Queue window:** jobs arrive at 0 and 2 ns, depart at 4 and 6. Over [0,8),
  occupancy area=2*1+2*2+2*1=8 job-ns; L=1, lambda=2/8, W=4, lambda*W=1.
  Over [1,5), area=1+4+1=6, L=1.5; counting one departure and its full residence
  gives lambda*W=1, a false mismatch. Use clipped residence intersections for every
  job overlapping a finite window, or justified steady-state estimates with boundary
  handling. Never silently drop boundary jobs; zero-flow mean residence is unavailable.

## Arithmetic cross-check

Executed via `uv run --no-sync python -` with this exact stdin. These assertions check
only the written arithmetic; they execute no proposed property test or simulator.

```python
from fractions import Fraction as F

assert (2 * 2 * 3 * 4, 2 * (2 * 3 + 3 * 4), 2 * 2 * 4) == (48, 36, 16)
assert max(F(48, 12), F(52, 4)) == 13
assert max(F(48, 12), F(52, 8)) == F(13, 2)
assert max(F(48, 24), F(52, 4)) == 13
assert (max(8, 8), max(8, 2) + max(0, 6)) == (8, 14)
assert (max(4, 8), max(4, 2) + max(0, 6)) == (8, 10)
assert (3 * 5 * 4 * 3 * 4, 3 * 5 * 4 * 1 * 4) == (720, 240)
assert (3 * (2 * 4 * 4 * 6 + 8 * 4 * 4), 3 * 2 * 4 * 4 * 6) == (960, 576)
assert 8 * 17 * (4 // 2) == 272
assert (3 * 5 * 4 * 4 * 2, 3 * (192 + 8 * 4 * 2), 8 * 17) == (480, 768, 136)
assert (3 * 3 * 4 * 4 * 4, 3 * (4 * 4 * 4 * 6 + 128), 3 * 4 * 4 * 4 * 6) == (576, 1536, 1152)
assert (3 * (192 + 64 * 4), 3 * 2 * 4 * 4 * 4, 960 * 3) == (1344, 384, 2880)
assert (3 * 5 * 2 * 4 * 4, 3 * (2 * 2 * 4 * 6 + 8 * 2 * 4), 3 * 2 * 2 * 4 * 6) == (480, 480, 288)

def edge(k):
    return (k * 10**12 + 1_200_000_000 - 1) // 1_200_000_000

assert [edge(k) for k in range(5)] == [0, 834, 1667, 2500, 3334]
assert edge(10**9) == 833_333_333_334
assert (max(3, 5) + 2, 3 + 5 + 2) == (7, 10)
assert 2 * 3 + F(64, 16) == 10
assert (min(64, F(2 * 64, 8)), min(64, F(64, 8))) == (16, 8)
assert (F(512, 32), F(512, 64), 100 * (1 - F(1, 10))) == (16, 8, 90)
assert F(2 + 4 + 2, 8) == F(2, 8) * 4 == 1
assert F(1 + 4 + 1, 4) == F(3, 2) != F(1, 4) * 4
assert 32 + 128 - 64 == 96
frequencies = [1_000_000 + i * 1_999_000_000 // 23 for i in range(24)]
assert len(set(frequencies)) == 24
assert (frequencies[0], frequencies[-1]) == (1_000_000, 2_000_000_000)
assert 24 * 4 + 24 * 4 == 192 < 240
print("Arithmetic assertions passed; no engine or producer called.")
```
