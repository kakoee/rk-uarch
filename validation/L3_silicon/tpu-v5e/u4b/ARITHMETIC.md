# Independent preparation arithmetic, revision 2

These are agent-authored synthetic interface examples, not human L1 worksheets, engine
results or TPU predictions. The [checker](check_model.py) uses only the standard library
and literal arithmetic; it imports no native executor, mapper or production count helper.
The original count examples and their tests remain in IMPLEMENTATION/check_package.

## Matrix, allocation and source provenance

- Synthetic 4×4 array, M=3/K_valid=5/N_valid=3: split K into 4+1, pad each K/N to 4.
  Useful MACs = 45, issued MACs = 96. Each slice's generic fill equivalent is
  `(4+4-2)*4*4=96`, so total **service-equivalent** MACs = 288. At a synthetic 32 MAC/ns
  this is 9 ns, not 288 executed MACs. At half that synthetic rate it is 18 ns. No clock
  appears. Two K slices must own the same output partial; splitting onto separate MXUs
  without an explicit reduction is invalid.
- BF16 M=3/K=130/N=7: inputs 780+1820 B, output 42 B; useful operations 5460. With a
  logical 84-byte FP32 partial and two K slices, local partial writes=168 B, later-slice
  read=84 B, final conversion read=84 B: 336 B of partial traffic, plus output writes.
  Do not call those partial stores HBM traffic. Raw INT8 uses 390+910 B inputs and 84 B
  INT32 output. No requantization/scale payload is implied.
- Nominal mapper upper tile M=1024/K=N=128 BF16: one X=262144 B, W=32768 B,
  double-buffered inputs=589824 B, partial=524288 B, Y=262144 B; total 1376256 B/MXU,
  5505024 B across four before other live buffers. This fits 96 MiB, but is not proof a
  whole compiled layer fits. Unique live buffers and overlaps still determine capacity.
- Coefficient table for 2048 positions, R=128, cos+sin FP32 is 1,048,576 B. It does not
  fit the selected 512 KiB SMEM budget. Keep it in HBM, stage selected rows; only small
  indices/positions may persist in SMEM. One position's coefficients are 512 B. Q and K
  logical reads sum to 1024 B; a declared shared read-only row in a full-layer mapping may
  stage 512 B once with two consumers. Standalone Q and K units each stage their own row.
- Peak-share derivation has a factual numerator but an assumed allocation: BF16
  `4*2*24.625e12=197e12`. The per-MXU record remains STUB, source=null, rationale=null.
  A finite 200000-ps HBM latency STUB is accepted by the existing SourcedValue schema;
  null/NaN and an unsourced spec_derived claim are refused. No schema change to STUB meaning.

## Vector and reduction work

- Logical shape 12×320 occupies six 8×128 tiles, 6144 physical elements, with 3840 useful
  elements. A 1×1 FP32 add occupies one such tile under this chosen layout model, while
  an integer address operation uses scalar/control work. Do not flatten dimensions away.
- Two rows of length 5 reduce in three pairwise stages. Useful combines are 8 total;
  active outputs per row are 3,2,1, but the unpaired tail is forwarded, not combined with
  a fake element. Each stage occupies one physical vector tile. At synthetic tile service
  7 ps and reduction multiplier 2 the service is 42 ps. Length 1 has zero combine stages.
- RMSNorm with M=2,D=4: input casts=8, gamma casts=4, output casts=8. Arithmetic:
  squares=8 multiplies, reduction adds=6, multiply by 1/D=2, epsilon adds=2,
  rsqrt=2, normalize=8 multiplies, gamma multiply=8. Thus typed useful multiplies=26,
  adds=8 and rsqrt=2; typed arithmetic=36, casts=20. The retained semantic `6*M*D`
  convention is 48, not 36. Record both meanings instead of forcing equality. Assuming
  one vector group, register intermediates, 2D shapes and nominal relative costs, there
  are 5 cheap arithmetic tiles, 2 reduction stages costing 4 quanta, one rsqrt tile
  costing 8 and 3 cast tiles: 20 quanta before setup/control/VMEM. These are work-service
  units, not a hardware instruction count or measured duration.
- Stable softmax of one fully valid row L=3, including score scaling: scale=3 multiplies,
  max=2 comparisons, subtract=3 adds, exp=3, sum=2 adds, reciprocal=1, normalize=3
  multiplies. Typed useful arithmetic=17 (plus required casts). The legacy softmax-only
  semantic convention is 15. For causal S=T=3,Hq=2, valid pairs=12 but dense score lanes
  are 18; mask/select work is explicit, and useful triangular pairs do not eliminate the
  executed dense score or padded reduction service. Separate the scaled/masked envelope
  from the convention, rather than adding a constant to every old counter.
