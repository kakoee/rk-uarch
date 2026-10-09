# A RR-C1 ordering correction — coordinator handoff

The exact proposed one-line sort is implemented on `u2/analytic`, baseline
`7aab97d35ca554b0477ac5719dfa4e5306f8bbab`. Work is uncommitted. This corrects the
ordering of provenance conditions only. Public signatures, workload/count/timing
algorithms, schemas, hardware, rendering, thresholds and evidence policy are unchanged.

`src/rkuarch/table/build.py` SHA256:

- Before: `ece53ed1bcb1ca02fdcc450ff4b1ee99da321f699fadcb5b446ea07f17fe4acc`.
- After: `c91880cb7ca8977e6ecf491109a8459394af39c6efab82714d34c8cdd895f9e6`.

The source change sorts `sourced_leaves(b.hardware_spec)` by its path before the
existing stipulation filter. It changes the list order and dependent table identity;
it preserves every included sourced value and all other table fields. No extra
production change was required. `changes.patch` is the Git diff against the stated
baseline plus the new test's Git no-index addition. `changed-paths.json` is the exact
bounded proposed local commit list, not a whole-worktree manifest.

## Tests first and affected checks

`tests/integration/test_u2_a_condition_order.py` is durable regression coverage.
It uses the actual accepted H1 `npu-l4.yaml` hardware and a small workload. Its
registry/review companions are explicitly synthetic test scaffolding, with no real
evidence eligibility. An independent JSON walk checks all 59 condition paths and
complete sourced values, including rationale, units and nulls. Count equality also
rejects duplicates; dictionary equality alone would not suffice.

The saved-input cases cover canonical JSON, recursively reversed mappings and
recursively rotated mappings. Array order stays intact. They retain hardware and
bundle identities, replay captured results with prepare/capture/analytic producers
trapped, compare rows, complete provenance, self-consistent table identities,
complete canonical table bytes and package equality, then exercise public write
and offline load and compare every saved companion byte and exact file set.

Before the source change: **3 failed / 1 passed**, specifically all three complete
table byte comparisons failed; condition membership/values passed. After: **4 passed**.
`tests-first.json` records the exact baseline source and final test hashes;
`baseline-final-tests.txt` is the matching red run. `baseline-tests.txt` is the earlier
run before test-only formatting, with the same three failures. No product behavior
was changed to make scaffolding pass.

The separate affected selection passed **108 tests**, covering existing table/replay,
prepared-input, shared loader/artifacts and resolution sessions. Both selections have
zero skips. Ruff passed on the production/test paths; mypy passed across 62 source
files. `git diff --check` passed. Exact commands, environment, hashes, timings, exits
and per-command logs are in `checks.json` and its named siblings. No full-suite or
full revised-input report exit is claimed.

## Actual complete H1 captured-result rebuild

Final observations are recorded in `actual-replay.json` and `actual-replay.log` by
`actual_replay.py`. This independent execution uses B's received actual 24-row package
at `/tmp/u2-b-real-report-exits-v1-xn5pjr8z/outputs/report/table.json`, the existing real
report context and public offline loader/builder. It does not use the tiny test's
synthetic reviews or call a synthetic reference builder. Its independent condition
membership helper is shared with the durable test, not its review fixture.

Preparation, capture and analytic execution entry points are trapped before loading.
The received prepared bundle is saved canonically in a new `/tmp/u2-a-rr-c1-*`
directory, loaded by the public prepared-input loader, and rebuilt using the received
jobs/results, once with YAML-order hardware and once with canonical saved hardware.
No table/report files or adoption outputs are written over the received package.
The small receipt records phase timings, received/result/context identities, exact
canonical table digest and the assertions actually completed. Both complete builds
passed: 24 rows (also identical to the received rows), all 59 exact conditions,
complete provenance, complete package equality and byte-identical canonical tables.
The historical table differs only in condition ordering and its dependent hash.

These are captured-result rebuilds, not new analytic engine execution or hardware
measurement. Full revised-input report render/repeat/replay, capability checks and
all final exits remain a later B/integration step after reviewed source/input refresh
and artifact adoption. Estimates are unchanged; local validation seconds do not
substantiate an engineering-hour revision.

## Strict lifecycle and preservation

`entry.json` verified all 84 support files before the source change. The separate
`support-lifecycle.json` verifies the same exact inventory afterwards: only
`src/rkuarch/table/build.py` differs; all other **83 files are unchanged**. It actually
calls `scripts.u2_inputs.load_inputs(..., check_support=True)` and requires this exact
expected refusal:

`input support changed: src/rkuarch/table/build.py`

That expected refusal is recorded separately from regressions. The verifier first
validates the old input file inventory and bytes. No support check is disabled; no
fingerprint is edited or silently rebound. The public captured-report loader and
builder check captured identities/closure; they do not authorize consumption of the
old frozen inputs with newly changed support. Both boundaries remain intact.

Historical accepted input digest remains
`81df43c063396c89bd3333f43957c71efc7087cfa65b2a401177f2227fca8898`;
historical adopted MANIFEST remains
`2d15afd7dd80124f70d387bc7cde4addda29162cd49370d40da7b99830709b44`.
Existing generation/adoption records remain historical. After reconciliation, the
coordinator prepares the exact revised freeze for Javid. U0002 still requires two
human generation runs and separate explicit candidate adoption. This source fix is
not generation/adoption authority or a policy amendment.

Prior archives, other worktrees and B outputs were read only. No bulk checkpoint
copy or whole-worktree source manifest was created. The new evidence is small;
received bulk output stays in place. `preservation.json` records bounded tracked/index
checks and hashes of the specific received records used here; it does not claim to
rehash every historical archive. No cleanup was performed.

Proposed local commit message:
`fix(u2): stabilize table provenance condition ordering for saved replay`

Proposed paths: `src/rkuarch/table/build.py`,
`tests/integration/test_u2_a_condition_order.py`, and the exact small evidence paths
listed in `changed-paths.json`. Stop uncommitted for coordinator reconciliation.
No staging, commit, push, main integration, tag, oracle generation/adoption or closure.

## Executed complete rebuild result

Both table content identities: `sha256:200ca0f703feb341e3871ad3a1f897ac45cb1e42f270d10384ea31cdcafbd554`.

Canonical complete table bytes: 359,587; file SHA256
`8c06dbc992f02bbfeee9182394b235dde1b588b4d040034400de9e3144ad47dd` (computed from the complete in-memory bytes,
not written over an adopted artifact).

| Executed phase | Seconds |
| --- | ---: |
| public_offline_loader | 85.601 |
| public_saved_prepared_loader | 0.150 |
| public_yaml_order_build | 99.649 |
| public_canonical_saved_build | 89.825 |

Total observed run: 275.283 seconds; exit0. This is an independently
executed A captured-result rebuild, not a re-labelled coordinator/B log. Preparation
and analytic producers remained trapped. No full revised-input report was rendered.
