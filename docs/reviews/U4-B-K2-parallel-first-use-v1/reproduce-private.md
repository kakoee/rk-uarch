# Reproduce the private join without installing a runtime

Use the exact published B helper directory and A publication
`d9a22f047d4410aab4abb75e1fc780a51d7a8f6b` (source correction
`bef76ac7bd9194103cde386b7f3278718efcc94b`). Review source/scripts first.
The final invocation is recorded verbatim in evidence/startup-final-launch.json;
all three A patch/postimage hashes and the31-file import closure are in
combined-reuse-proposal.json. This is saved-result Python testing, never native use.

Reconstruct only these private inputs under a fresh /tmp directory:

1. For each path in private_import_closure, export its Git blob from exact24fa368.
   Apply A's host-session.patch, runner.patch and hardware-rule.patch with git apply
   --check and normal apply. Check every postimage against private_import_closure.
   This is a minimal observed runtime closure, not a copy of the checkpoint.
2. Copy B's parallel_entrypoint.py into a separate private join directory; apply
   combined-reuse-integration.patch and verify B_combined_helper. Name the result
   parallel_case_reuse.py. Copy parallel_core.py, resource_limits.py,
   parallel-policy.json, diagnostic.py, reuse_join.py, startup_join.py and
   session_boundary_controls.py there. Save the exact private_import_closure map
   as proposal-files.json. Freeze helper/source hashes before execution.
3. Reuse the original read-only candidate/python/site/campaign/manifests and real
   selector mounts from the recorded command. Mount the private31-file tree at
   /proposal, helper join at /join, and the unchanged stopped saved evidence at /saved.
   /receipts is a fresh private directory. /parallel is a read-only helper copy.
   Use exactly the accepted image, --pull never, network none, readonly filesystem,
   UID1000, cap-drop ALL, no-new-privileges and the existing64MiB noexec tmpfs.
4. The original mounted interpreter runs -I -S -B, clean environment, with /join and
   /parallel prepended only for helper loading. The final command sets
   sys.argv=["startup_join.py","--controls-only"] and runpy.run_path on
   /join/startup_join.py. That mode reuses the unchanged d0 timing/PID/sixth-fault
   evidence but repeats both final six-operation groups, case controls and14 bound-read
   negatives. Omitting the switch additionally runs the same8 saved validation batches
   at1/resource-selected workers and the sixth-response group fault. No native process
   is permitted in either mode. The script itself guards process spawning while allowing
   only the owned Python worker forks used by the scheduler.
5. Supervise only that unique diagnostic container with the recorded1200s/64MiB limits;
   preserve stdout/stderr/exit and partial progress if anything fails. Stop rather than
   changing security, image, packages or authority. Verify original deployment/stopped
   evidence snapshots after execution. Do not reuse this diagnostic as a runtime launcher.

The published startup_join.py differs from the final executed script only by an
AST-identical long-string wrap; source hashes distinguish them. The exact executed
script remains in /tmp/u4-b-k2-parallel-v1/startup-source-v2/join/startup_join.py and its
hash is in the launch receipt. The final combined helper adds only stdlib import sorting and call-line wrapping to
the executed helper, including its exceptional cleanup. Non-import AST and the import
multiset are identical; evidence/combined-format-equivalence.json binds both exact hashes.
The final formatted patch is separately applied and checked by the final host selection.

A's final startup/factorial/source-reversion results remain inherited. B independently
compared84 published raw receipts with their saved private originals and checked the
unchanged transport, result-validation tail and45 original resolver validation statements.
That integrity/AST check is not another execution of A's tests. The B final receipt records
actual private imports; source/support and environment-read completeness are separate limits.
