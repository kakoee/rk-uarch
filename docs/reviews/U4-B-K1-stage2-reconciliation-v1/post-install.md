# Concrete post-install inventory and metadata procedure — not activated

Run only after separately authorized source installation and coordinator/reviewer reconciliation,
on an ordinary independent clone containing the actual installed commit. Do not use frozen A.
The source commit must be full, real and available in Git. The reviewed base or a null value
refuses. The helper checks the complete K1 path delta from the base and all twelve postimages;
additional native/register changes require a new review binding. Other unrelated source history
is represented by the actual installed commit/tree, not silently relabelled as the proposal tree.

The proposed invocation is:

```bash
python3 -B docs/reviews/U4-B-K1-stage2-reconciliation-v1/post_install.py \
  --repo "$INSTALLED_REPO" --source-commit "$INSTALLED_COMMIT" \
  --work "$NEW_PRIVATE_WORK" \
  --python /home/jjaff/AI-infra-simulation/rk-uarch/.venv/bin/python
```

These three shell variables must be supplied from the eventual real installation; no values
are invented now. `NEW_PRIVATE_WORK` must be absent and outside that repository. The helper
archives the commit into `work/source`, keeps source read-only in containers and writes to
`work/receipts` and a separate target. It preserves receipts on failure and rejects their reuse.
The work directory is deliberately retained for review and must accompany the receipts.

1. Check exact installed postimages, complete K1 change footprint, lock, accepted tool package,
   native input hashes and real test source. Inspect the already available exact image by local
   ID. Never build, pull or start Docker as a fallback. Container calls use `--pull never`,
   `--network none`, Linux/amd64, the invoking unprivileged UID/GID, read-only source and private
   target/receipts mounts. No new hosted or runner action is performed.
2. Use the existing accepted `native-container.sh inspect` stage to record full versions,
   compare their exact receipts with the accepted package, check target installation and execute
   these two **real** commands in the exported `native/` directory:

   ```bash
   cargo metadata --locked --offline --all-features --format-version 1
   cargo metadata --locked --offline --all-features --format-version 1 \
     --filter-platform x86_64-unknown-linux-gnu
   ```

   They write `receipts/metadata.log` and `receipts/metadata-target.log`, with stderr and exit
   receipts. The mount retains the source's absolute path so workspace/source-path validation
   resolves the same files on host and container. No graph paths or resolved nodes are invented
   or rewritten. Full metadata is required for the linkage test, including the conditional
   UEFI entry; Linux-filtered metadata has a separate validation role.
3. Run the accepted container `checks` stage: fmt, clippy, deny, full debug/release listing and
   execution, exact replay listing and three fresh replay processes per mode. Use all features,
   locked/offline, x86_64 target, seed41011/cases256. Consume actual outputs through B's existing
   source/metadata/results guards. Validate 27 full-lock versus 26 Linux-selected packages,
   exact features/registry and lock checksums. Reject inventory drift instead of silently
   freezing a new list. Require the exact 28-name counters and expected replay payload hash.
4. The helper explicitly runs the following host Python selection with explicit pytest config,
   root, isolated imports, bytecode/cache suppression and `K1_METADATA` set to **this run's**
   absolute `receipts/metadata.log`:

   ```text
   native/test_register_linkage.py
   tests/unit/test_third_party.py
   tests/unit/test_third_party_patch_check.py
   ```

   Missing/invalid metadata fails; this test is not skipped, filled with roles JSON, or linked
   to A's expired `/tmp/u4-a-k1-stage2-…/outputs/metadata.json`. Host Python is not the accepted
   Rust toolchain: it only validates the actual container outputs and text/graph bindings.
5. Only after these checks pass, save `metadata-binding.json` with actual source commit/tree,
   source root, lock hash, all-features/target, both raw metadata hashes, exact image ID, tool
   receipt hashes and tool-package commit. Save `inventory.candidate.json` with that actual
   commit and observed targets/names. `source_commit` never comes from the null proposal field.
   The helper checks source bytes/mtimes afterward and keeps failures visible.
6. Re-execute the applicable fault/restoration campaign using [controls.md](controls.md), then
   present the candidate inventory, bindings, source-isolation and real failure/replay evidence
   for review. Only a later authorized B installation may replace `.github/native-k1-tests.json`.
   Retain the historical 19-test record and original 0001 identity. Source-only proposals or
   native check success do not themselves activate a workflow or close reviewer findings.

Current discovery gap: default pytest `testpaths` is tests/contract/tests/validation, so it does
not collect `native/test_register_linkage.py`; `make native-test` runs Cargo only. The existing
container inspect stage already emits the needed graph, but no live path invokes the manual
Python test with it. This proposal helper joins those steps explicitly. Neither Makefile nor
live CI is changed here. If this sequence later becomes the canonical native check entry point,
review that separate wiring and retain docs-only classification and U0024's hosted skip.

Preparation evidence after Docker restoration: native_check.py ran the exact unapplied
proposal using genuine construct.verify receipts, while linkage_controls.py exercised both
F5 mutations against real metadata. The installed-commit entry point above remains a proposal;
its source identity cannot be filled from those scratch trees. The adapter in native_check.py
also reconciles A's literal diagnostics with the historical driver's regex API. Its prefix
and suffix campaigns are explicitly separated in the receipts.
