# Candidate reads and first-use authority boundaries

The source manifest is a declared input closure, not a trace-derived quota. Both modes read
an explicit readonly /work export, accepted readonly /cargo-home, the pinned image/toolchain
and exact /controls wrappers. Only /target, phase-specific /receipts and private /tmp are
writable. No live Cargo cache, credentials, global Cargo overrides or host Docker socket is
mounted in containers. Network is none and pull is never. No new dependencies or flags.

| Phase | Declared / newly observed | Remaining bounded audit |
| --- | --- | --- |
| Source selection | Full explicit Git commit, actual file hashes, sorted73 SourceInputs; native target outputs excluded | Git selection/controller reads distinct from compiler reads; no live HEAD input to identity generation |
| Python preparation | Frozen freezer/generator/builder/refusal helpers; five explicit B helper files; all local contract modules and native host/runner/record modules in source inventory; actual pinned Python/module origins in inputs/host-python-tools.json | File-level generator/interpreter/import/config/locale/stdlib/extension reads and environment-use limits require separate B reconciliation; do not infer them from Cargo tracing |
| Trust/data | Actual registry/profile/corpus file hashes; all267 registry/profile/bundle references verified;133 exact pending request hashes | Cases/outcomes are finite input expectations, not runtime duration data or execution authority; source bundles are transitive corpus inputs |
| Rust compilation | Actual wrapper argv/environment; accepted sha2 force-soft flag seen in both compiler commands; actual verbose build logs, dep-info and dependency build-script output records | Actual file/open/stat/failed config/exec/mmap/process/fd/cwd/OS/cache reads need B's new candidate trace; dep-info is not exhaustive read evidence |
| Derived identity | Generated identity output path is upstream; its actual bytes/hash are downstream, pure from checked input records | B compares generator derivation and generated file read in each build; no self-hash |
| Executable | Separate actual debug/release SHA256, ELF header/interpreter/NEEDED records, invalid-input-only observed runs in pinned image | No ordinary host runtime claim follows from image construction; final immutable loader/DSO/inode deployment must be verified |
| Python invocation | Confined no-symlink descriptor reads, complete host joins, canonical request/response checks and process limits tested synthetically | Independent selector installation and containing commit/blob proof; actual accepted human subject and exact B review; no caller-selected authority |

B's earlier probe canary and trace findings are inherited only for their exact corrected C2
source. They do not prove reads for this production candidate. A's BuildReceipt points to
partial actual evidence with complete_bounded_read_audit=false; it cannot satisfy the final
independent review required by resolve_host. The final review boolean must bind actual named
bounded findings and limits, never substitute for unavailable evidence.

The BuildTrust purpose is construction-test-only. Direct Rust uses its separately compiled
registry/profile/case identity plus the actual engine identity; self-rehashed input does not
supply either anchor. Final human approval is downstream and authorizes a finite exact saved
job set and both actual executable digests. Build-time trust is not first-use authority.

Proposed publication order: final candidate audit and exact subject → real human reply →
complete HostRecord containing those preexisting files → normal immutable publication →
external selector with that commit/path/blob and verified runtime root. No containing record
or binary digest hashes itself. Source changes require new BuildInputs/generation/builds;
evidence-only commits leave explicit source identities unchanged.
