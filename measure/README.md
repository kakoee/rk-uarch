# measure — silicon measurement kits

Written and dry-run before any paid hour or real card run: CPU JAX for tpu-v5e/, ttsim
(functional only) for blackhole/. Dry-run outputs are labelled SYNTHETIC and the ledger refuses
them. Real runs happen only after check_ordering passes. Every result captures its environment.
Timing is device-side only; kits also record the compiler-reported FLOPs and bytes, and the
device counters the chip exposes.
