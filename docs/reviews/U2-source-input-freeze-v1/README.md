# U2-source-input-freeze-v1 — ready for Javid's decision

Status: **PROPOSED; not yet accepted.** Coordinator reconciliation is complete.
Recommendation: accept these exact source/input bytes for the next human-only
created/verified-identical generation pair. This acceptance does not adopt an artifact,
accept real runtime outcomes, authorize a commit/push, or close U2.

## Exact review subject

- Input manifest SHA256: `81df43c063396c89bd3333f43957c71efc7087cfa65b2a401177f2227fca8898`.
- Source manifest SHA256: `8457d0607baf0af08c0b6d1c6eead00e141e778f6fd501d8869d9ae5eaadf443`.
- Source inventory:299 paths, including all84 generator-support paths; exact inputs
  in inputs/. B's original proposed package is preserved separately.
- Upstream pin: `1e5706e0ebfcc67c1a7333079a35b75f693e9963`.
- Execution tree: `/home/jjaff/AI-infra-simulation/rk-uarch-u2-integration`.
- Existing external locked environment: `/tmp/rk-sim-u1-jjaffari-1e5706e`.
  CPython3.12.14; exact distribution inventory and pinned lock digest are recorded.
- New candidate destination: `docs/reviews/U2-real-generation-v1/candidate` in that
  integration tree. The generation directory is currently absent.

[Inventory](inventory.json), [source hashes](source-SHA256SUMS),
[input manifest](inputs/SHA256SUMS), [environment preflight](oracle-environment-preflight.json),
[executed coordinator preflight](coordinator-preflight-result.json).
Two existing integration test-path adaptations differ from B's supplemental test list;
they are explicitly recorded, tested, and frozen at integration's actual hashes.
All production and84 generator-support bytes match B's final full synthetic run.

The matrix keeps864 retained oracle rows plus144 H1 BF16/BF16 rows, seven accepted
component/precision pairs, original nominal counts and .55 retained execution inputs,
and the accepted H1 claim/stub1.0 input. Four direct refusal outcomes must be observed
from the real oracle. Synthetic expected values/reviews are not adoption candidates.
H1 physical96 successes/48 capacity failures and864 physical not_run cases remain
explicit; this freeze does not supply missing physical hardware or waive any exit.

## Why this decision comes now

The reviewed renderer index is integrated. The current relevant integrated suite has
413 passes with zero skips; static/schema checks pass. Full synthetic hidden/STUB,
repeated bytes, prepared replay through package/render and capability refusals have
completed. Coordinator independently reran the full saved STUB render and compared
all saved repeat/replay bytes. See [recheck](../U2-RI-coordinator-recheck.md).
Two pre-refresh artifact gates remain active as expected. Actual oracle agreement
and real direct-refusal evidence remain unexecuted.

U0002 requires freezing reviewed generator/supporting code and complete inputs
before the human two-run pair. Your earlier acceptance kept generation/adoption,
commit/push and closure separate. This is the concrete freeze decision under that
existing lifecycle, not another policy change or an independent final review.
No still-planned fingerprint-changing implementation remains for this bounded
checkpoint. A later required source/input fix invalidates this freeze and requires
reconciliation/new inputs and a fresh pair. Do not reuse or relabel different-input runs.

## After acceptance: Javid's separate execution step

The [human-only script](human-generate.sh) is prepared and syntax checked, but **has
not been executed**. It rechecks source/input/environment identities, creates the
absent review directory, executes the same generator command twice in fresh
processes, and requires created then verified-identical. It records both logs,
strict inspection, the complete semantic difference and raw candidate-manifest digest.
The [preflight](preflight.py) executes only read-only validation and package metadata.

After explicitly accepting this freeze, Javid can run:

```bash
bash /home/jjaff/AI-infra-simulation/rk-uarch-u2-integration/docs/reviews/U2-source-input-freeze-v1/human-generate.sh
```

If any step fails, preserve the directory and logs and return for reconciliation;
do not delete/reuse the destination, install dependencies, edit metadata, alter inputs
or weaken gates to continue. The script intentionally refuses a reused run directory.
Then return the created/verified-identical logs and candidate manifest digest to the
coordinator. Complete differences and real outcomes must be reviewed before a separate
explicit candidate adoption decision. Existing adopted artifacts are untouched.

Commit and push are still separate; no development-branch push or mandatory PR.
Main remains the publication branch, workers remain preserved, and all work is still
uncommitted. Hashes identify bytes; they do not put them in protected branch history.
Final independent reviews, actual runtime/B-F16 exits, U0021 published-commit Ubuntu
CI/WSL2 cold clone and sprint-closure approval remain outstanding. No simulator-
performance-host or real-evidence eligibility approval follows from this freeze.
