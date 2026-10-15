# U4-K1-KI-C1-formatting-v1

**Proposed exact delta; source publication is held.** The approved twelve-file K1 installation
was committed locally as `63ca8bec5a4ac1d7dcf87290a5cf080c846de66d`, but full-tree Ruff found
one E501 error in its reviewed Python guard test. The prior approval requires reconciliation
before changing any reviewed bytes. No other code change is proposed.

Approve [KI-C1-formatting.patch](KI-C1-formatting.patch), SHA256
`6715d80022a3dae49088ab6787fe083743ce5fbf35beb1152b509b94cfa829e8`:

- Only `tests/unit/test_third_party_patch_check.py` changes: wrap its 106-character
  parametrization decorator onto three lines.
- Old SHA256: `85c5590b7eccd3265b893e33458f1d94250dba4f81fa8af4d6bb6a90ec3737cb`.
- New SHA256: `26a882fdb9c0930864e47c88dae36c571085c614c64dd425a1cdbcb66f4c8762`.
- Python ASTs are identical, including all seven mutation values. Full-tree Ruff and all
  eight affected tests pass in the disposable preview. No assertion, policy or Rust changes.

After approval, make a separate one-path local commit with normal hooks, message
`style(test): wrap reviewed K1 guard parametrization`. Preserve the original reviewed commit.
Record the new hash as a narrowly approved exception to the historical B postimage binding;
never rewrite the historical subject or independent review. Use a fresh, explicit binding
for B's installed-source helper that differs only in this approved test-file hash, retaining
all eleven other exact postimages, lock, tool pins, target and accepted image requirements.

Re-run installed-source checks with that binding and the new commit so metadata and the
inventory candidate identify the final source. Rust fault evidence from the parent remains
attributed to that parent; exact unchanged native bytes justify retaining it rather than
claiming a new campaign. Confirm strict currentness, full lint and tested source isolation.
Then perform the already authorized separate normal push, preserving peer history, and
return B's concrete inventory candidate for review before replacing the live 19-test record.

K1 remote/performance qualification, K2, infrastructure actions, live inventory replacement,
sprint closure and tagging remain outside this approval. Do not poll hosted CI.
