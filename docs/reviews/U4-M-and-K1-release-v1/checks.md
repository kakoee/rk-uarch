# Coordinator final reconciliation of A and B

**Subject:** published `1a56ff22068ded35cac944fd8c1de8ffde9cc86d`. A's exact M
subject remains `111b24b`; tool package remains `83a9a14`. No new blocking issue found
within these bounded checks. This is coordinator reconciliation, not an independent
adversarial verdict or native qualification.

## Newly executed

Used a private `git archive` export of the subject, applying only the exact M patch
(d392b243...) and unchanged selected repair (c238574b...). Both patch digests verified.
Existing coordinator Python/tools were used; no installation. Cleared PYTHONPATH,
MYPYPATH, VIRTUAL_ENV and UARCH_HUMAN; disabled bytecode and pytest cache; temporary
pytest/Hypothesis data outside the export. Asserted mapped and policy imports originate
inside the export before invoking pytest with explicit config/root.

Combined selection:

```text
tests/unit/test_u2_support_policy.py
tests/unit/test_vendor_script_entry.py
contract/tests/mapped
docs/reviews/U4-B-final-reconciliation-v1/test_fixture_inputs.py
docs/reviews/U4-B-final-reconciliation-v1/test_ci_host_guard.py
```

Result: **195 passed, 1 skipped** in 91.73s (B's 173 + 22 selections together).
The sole skip explicitly says real new-policy human generation/adoption has not occurred.
No skip is converted to acceptance. This reruns the final clock/trust controls, resident
D02/D14 admission and independent arithmetic, and synthetic host/container guard controls;
it runs no native kernel or container.

- Recomputed policy inventory: 56 entries, exact path/digest equality with B's final
  `audit-1.log` inventory.
- Patched direct `scripts/vendor_rk.py --check`: expected exit 1,
  `input support inventory changed`. This is not currentness success or a waiver.
- Live unpatched `scripts/vendor_rk.py --check`: pass, current snapshot compatibility verified.
- `bash -n` on B's host/container scripts: pass.
- `ruff check --no-cache .` on the patched export: pass.
- Proposed one-file ADR patch applies cleanly in the export and matches its declared
  postimage SHA256. Protected live files were not edited.

Scratch diagnostics were retained locally at
`/tmp/u4-b-final-coordinator-f5x2zhxj/receipt.json`; the directory is not a publication
or runtime dependency. Tests used the existing `.venv` Python, explicit `-c pyproject.toml
--rootdir . -p no:cacheprovider --basetemp <outside> -q -rs`. Module origins were selected
inside Python, not by inherited PYTHONPATH.

## Inherited and still unexecuted

A's upstream tool/archive verification, its 252-test receipt, B's source-preservation
snapshots, B's 30 scope/prompt tests and earlier fault reverts remain their evidence.
The prior coordinator record separately reproduced 65 mapped tests, schema freshness
and both CI-form type checks. Those are not new runs in this receipt.

No full suite, new upstream authenticity/licence analysis, image build/run, native build,
real Linux native CI, server work, performance measurement, generator/adoption or independent
review was executed here. No hosted CI was polled. Tool/checksum consistency and synthetic
log controls cannot establish that the proposed image actually builds or the kernel works.

## Decision disposition

The final audit clears the concrete dependency-audit prerequisite for presenting M's exact
bytes. D02/D14's explicit resident state resolves the prior catalogue conflict; qualifying
installation/authority and runtime results remain later first-use steps. B has supplied
reviewable CI commands, but final image/cache/discovery/test names are post-acceptance
construction outputs. No requirement for full tables or self-hosted registration is added.

[next-decision.md](next-decision.md) separates M/trust and migration preparation from
K1 tool/licence and private implementation release. The selected policy is already a U3
decision; this packet does not ask to choose it again. The protected ADR patch remains
unapplied and the packet records no user acceptance.
