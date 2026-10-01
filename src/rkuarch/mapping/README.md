# mapping — named, versioned policies

A policy is a pure function (op graph, HardwareSpec) → TaskGraph, and a STIPULATION about how
a compiler would lay the work out. Its name@version travels to every row. There is no search
and no autotuning. A better policy is a new version, never an edit. A policy declares the
matrix dataflow it needs and its buffer depth, and places every SRAM-resident buffer (core,
offset, bank); a tile that does not fit is refused, never spilled silently. onnxim-compat@N
exists only so the native engine can be compared with the fork on the same work.
