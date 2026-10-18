# A-only refusal codec correction for B's final candidate review

The actual native47-case probe on a06c364 returns the expected20 negative outcomes,
including SramCapacityExceeded and LiveBufferAlias, with zero runtime entries. A's
initial D3/adapter consumption reused the K2 decoder, which correctly excludes those
component codes. That consumer wiring was wrong; it is not a native or B expectation
mismatch. Those failed consumption attempts are not credited as passing D3 checks.

A now has an additive component decoder using installed ProfileEntry outcomes plus
native structural errors, retaining exact canonical framing/status/stream validation.
K2's decoder/code set is byte-unchanged. Five literal regression cases failed first;
a targeted private removal of component codes also fails all five, and exact restoration
passes. No native timing change, new law, dependency or old K2 pin transition is involved.

The final unapplied D3 source/patch is version2; version1 is preserved. The private
adapter now uses the component decoder too. This changes A's source/build binding;
a06c364 remains a superseded observed candidate, not silently rebound current bytes.
The native unit executable and Rust source are unchanged, so their independent laws,
typed controls, lint and earlier behavior evidence remain explicitly reusable.
B's strict-type annotation and prospective consumer binding transition requested in
peer-consumer-types.md remain a distinct owner dependency. Final candidate review must
use the actual final source/executable/import/consumer package, not prior arithmetic.
