# Concrete acyclic build and authority record proposal

`record_models.py` defines six closed Pydantic metadata roots and generates the six exact
JSON schemas under record-schemas/. These are ordinary proposal files, not installed
contract roots, another workload IR, an implemented host resolver or accepted records.
All required final fields are non-null. A syntactically valid metadata object is never
proof of approval, real build or actual execution. No complete HostRecord instance is
created in this package. Synthetic hash values occur only in shape/refusal tests.

## Shapes and canonical identities

All record identities are `content_hash(validated_record)` using the installed canonical
UTF-8/hash functions, with **no embedded self hash field** and no excluded children.
FileBinding.byte_hash is SHA256 of exact file bytes; a canonical record hash and byte hash
are different roles. Require semantic records be stored in canonical UTF-8 before use.
Paths are explicit relative paths rooted in an immutable export, no traversal, symlink
escape, glob, cwd discovery or network fallback. Verify byte digests before parsing and
canonical content hashes after parsing. Every array inventory must be sorted/unique by
its declared key; a future resolver enforces cross-file closure, not merely JSON Schema.

| Root | Exact role and keys (full machine definitions are normative proposal bytes) |
| --- | --- |
| BuildTrust | construction-test-only purpose; semantics file; registry content/file hashes; profiles each with full profile hash/file and finite case_id/graph/point/spec/clock/seed/outcome joins; corpus inventory file |
| ToolInputs | accepted K1 pins, compiler commit/release, target, actual image, Cargo.lock, full/target metadata, unified features, licences, checksums, linker/OS inventory and explicit flags |
| BuildInputs | frozen source commit; sorted path/byte-hash/role source inputs; trust and tool content/file hashes; model subset paths/hash; exact debug+release mode configs; generated identity output **paths only**; explicit permitted environment |
| BuildReceipt | build-input content hash; actual engine; mode/target; actual executable file/digest; image; generated identity output file/digests; actual reads/environment/compiler/build log/origin/software-path receipts |
| HostRecord | actual human decision and independent review files; semantic/trust/build/tool/model joins; loader read inventory; expected engine; separate debug+release executable and receipt bindings; jobs/corpus inventories; exact profile hashes and registry hash |
| HostSelector | independently installed repository identity, acceptance commit, record path and exact record-byte digest; no caller-controlled override |

Hash the model source subset as the sorted array of the exact SourceInput objects selected
by model_source_paths (including semantic law/accounting sources), never as filename-only
strings. The engine is:

- implementation_hash = content_hash(BuildInputs)
- compiler_lock_hash = content_hash(ToolInputs)
- model.implementation_hash = content_hash(the selected sorted SourceInput array)
- name=native, version=native-stage/1, model.name=fixed-delay, model.version=1.

These existing reserved version literals are proposed to remain for first public K2 use;
new implementation hashes bind the accepted first-use laws and schema revision. No old
library-only K1 identity or synthetic label hash satisfies the real build requirement.

## Hash/read dependency order

1. Freeze code/semantic/schema/tool inputs at a published source commit. Source metadata
   records this commit. Build code must not read dynamic repository HEAD, untracked files,
   timestamps, caller environment or final-record paths; any read must become an explicit
   audited input before acceptance.
2. Freeze **engine-free** finite profiles/registry/corpus and the construction BuildTrust.
   Profiles/registry contain no engine, job, binary, receipt or final acceptance identity.
   Trust purpose describes its limited authorization power; it is not a qualifying flag.
3. Create ToolInputs and BuildInputs. Input files include the actual build/identity generator
   and scripts, source modules, canonicalization, schema, accepted trust content and tool
   manifest. Generated identity source, executable, jobs, BuildReceipt and HostRecord are
   outputs and cannot be source_files. BuildInputs itself is not in its input file inventory.
4. Compute the three logical identity hashes, generate the exact identity module as a pure
   function of these inputs, and later build. The generator's source is an input; generated
   identity bytes are verified derived outputs. Their hash belongs in BuildReceipt, not
   BuildInputs. Source commit must precede generated identity/receipts publication; do not
   amend source to embed the eventual receipt and then claim the same identity.
5. Build both configurations from the **same** logical manifest, whose mode_configs includes
   both exact modes. Record/verify actual debug and release executable digests separately.
   Shared logical identity permits debug/release deterministic result equality but does not
   let one binary stand in for the other. Each receipt must match its mode, target, tool
   inputs, generated identity and actual origin. No unverified binary is selectable.
