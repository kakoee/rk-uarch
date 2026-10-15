# Exact installation selection and guarded human helper

This is a reviewable installation proposal, **not an installation authorization**. The exact
M bytes, trust mechanism, selected policy and tool/licence decisions are already accepted.
The next coordinator/Javid action is the bounded human installation release, not a repeated
semantic vote. Installed U0002 already contains the prospective selected-policy addendum;
this package proposes no further ADR edits.

[selection.json](selection.json) is the complete 32-path source selection:

- 26 additions from A: two M Python modules, twelve schema mirrors, eleven input fixtures,
  and one admission-test module, all under `contract/`.
- Three modified scripts (`__init__.py`, `u2_inputs.py`, `vendor_rk.py`), two new scripts
  (`u2_import_guard.py`, `u2_support.py`) and the new policy-test file from the six-file repair.

These 29 additions/three modifications are the entire proposed source commit. No native code,
K1 review, M runtime loader/mapper, authority record, production test profile, artifact,
current-adoption binding, ADR, workflow or oracle input is part of that selection.
The helper consumes the original published patches by their accepted hashes.

[human-install.py](human-install.py) is finalized for this source selection. It offers
`--check-only` and a separately gated `--install` mode. Read-only preview verifies:

1. Full expected HEAD/package commit, normal `main` and origin, required baseline ancestry,
   clean worktree/index including untracked paths, no hidden index flags and no unfinished Git operation. It stops
   on unrelated work rather than deleting, stashing or staging it.
2. Only review-directory changes since the audited source baseline. Any other intervening
   source/CI/contract change requires a refreshed audit, even if patch application succeeds.
   This uses Git diffs, not a whole-repository manifest.
3. Normal executable ownership/prediction hooks; no redirected hooks path. The helper never
   sets `UARCH_HUMAN` or bypasses hooks. Its own executable and identity files must match
   the named package commit.
4. Unchanged installed authority/lock files, accepted patch hashes, exact selected preimages,
   no target/path symlinks or collisions, exact patch/selection path agreement.
5. Live strict currentness; combined disposable patch application; all 32 postimages; the
   exact freshly measured support inventory; and the expected stale-artifact refusal.

After this package is committed/published, a read-only invocation is:

```bash
python3 -B docs/reviews/U4-M-policy-installation-readiness-v1/human-install.py \
  --check-only --package-commit "$READINESS_COMMIT" --expected-head "$(git rev-parse HEAD)" \
  --python /home/jjaff/AI-infra-simulation/rk-uarch/.venv/bin/python
```

`READINESS_COMMIT` is the full published commit containing the reviewed helper/selection,
not a tag or guessed future identity. The Python path names the existing checked environment;
no installation/sync is performed. The helper derives its target repository from its location.
A successful preflight authorizes nothing and performs no live installation or commit.

For **later human installation**, coordinator first checks this package and Javid supplies
an actual Git decision record with exactly these fields:

| Field | Required value |
| --- | --- |
| `format` | `uarch-M-policy-install-authorization/1` |
| `action` | `install-source-only` |
| `approved` | true, only after actual human authorization |
| `authorizer` | Javid, only from the real decision |
| `package_commit` | Reviewed published readiness commit |
| `selection_sha256` | SHA256 of this exact `selection.json` |
| `source_parent` | HEAD before committing that decision record |

No such record is supplied here. This is an installer decision record, not the future K2
registry/profile/engine authority. Coordinator authenticates the human decision and Git
provenance; a string or environment flag is not cryptographic proof of a human. The unit-test
parser fixtures are explicitly synthetic and confer no authority.

The decision must be committed alone under `docs/reviews/`, leaving that authorization commit
at HEAD. The human then uses `--install`, the same pinned package/Python arguments,
`--expected-head` and `--authorization-commit` both naming that exact HEAD, and
`--authorization-record` naming the committed decision file. Only the human supplies the
existing ownership flag in their environment. This installer must not be invoked in install
mode by an agent.

After all preflight checks it applies both patches together with `git apply --index`, checks
all postimages and the exact staged set, then makes one normal local source commit **S**.
It checks the parent/path set and clean post-state, emits S/tree/parent, and **stops**.
It has no push, freeze, generation, adoption or test-activation operation. If a command or hook
fails, preserve the state and diagnose it; the helper never cleans up by discarding work.
Do not rerun over a partial/already installed selection. No concurrent source writer is an
explicit premise; reserve the installation window before invoking it.

Hold S locally. Its stale-artifact refusal is expected but makes S unsuitable as the published
main tip. The subsequent separately authorized lifecycle is in [lifecycle.md](lifecycle.md).
The helper's installation branch remains unexecuted; preview and refusal checks establish
preparation readiness only.
