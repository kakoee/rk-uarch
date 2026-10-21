# U4b native reference implementation — consolidated handoff

**One coherent implementation proposal; protected installation remains human work.**
The user approved the nominal model and semantic interface at
`180c6b9fb5df6af46f5df3601c7c895a79ac8d23`, including its labelled STUB estimates.
This package implements that baseline in the existing mapper, ordinary interface and
single native engine. Published main continues to run the installed component implementation
until a human installs the complete transition. No new semantic decision is requested.

The scope is exactly the approved 52 units: 12 matrix, 9 memory, 24 operator envelopes,
4 complete decoder layers, 2 DRAM gathers and 1 minimal launch unit. Required Q/K rotation,
conversions, norms, residuals, append, attention and gated FFN work remain in those envelopes.
There are no added benchmark rows, embeddings/heads, second engine or prediction table.
This is implementation evidence, not device observability, final benchmark acceptance,
silicon accuracy, a frozen U5 prediction, a lane signature or U4 closure.

## Concrete protected installation

The [complete transition](transition.patch), [patch checksum](transition.sha256),
[base commit](base-commit.txt) and [reconstructed source tree](source-tree.txt) freeze the
reviewable source. Reconstruct in a new disposable directory:

```sh
python docs/reviews/U4b-native-reference-implementation-v1/reconstruct.py /tmp/u4b-review
```

The script exports the recorded base, applies the patch only in that new directory and
checks the resulting tree. It does not install into main or create a runtime approval file.
The base incorporates peer commit `776321470cd5edf722adc97ae036a45398403704`, the inspected
report-test correction after the approved model baseline. The transition does not edit or
reverse that peer change. Further peer history must likewise be preserved when installing.

Human installation must carry the whole patch together under the existing human-owned-file
procedure. It includes the additive contract carriers/schemas, the approved U0011 amendment
and interface document, and their dependent implementation/checker/package changes.
Installing only the imports or only the schemas would leave an incoherent checkout.
The coordinator checkout was read only. No protected installation occurred on main.

No golden expectations, vendor snapshot, dependencies, lock files, prediction artifacts,
measurement kit, CI workflows or deployment permissions are changed. Ordinary users still
select an executable and supply a saved job. They need no executable digest, HostRecord,
review token, startup guard, source archive or build-tracing record.

## Implemented interface and mapping

- Component `/4`, model 2, TaskGraph/1 and observations/3 remain supported. Reference `/5`
  uses `TpuV5eReference`, model `native-intervals/3`, engine `native-stage/3`, TaskGraph/2
  and observations/4. Package version remains `0.0.1`. No dummy clocked HardwareSpec exists.
- The packaged nominal reference has the approved 9 published numeric facts and 17 numeric
  STUB claims. Their basis remains in [MODEL](../../../validation/L3_silicon/tpu-v5e/u4b/MODEL.md)
  and [the parameter catalogue](../../../validation/L3_silicon/tpu-v5e/u4b/model-parameters.json).
  Production admits these STUBs. Missing/invalid inputs, false joins, unsupported precision,
  incomplete coverage, invalid lifetimes and infeasible mappings refuse before execution.
- Source closure reuses the v2 operand, prepared-op, rotary coefficient and KV conventions.
  Epsilon, attention scale and raw INT8 range are explicit numerical inputs. Complete
  decoder roles, dimension joins, exact supplied coefficient bits, positions, page
  permutation, valid context and tail traffic are checked. Coefficients are never regenerated
  by execution or replay. Raw INT8 remains bounded signed inputs with INT32 storage/output.
- Matrix tiles use M chunks up to 1024, physical K/N 128, stable four-MXU ownership and
  explicit double-buffer dependencies. Partial stores/reloads occupy shared VMEM; BF16
  conversion occurs once at the final K boundary. An explicit mapper spill counterpart
  adds HBM spill/reload transfers; the engine never silently retiles or spills.
- Packed matrix input/weight layouts are stated mapping choices. Decoder activations are
  contiguous: supplied X is packed once with charged gather/materialization traffic, and
  matrix outputs have explicit row spans. Attention explicitly materializes scores and
  probabilities, converts probabilities to BF16 for AV, shares K/V by KV head, and joins
  head outputs into contiguous output. These are modelled choices, not observed XLA layouts.
- Vector groups contain typed arithmetic, cast, special-function and staged pairwise
  reduction work. The VPU remains occupied through the group, including setup, so its
  declared 64 KiB transient workspace is not concurrently reused. Semantic convention
  counts, typed useful work, issued padded work, casts and fill-only service are distinct.