6. Form complete jobs with the actual logical engine identity and exact accepted saved
   inputs. Jobs and hashes are outputs. Final HostRecord binds these, both receipts/binaries,
   inputs, independent review and actual human decision. Its file may be committed only
   after those inputs exist; the externally installed HostSelector pins the containing
   commit/path/blob. The acceptance commit is intentionally **outside** HostRecord's own
   hash. No final receipt, executable digest or final record appears upstream in its own
   computation. A record cannot self-assert its authority. The decision/review files name the frozen
   upstream build/trust/binary/corpus subject, not the eventual HostRecord hash. Human
   installation of the external selector authorizes the final record bytes. A decision
   embedding that eventual record hash while being hashed inside the record is forbidden.

A human may authorize a bounded construction/test experiment with the frozen BuildTrust
before a final HostRecord exists. Such binaries and test runs are explicitly construction
controls, not qualifying public first use. The direct Rust boundary checks the compiled
finite allowlist and real logical identity; that prevents arbitrary caller profiles but
cannot establish human first-use permission. Qualifying invocations additionally require
the independently installed HostSelector and validated final HostRecord. A synthetic test
anchor never becomes qualifying merely by moving it into a file or flipping a boolean.
No runtime `--approved`, `--registry-hash` or caller pathname may create authority.

The final resolver must check all duplicate joins: HostRecord profiles/cases/registry equal
BuildTrust; engine hashes equal BuildInputs/ToolInputs/model subset; receipt engine/mode/
target/image equal manifests; executable digests equal actual selected bytes; job inventory
has exact bundle/point/clock/seed/admission/profile/registry/engine closure; human decision
names this exact subject and finite outcome map. Hash equality alone proves content, not
review scope. Null/missing/unknown joins, placeholder labels, unknown profiles, caller
rehashes, a different binary advertising the same identity and wrong mode/target all refuse.

## Read inventory for B's actual future audit

| Phase | Required reads / source | Identity and exclusion boundary |
| --- | --- | --- |
| Manifest selection | frozen published tree, all Rust modules/build.rs/manifests/config, generator and any Python helper | Enumerate actual imports/includes/macros/build-script inputs, parent initializers and function-local imports; no assumed count |
| Canonical/schema | installed contract mapped/hashing/common dependencies and generated mirrors; Python interpreter/uv.lock; Rust numeric/serializer sources | Actual imports and data are inputs if used by build or verifier; no automatic selected-policy exclusion |
| Trust selection | exact proposed semantic file, registry, full finite profiles, corpus inventory and referenced bundle/spec/clock bytes | Parse existing M carriers; registry/profile have no engine/job/binary refs; files explicit, never discovered |
| Tool construction | accepted pins, compiler/components, lock, complete package sources/checksums/licences, features, linker/OS and image/cache inventory | Private construction output becomes candidate ToolInputs only after actual review; cache hit does not prove current executable |
| Identity generation | BuildInputs/ToolInputs/BuildTrust plus generator and enumerated environment | Trace opens/env; generated identity content is derived and verified, never recursively hashed as input |
| Binary build | actual Cargo metadata/artifact paths, source, dependencies, linker, flags, generated identity | Fresh outputs in private target dir, stdout/stderr and read/environment inventories; no PATH or stale-target guessing |
| Host resolution | host-installed selector, exact published acceptance blob, human/review subjects and all referenced manifests/receipts/inputs | Content/file/Git joins all verified; external authority root is not read from workload JSON |
| Launch | verified immutable selected executable, actual device/inode/path/digest, canonical revalidated job, finite profile/registry | Maintain immutability/TOCTOU premise through execution; verify both modes separately; refuse inability to maintain it |
| Parse/receipt | actual stdout/stderr/exit, host operational metrics and executable/input identifiers | Installed result validation plus accepted causal law; no repaired/synthesized completed result |

Preserve separate inventories for build, loader runtime and selected generator support.
A's26 loader/56 support observations and B's independent match at8b7a647 are inherited,
not predictions for the future host resolver. This addendum adds no production reverse
import or authority read. If actual selected inputs change on eventual installation,
B must propose the bounded freeze/human-generation/audit/adoption lifecycle and hold the
affected source from green publication. Do not regenerate/adopt artifacts during this
proposal or exclude an inconvenient edge.

The reproduced baseline inventory is in read-inventory.json: each current loader path and
byte hash, actual imported origin names, the single explicit saved-job read, and every
selected-support path/hash. validation/read-audit.json retains B's original harness output
verbatim, whose embedded source label remains418d697; validation/checks.json records the
actual invoked4ede30d export. No future build/host dynamic read set is claimed from that
current loader audit.