- RoPE Hq=2,Hkv=1,R=D=4: 12 elements, 6 useful arithmetic operations per pair give
  36 arithmetic ops and 24 casts. With Q pairs shaped 2×2 and K pairs 1×2, each separate group has six
  pair-primitives occupying one vector tile each. Each group also has two casts, shaped
  2×4 or 1×4. Combined issued arithmetic=12288 and casts=4096, distinct from useful 36/24. Position-zero
  coefficients (cos=1, sin=0) do not remove required work from the timing/count model;
  compiler elimination would be a changed measurement envelope to reconcile later.

## Memory, logical requests, timing edges and state

- A valid 2049-token BF16 K+V payload, Hkv=8,D=128, is 8,392,704 B. At p=16 allocation
  is 8,454,144 B across 129 logical pages; at p=32 it is 8,519,680 B across 65 pages.
  A shared int32 page-index table adds 516 or 260 read bytes respectively; contiguous
  gather outputs each preserve the valid combined payload. Neither padding nor indices
  may disappear. Both tail cases remain correctness examples, not added timed units.
- Splitting 20000 contiguous bytes into <=8192-B logical spans produces 8192,8192,3616.
  A 4096-byte valid page tail remains 4096, not 8192. A hole/page boundary can force a split
  below the maximum. These are logical service requests, not physical transaction counts.
- Synthetic HBM example: payload=4 B each, latency=10 ps, spacing=1 ps, bandwidth=2 B/ps.
  With window 2, issues at 0 and 1; eligible at 10 and 11; shared service spans [10,12]
  and [12,14]. With window 1, the second issue waits for completion at 12, then completes
  at 24. This discriminates shared service, credit lifetime and same-time release/issue.
  No production scheduler is embedded in the arithmetic check; these are literal cases.
- Fractional synthetic server: three 1-byte spans at 3 B/ps have rational endpoints
  1/3,2/3,1 and integer completion timestamps 1,1,1; cumulative service is 1 ps, not
  3 ps from per-span rounding. Dependencies/credit releases still use integer events.
- A synthetic device startup of 11 ps plus two sequential op intervals of 3 and 5 ps
  gives 19 ps for one invocation, not 30. A prime plus reported invocation runs 38 ps
  internally but reports 19 ps and one iteration's work. Reusing persisted page metadata
  changes only declared transfers; resetting logical decode length to 2047 cannot silently
  grow it to 2048 for the next invocation. A separate synthetic native resource bound
  with startup 11 and exclusive-owner occupied demands 3,5,4,2 ps is 16 ps. It is a
  lower bound, not the exact dependency schedule or a replacement for the retained C0 law.

## Existing transport limits and concrete expansion check

The installed Rust protocol and Python transport defaults cap input and output at 64 MiB.
A 256 MiB copy has 32768 logical 8 KiB reads plus 32768 writes. A deliberately unreused
4096-cube mapping with M chunks 1024 and K/N slices 128 has 4096 compute slices;
32 X spans plus 4 W spans each produce 147456 input requests, plus 4096 final-output
requests. Those counts are a serialization-size warning, not a mandate to reload data
when an explicit reuse buffer is supplied. Do not claim the current /4 wire cap already
supports R's detailed observations. Keep ordered span descriptors compact and size finite
R input/output/event budgets against the actual serializer and largest approved points
in the implementation milestone. A finite-cap increase is ordinary transport work, not a
new hardware parameter/authority decision; never silently drop observations, truncate
requests or remove the large suite rows to fit. No new budget value is pretended measured.

## What the next implementation should exercise

Use these fixtures with the new interface, then reuse the existing ordinary-boundary,
rotary, resource, lifetime, credit and replay tests named in IMPLEMENTATION. Mutations
must distinguish useful/issued/fill counts, loss of conversion/scale/mask, extra startup,
rounded-away tails, early credit release, false causes, missing coefficient traffic and
incorrect state reset. Imported infeasible mappings refuse; a mapper-produced explicit
spill counterpart for the same mathematical work exposes additional traffic before it is
compared. Do not satisfy capacity tests with hidden native retiling or a smaller workload.
One combined reviewed implementation milestone follows interface approval.