- Read/reduction, scalar runtime fill, copy, reverse-page gather, append and scalar FP add
  use the same graph/runtime. Cache layout is `[batch, physical page, head, token, D]`;
  gather outputs are contiguous `[batch, token, head, D]`. Payload spans preserve holes,
  page boundaries and tails, with at most 8192 bytes per logical request. Index and output
  traffic are included. Physical transaction counts stay null.
- Startup occurs once per invocation. Priming retains only declared SMEM metadata bound
  to its control producer, resets payload/scratch/credits and restores the fixed context.
  The reported iteration alone contributes counters. Equality after one/two primes is a
  property of this reload policy, not evidence of device retention.

The same native `Runtime`, sequence/event machinery and resource queues execute both
models. Reference service is rational picoseconds with ceiling only at integer completion;
shared bandwidth cursors retain fractional progress. The wheel additionally accepts a
queue bucket width directly, which is an indexing choice rather than a hardware clock.
Active-bucket indexing avoids scanning empty buckets; existing event ordering and component
regressions remain covered. Reference serialization avoids duplicate large JSON trees while
preserving the existing canonical bytes and hashes.

Finite reference limits are 256 MiB input, 512 MiB output, 500,000 graph tasks, 2,000,000
sequences and a 600-second ordinary native process deadline. Component limits remain
64 MiB and its existing deadline. Actual selected maxima and complete, untruncated output
sizes are recorded in the integration receipt. These are software bounds, not hardware
parameters. Large detailed graphs still require substantial host memory; no simulator
performance or controlled-host qualification is claimed.

## Ordinary installed use

Preparation is available through `rkuarch.mapping.component.map_reference`,
`rkuarch.workload.reference.suite_source/nominal_hardware`, and the ordinary `prepare_job`
dispatch. `uarch_contract.reference_json.blocks` writes the same canonical format without
copying the entire graph. Inputs are prepared once and saved; execution never invokes a mapper.

```sh
python -m rkuarch.engines.native.ordinary run --job job.json --executable /path/to/uarch-engine --output result.json
python -m rkuarch.engines.native.ordinary replay --job job.json --output result.json
uarch-engine --protocol uarch-engine/5 < job.json > result.json
```

The wheel contains the reference carriers, schemas, nominal values, ordinary consumer and
independent checker. Replay needs neither the producer nor an executable. Test-only
synthetic hardware still requires the existing explicit test invocation; normal reference
STUBs do not. Data hashes and software versions remain ordinary provenance.

The packaged checker validates complete activity/task/sequence inventory, exact rational
services, earliest resource grants, HBM FIFO/spacing/window release, typed/per-op counts,
allocation intervals, metadata/context identities, consumed STUB leaves and critical causes.
Critical path parts must cover the duration and name actual service/issue relationships.
It computes no schedule and imports no mapper or native calculated-duration helper.
Consumed STUBs include admission reads (such as both peak-share checks), not only parameters
that lengthen a particular job's critical path. Result calibration remains `stub`, error
`unknown`, energy `unverified`; unrepresented energy/physical transactions remain null.

The additive `u-c0-tpu-v5e/1` resolver preserves useful-work aggregate and per-op baselines,
with typed casts/reductions and mathematical operand bytes. It excludes native startup,
padding/fill, local staging and HBM latency/credits. The integration records comparisons;
it does not redefine the additive C0 formula as a universal bound on arbitrary overlap.
The independent native resource-demand lower bound remains a separate checker law.

## Evidence and review status

See [EVIDENCE](EVIDENCE.md) for exact commands, actual pass counts, installed module origins,
serialization maxima, fault controls, inherited evidence and deferred checks. The reusable
campaign is `validation/reference/run_integration.py` in the transition. It tests each of
the same 52 selected units through ordinary production execution in three fresh processes,
debug/release byte equality, noneditable installed replay with producer imports disabled,
and a second priming count. After checking the first result independently, exact equality
of all result content except the changed input identities and prime count reuses those
checks for the second result; that result's own identity and new bindings are checked too.
No nominal duration table or simulated output corpus is published as U5 predictions.

Author verification does not constitute independent review. Human protected installation,
independent implementation review, human L1 worksheets, the U0024 remote/controlled-host
obligations, compiler/event/state correspondence, both benchmark lane signatures and final
benchmark acceptance remain separate. U-P9 still owns the prediction ordering/freeze join;
U-P10 owns device measurements. This task neither performs those steps nor closes U4.
