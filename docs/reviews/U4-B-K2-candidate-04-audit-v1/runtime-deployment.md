# Final deployment preconditions — proposal, not installation

The actual ELF targets are Linux x86_64 PIE. Both request
/lib64/ld-linux-x86-64.so.2 and need libgcc_s.so.1, libc.so.6 and ld-linux-x86-64.so.2.
B independently inspected both actual binaries with readelf and rehashed the accepted image
runtime. runtime-hashes.txt binds libc, loader, libgcc, ld.so.cache and readelf. In particular:

| Runtime byte identity | SHA256 |
| --- | --- |
| libc.so.6 |6b4a45352fd0c540a9c7c718f35ce8c8e46a4e482f9d3885a910c32d1a0e1421 |
| ld-linux-x86-64.so.2 |02bcda52c1a5dfc236f94d9e5255b4a0e26347d8a372a5223b650e31f291ce3c |
| libgcc_s.so.1 |2bd1552c47799ef67e701e81d4383061fd76059868e446e63560f0dd0d5ec14e |

These are observed image identities, not an instruction to copy system libraries or change
a host. The human/coordinator must select the actual launch namespace and immutable runtime
root. Using that exact existing runtime avoids a new library compatibility inference, but
Python's current runner directly executes an ELF descriptor; it does not automatically wrap
it in Docker. Do not substitute a shell/Docker wrapper for the accepted executable hash.
If an ordinary host is selected, audit its actual loader, transitive DSOs, search/cache and
namespace against the selected deployment before granting execution. A different runtime
requires a concrete reconciliation, not an automatic claim that the build image covers it.
No new image, distribution, packages, privilege/security relaxation or host change is made here.

Assembly order:

1. Reconcile the exact review.json subject and choose the runtime namespace/root and immutable
   ownership/mount controls. Materialize declared relative source/data/receipt/generated/job
   paths and both actual binaries without changing bytes. Verify all hashes and full133-case
   membership. The HostRecord proposals refer to real A ordinary receipts supplemented only
   by the independently observed B read inventory; the logical engine and binaries stay fixed.
2. Obtain the genuine exact human first-use reply. Bind its actual decision file in
   HostRecord-proposal's proposed_fields. Do not synthesize the required yes/accepted_by fields.
   The decision and independent review predate the HostRecord, avoiding a self-reference.
3. Normally publish the complete HostRecord; independently verify its containing commit,
   path and blob against the immutable publication. Fill the external selector only afterward.
   acceptance_commit is a declaration in the resolver; installation must prove the Git join.
4. Under separate installation authorization, place the real selector at
   /etc/rkuarch/k2-host-selector.json, root-owned and not group/world writable, with the selected
   root and exact record byte hash. Establish immutable binary inode and runtime files for
   the execution interval. chmod0555 and an open descriptor prevent neither owner rewrites
   nor modifications through another writable mount; descriptor pinning covers pathname swaps.
5. Reverify both executable hashes and runtime closure in the actual namespace, then resolve
   both modes and execute the first-use-obligations.json selection. Preserve all receipts and
   expected refusals. Public mapped success/replay/fault controls remain pending until here.

The current runner uses a fresh private working directory, PATH=/usr/bin:/bin and LC_ALL=C,
no propagated LD_LIBRARY_PATH, canonical EOF-framed JSON, bounded concurrent stdin/stdout/
stderr, process-group cleanup and timeout. Its30s/64MiB/64MiB/1MiB limits are operational
controls, not simulator performance results. Native event/observation caps remain distinct.
No authority is inferred from a schema-valid synthetic host or structural result test.

This is the genuine remaining human/runtime boundary. It does not require another K1 or C1
licence/pin decision, does not authorize successful public execution now, and does not expand
K2 into component models, human L1, remote CI, C3, G3a, performance or sprint closure.
