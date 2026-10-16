# Scope of the completed bounded audit

The two fresh builds use the accepted image with --pull never, networking disabled,
read-only source/cache/controls/diagnostics, UID1000, no capabilities and unchanged seccomp
plus no-new-privileges. Only private targets, receipts and tmpfs are writable. Exact Cargo
arguments, source and permitted environment match candidate-04. The diagnostic prefix uses
the inspected image loader with a tracer-only --library-path; it does not inject a loader
search path into Cargo or descendants. Every acquired file/symlink was reverified against
the earlier inspected private diagnostic tree. Acquisition notices remain in the original
package; no image/tool installation or distribution occurred.

The previous accepted canary and sentinel/missing-record controls are inherited for the
unchanged monitor, tracer and security configuration. Candidate-specific missing-child and
missing-terminal controls were newly executed in memory and refused. Restored originals
passed. Both candidate traces ended below10min/512MiB with no truncation or monitor stop.
Raw logs, compiler wrapper output and per-file hashes remain private under the recorded root;
build-traces-summary.json binds their exact private monitor receipts and complete file-hash
inventories. The unchanged parser preserves per-process order, joins unfinished/resumed
calls, checks child coverage and terminal records, and rejects truncated relevant path/argv
records. Trace buffers are not claimed as full file contents.

Native observations include successful/failed opens and config probes, directory traversal,
fd-decoded reads, exec, mmap, inherited cwd, symlinks and generated target/build-script files.
The470 tool/image/OS path queries per mode are bound by the actual accepted image;154 dynamic
kernel/device paths are not source.648 cache queries bind to the unchanged1719-file cache.
Generated/temporary path counts are1291 debug/1094 release; final generated-file hashes do
not recover every transient historical byte. The17 actual source files include generated
identity.rs; tests/helper source declared upstream but not read in binary builds remains
explicitly distinct. Native unit/admission test builds are ordinary untraced follow-up
checks, not additional traced build-closure claims.

The identity generator independently rechecked source, trust, registry/profile/corpus,
semantic and tool-record bindings, then reproduced generated identity bytes. BuildTrust and
profile/registry are engine-free. BuildInputs includes the generated output path, not its
bytes; logical implementation/tool/model hashes precede generated source, binaries, jobs,
receipts and final host authority. No generated output, binary or containing HostRecord
hashes itself. Full actual saved-job equality against independent B assembly checks the
transitive corpus bundles that are downstream of the generator's narrower reads.

Generator Python opens and imported module origins were recorded independently; all project
origins are private.173 common interpreter/stdlib/third-party module byte identities match
A. This hook begins after interpreter startup, does not intercept all C-extension internal
IO/stat calls, and does not prove environment-variable use. A's frozen Python/tool inventory,
source inspection and exact regeneration supplement it. Neither dep-info nor linker maps
alone are treated as exhaustive reads. The read_audit_complete boolean in review.json means
this named bounded construction audit is complete; it does not assert universal, semantic,
all-environment or all-runtime closure.

The loader's inspected data reads are the independent system selector; bound HostRecord,
BuildInputs, BuildTrust, ToolInputs, semantic/review/decision/corpus, all source files, both
executable receipts and binaries, registry/profile/job files; and a selected descriptor at
launch. Import closures include their initializers and installed contract imports. Public
invocation does not read the oracle, rebuild mappings, generate a candidate, consult ambient
workload authority, or import rk. Fresh producer-disabled relocation and caller-rehash tests
passed in the224-test selection. Source isolation and strict adopted-artifact currentness
passed independently; these are different checks from native input closure.

A runtime deployment is still required. The accepted image's immutable bytes explain these
construction/invalid-input observations, not arbitrary later host libraries. The resolver
checks selector ownership, relative paths, no symlinks, hashes, complete corpus membership
and both executables; it does not establish OS-level inode immutability or consult Git to
validate acceptance_commit. Those limits are explicit installation preconditions, not hidden
runtime guarantees. See runtime-deployment.md before final authority installation.

Reproduction uses the exact helper copies placed in a new private root with a7639542 export,
the checked73 source files from24fa368, regenerated identity, copied accepted cache,
controls/vectors and verified diagnostics. check_identity.py/check_corpus.py are host-only;
trace_builds.py uses the prior reviewed monitor and A's exact permitted environment;
native_checks.py runs only units/admissions/invalid public inputs; host_checks.py and
guard_checks.py use explicit roots and sanitized imports. Most recipes derive their scratch root
from their copied location; prepare_export.py and dependency_audit.py explicitly pin the
recorded private root and refuse/recheck their inputs. Do not run these scratch recipes in historical packages.
The executed helper hashes and formatting-only AST equivalence are recorded in helper-bindings.json.
