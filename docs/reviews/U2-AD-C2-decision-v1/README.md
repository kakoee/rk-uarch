# U2-AD-C2-decision-v1 — ready for Javid's decision

Status: proposed, not accepted. The active guard is unchanged. AD-C1 test isolation is already reconciled separately.

Recommend option A: accept the exact [guard patch](option-A.patch) in contract/tests/vendor_support.py. It permits only the unaliased `from importlib.resources import files` in `src/rkuarch/provenance/proof_raw.py` when the complete file hash is `9f47439f058417e24fcf2891f996d7b9428a69c4c8825c5e3188936c6d659c15`. All other import, dynamic-call and vendor-string checks still apply. This is a source guard with existing stated limitations, not a hostile-environment security boundary. Even comment changes invalidate the exception and require renewed review.

Exact guard before: `d5a59904099a3a9729def3cb2e1bb752a2546d006027a366e6d7e512ebf00dfc`.
Exact guard after: `4892004b408f904ba3e9b1945dac8cd610c4523c458e47edb25f2d9022d31d60`.
Exact patch SHA256: `67f781e84a8c5f554b24a5226b5e160ed38c4608a502dac2362ecc1abe72316e`.

The loader's existing calls read six local JSON schema members; it imports no rk source. Its helper is not claimed to enforce a general filename allow-list. No production or packaged schema bytes change with option A. Option B duplicates 35,624 bytes of schema text in runtime source and changes generator-bound support; it adds maintenance and lifecycle work without a demonstrated need here.

Coordinator independently applied A only in temporary files: the complete current production tree passes the proposed guard, and 16 isolated positive/negative cases match expectations, including comment drift, foreign package, dynamic package, alias, directory change, unrelated resource import, rk/scripts imports, dynamic execution and vendor strings. The complete unchanged production loader imports and decodes all six exact schemas from relocated directory and ZIP packages. See ../U2-AD-reconciliation/option-A-independent-checks.json. These checks complement B's 21 prototype cases; counts overlap and are not summed. No wheel was built: hatchling/build/pip are absent from the existing venv. Installed-wheel validation remains pending; no dependencies were installed.

Approval authorizes the existing B session to apply only this exact guard patch, add durable focused regression tests for the reviewed exception and retained prohibitions, and return a tested checkpoint. Production changes, blanket importlib exceptions, fixture relabelling, new generation/adoption, commits, pushes and closure are excluded. Coordinator will review the resulting test additions and inventory before integration. Use B-handoff-after-approval.txt only after this decision is accepted.

Freeze treatment: seven AD-C1 supplemental test members already changed and 23 test/helper/received-data files were added, recorded in ../U2-AD-reconciliation/post-AD-C1-source-SHA256SUMS (322 paths). A changes one additional supplemental member and later adds reviewed regression tests; all 84 generator-bound support paths and the approved input digest remain unchanged. The original 299-path freeze and human generation pair remain immutable historical evidence. Record a separate current supplemental inventory; do not rewrite or claim exact equality to that old freeze. This test-only reconciliation does not authorize new generation or a different artifact.

Approval is needed because the repository's CLAUDE.md says “Both humans: contract/, tests/golden/expected/, CLAUDE.md, docs/decisions/.” and “Agents propose and stop on contract/, tests/golden/expected/, CLAUDE.md, docs/decisions/.” The earlier bounded AD-C1 authorization covered its test corrections; it explicitly held this new guard exception at proposal stage. This request concerns that exact remaining exception, not a repeat approval of artifact adoption.
