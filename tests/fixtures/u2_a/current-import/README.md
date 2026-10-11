# Current supported import, independently specified tiny decoder

This is an additive current identity binding of the hand-authored two-layer D4 graph
in `contract/tests/fixtures/u2/independent-bundle.json`; the historical fixture remains
unchanged. No model producer, core evaluator, oracle or result lookup constructed its
work. Only `intent.assumptions_hash`, `intent_hash` and `bundle_hash` were updated once
using the accepted current physical model identity. Point hashes, graph dimensions,
operand extents, multiplicities, hardware rates and queries are byte-semantically
unchanged. The construction procedure and old/new file hashes are in the Stage 2
response's `import-construction.json` and `construct_import.py.txt`.

The deliberately small graph has two layers, D=4, two query heads, one KV head, head
width 2, FFN width 8, vocabulary 8 and untied head. Decode B=1/T=17 and prefill n=1/L=1
have independent literal expectations respectively:

| Query | Matrix ops | Vector ops | Reads, bytes | Writes, bytes |
| --- | ---: | ---: | ---: | ---: |
| Decode | 1184 | 572 | 1296 | 288 |
| Prefill | 672 | 252 | 1040 | 288 |

Decode per-op duration is 1,892,000 ps, aggregate U-C0 1,584,000 ps. These hand-worked
expectations predate the producer. KV reads consume 17 valid tokens per sequence:
K+V use 136 bytes per layer (17 × 1 KV head × D2 × 2 operands × 2 bytes), despite two
allocated 16-token pages. Counts are one rank, one iteration, two layers.

`test_current_import_exact_bytes_without_preparation` consumes the exact fixture via
public `uarch capture`, including real analytic subprocess execution, with preparation
and rk imports trapped. It never reseals or regenerates the input. The test checks a
literal fixture-file SHA256 before execution and literal result expectations; the
negative trap control verifies that high-level preparation really is blocked.
A separate rehashed wrong-model-version input still refuses. `assumptions.json` is
a model declaration, not a review, reference, measurement or eligibility grant.

The current engine implementation binding is intentionally strict. A future core
source/version change requires an explicitly reviewed fixture binding update; this
fixture must not be silently repaired at runtime. No policy change is made here.
