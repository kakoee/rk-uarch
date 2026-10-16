# A intermediate source/interface — construction milestone, not final freeze

This source implements the fixed-delay carrier/admission/accounting boundary and release-aware
K1 extension, plus the Python subprocess/host resolver. It is an intermediate development
subject for B, not a final audited build or first-use authorization. The accepted C1 manifest
and lock are installed in owned native files. c678ded and B bcecc67 evidence remain unchanged.
B 24600f9 is integrated; its canary/probe traces are inherited B observations, not A build reads.

Native target: package and executable `uarch-engine`, library `uarch_engine`. The normal binary
requires a generated `native/crates/uarch-engine/generated/identity.rs`, whose actual identity
will derive from the frozen published source and engine-free construction trust/tool inputs.
There is no fallback engine hash or workload-supplied authority. Identity generation and final
build metadata are still being completed; this commit is not the final audit subject.

The process takes exactly `--protocol uarch-engine/3`, one UTF-8 JSON object through EOF, with
JSON whitespace permitted on input, duplicate/marker/trailing-data refusal. Exit 0 is one
canonical result object, no newline and empty stderr. Exit 2 is empty stdout and one canonical
stderr object with exactly code/message/pointer (pointer string or null). Exit 1 is internal/IO
failure, never semantic evidence. Python rejects other statuses/framing, validates canonical
bytes and the installed result laws independently, and separates transport from refusal.
The exact currently implemented refusal vocabulary is `runner.REFUSAL_CODES`.

Operational caps: input/output each 64 MiB; 100,000 jobs; 100,000 owners; conservative scheduled
plus inline event bound 3*jobs+dependencies+clock-setup entries <= 1,000,000; observations bound
events+6*jobs <= 2,000,000. No truncation into success. Owners are sorted u64 identifiers mapped
to dense internal u32 IDs, not array bounds. Python defaults: 30 seconds, 64 MiB stdin/stdout,
1 MiB stderr, concurrently drained with nonblocking selectors; timeout/cap kills the launched
process group and reaps the child. These are operational limits, not performance claims.
B should check these against the entire prospective finite corpus before final freeze.

Python entry points: `engines.native.runner.encode_request`, `parse_response`, `run_fixed_delay`;
`engines.native.host.resolve_host(mode=...)`; six records in `engines.native.records`.
The proposed independently installed selector location is `/etc/rkuarch/k2-host-selector.json`,
root-owned, no group/world write. It is not installed. Workload paths/environment/CLI cannot
select it. File resolution uses relative explicit bindings, descriptor walks with O_NOFOLLOW,
byte hashes and full record joins; launching uses a verified read-only executable descriptor.
Both actual debug/release digests are checked separately even when selecting one mode.

The host decision/review subject shape is explicit in `host._resolve`: build/tool/trust/model
hashes, both executable digests and corpus/jobs byte hashes, with no containing receipt hash.
A future exact human decision and B final read/currentness review are required; no present
synthetic record qualifies. Remaining hardening/tests and complete actual build records are
in progress under this same milestone, not a request to stop for another vote.

New observations so far: five release tests all failed against a forwarding-only K1 baseline;
implemented release/phase behavior passes them and existing K1 tests. Current private library
selection: 41 passes, including DTO validation (no execution), protocol refusals and accounting
helpers on private Job values. Python transport selection: 14 passes. Raw command/error/tool
receipts are private under `/tmp/u4-k2-impl.69r1lz_3`; final handoff will bind compact receipts.
No successful public MappedEngineJob was executed. Public end-to-end cases and final metadata
are still in preparation, and final qualification/first-use/C3/U0024 remain separate.
