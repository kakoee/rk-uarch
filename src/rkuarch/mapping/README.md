# mapping — named, versioned policies

A policy is a pure function (op graph, HardwareSpec) → TaskGraph, and a STIPULATION about how
a compiler would lay the work out. Its name@version travels to every row. There is no search
and no autotuning. A better policy is a new version, never an edit. A policy declares the
matrix dataflow it needs and its buffer depth, and places every SRAM-resident buffer (core,
offset, bank); a tile that does not fit is refused, never spilled silently. No mandatory
external-tool compatibility policy is required. Optional references need matched resolved work.

Policies execute in preparation, before simulation. U-P7 serializes their complete TaskGraph
output for inspection and replay. An externally supplied mapping follows the same validated
format and bypasses these policies. Engines never silently remap an input. Record producer
versions, hardware binding and content hashes; moving a file is not a mapping change, while
changing placements under the same policy label is. Keep local preparation as the default.

U4 component input API: `component.map_component` implements ws-rowsplit@1 for the exact
npu-l4/ratio1 BF16 q_projection slice. It emits explicit TaskGraphs without timing. See
[the API and limits](../../../docs/reviews/U4-A-component-mapper-v1/interface.md), including
current accumulator lifetime limitations. Workload assembly and saved replay are separate.
