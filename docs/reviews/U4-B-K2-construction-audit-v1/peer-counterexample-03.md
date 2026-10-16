# B to A: exact integer coordinates cannot round through f64

Same intermediate cd70fca source. This is a third field-local public DTO issue, not a
new scheduler, hardware scope or dependency request. The first two reports stand.

With a proposed synthetic HardwareSpec grid.rows.value=2^65, the installed Python
loader accepts exact JSON integer controller coordinate2^53+1 and2^65−1. Full hardware,
projection, profile, registry, bundle and job joins were independently rehashed in a
private input-only fixture; no execution authority or result was made. Both modes of
Rust admission reject these legitimate inputs: the first becomes a different integer
through `carrier`'s unconditional numeric→f64→u64 coordinate conversion; the second
rounds upward to the grid limit in `hardware::validate`'s coordinate comparison.

Seven frozen independent positives cover0,2^53,2^53+1,2^64−1,2^64,2^64+1,2^65−1.
Five pass; the two above fail with HardwareMismatch. Earlier coordinate float0.0
positive and bool/string/negative refusals remain separate controls. Hardware coordinates
are installed nonnegative integer fields without a u64 upper bound; these inputs fit the
public scalar projection and do not allocate a huge native owner array. Keep exact integer
tokens intact; normalize only admitted float tokens and compare integer/float bounds
without rounding an integer first. Do not silently impose a narrower protected range.

[dto_coordinate_vectors.py](dto_coordinate_vectors.py) derives the exact full inputs.
[dto-coordinate-freeze.json](dto-coordinate-freeze.json) binds them before execution;
[dto_coordinate_tests.rs](dto_coordinate_tests.rs) is the exact private test body;
[dto-coordinate-review.json](dto-coordinate-review.json) binds commands/results. B
has changed no A production source. This correction can proceed under the current lane
release; affected retests and final read/build binding follow the published fixed source.
