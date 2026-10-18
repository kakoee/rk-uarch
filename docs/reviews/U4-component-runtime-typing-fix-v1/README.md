# Component runtime CI typing correction

The reported production CI failure has one cause: the nested `population` helper lacked
annotations. The live correction is `def population(t: int) -> int:`. Its calculation,
call sites and validation behavior are unchanged. The ASTs match after removing the
added annotations. Base: `56bbc830a91c53bf0281220c02b2394f3a8a34fb`.

## Runtime source identity

[transition.json](transition.json) binds the exact old/new source bytes.
[consumer-bindings.json](consumer-bindings.json) is an additive prospective 51-file
consumer binding. Only `validation/component/runtime_checks.py` differs from B's
preparation-v2 binding; its other 50 entries match exactly. The old record remains
unchanged. Real `verify_sources` refuses the old binding and a tampered prospective
binding, and accepts the exact new binding in the isolated source export.

A/B should use this published source correction instead of applying A's duplicate
`B-consumer-types.patch`. The final build/runtime package must explicitly incorporate
this transition. Existing payloads, build identities, binaries and evidence keep their
original identities; this is not a claim that they already bind the corrected source.
No builder pin, authority or deployment has been changed. During integration, A's final
handoff `8356856` appeared on the actual remote and was merged normally. Its existing
evidence archive is unchanged; this fix adds no new native evidence.

## Additional CI failure and unapplied correction

The second CI command, `mypy --no-explicit-package-bases contract/tests`, exposes
37 errors in three installed issue-edge tests. These were hidden behind the first
failing command in CI. [contract-tests-typing.patch](contract-tests-typing.patch)
adds test/helper annotations and explicit types for heterogeneous fixture dictionaries.
It also updates only the three corresponding test hashes in
`validation/component/issue-amendment-binding.json`.

All four live files remain unchanged. The exact pre/postimages are in
[protected-test-identities.json](protected-test-identities.json). No structural
validator, independent checker, fixture, schema, native implementation or ADR changes.
The original review packages and their historical hashes are preserved.

`CLAUDE.md` says: "Agents propose and stop on contract/, tests/golden/expected/,
CLAUDE.md, docs/decisions/." Human installation is therefore required for this patch.
After approval, apply the four paths together and commit them with the normal human
protected-file workflow. Do not update the binding alone or rerun artifact generation.

## Executed checks

- Production CI mypy command: 92 files, passed after the live annotation fix.
- Existing runtime checker/campaign/selection tests: 28 passed.
- Contract CI mypy command on the unapplied correction: 39 files, passed.
- Corrected contract tests: 15 passed; installation/selection identity tests: 21 passed.
- Clean tracked-export Ruff and strict vendor currentness: passed.
- Prior/new/tampered runtime binding controls and isolated import origin: passed.

[checks.json](checks.json) separates live-source verification from the unapplied
proposal. No full suite, native execution or hosted CI polling was performed.
The contract CI command remains failing on live main until the protected proposal is
installed; the production CI command reported by the user is corrected.

## Approved installation and peer join

Javid approved publication and the exact four-file correction with `yes`; see
[acceptance.json](acceptance.json). B independently published the identical runtime
annotation at `097577b`. Its prospective consumer-bindings-v3 files map is identical
to this package's 51-file map; both histories were merged normally.

[human-install.py](human-install.py) defaults to read-only preflight. With the human
`UARCH_HUMAN=1` environment and `--install`, it verifies the pinned helper and approved
proposal, checks the exact four preimages, tests a clean private export, then applies
and commits those four paths using normal hooks. Unrelated untracked review files
are preserved. It never pushes or runs native jobs. Return its commit receipt for
coordinator publication. No new decision is requested.
