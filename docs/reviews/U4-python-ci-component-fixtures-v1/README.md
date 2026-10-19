# Python CI component-fixture repair

Subject: published main `71a1c75d20bf60493952be6c96c768c64a51f7eb`;
failed GitHub run [39175117845](https://github.com/kakoee/rk-uarch/actions/runs/39175117845).
The Python job reported 16 failed, 1695 passed, 36 skipped and 277 deselected.

## Causes and changes

- Eleven failures came from the synthetic component payload fixture using a frozen
  candidate consumer inventory against current source, including the newly added
  `runtime_resources.py`. The fixture now declares its own current-source inventory,
  explicitly synthetic, with no binary binding or execution authority. Published
  candidate bindings and the production closure checks are unchanged. Existing
  missing/wrong/stale-source controls still run.
- Three failures came from the startup fixture collecting Ubuntu stdlib symlinks
  outside its declared import roots: `sitecustomize.py` resolves into `/etc`, and
  the linker `libpython3.12.so` resolves into `/usr/lib/x86_64-linux-gnu`. The fixture
  now includes only files resolving within its declared project/stdlib roots.
  Launcher roots, source checks and import behavior are unchanged.
- Two failures came from historical installation hashes applied to B's deliberately
  changed `observations_v3.py` (the Stage 2 matrix-order check). An explicit test-only
  transition records that checker change and the two changed identity tests. The
  installed helper, historical records, ADRs and runtime consumer pins remain
  unchanged. New controls reject missing/extra transitions, a wrong preimage,
  authority, a wrong base record and a modified checker.

The new identity record is `tests/fixtures/component_current_identity.json`.
Its replacement preimages are derived from the unchanged installed binding chain;
its postimages and added test-helper identities are literal reviewed hashes, not
hashes adopted dynamically during verification. No self-hash cycle is introduced.

## Verification

- Reproduced the inventory and installation failures before correction.
- Reproduced the original benign startup failure on Ubuntu system CPython 3.12;
  the corrected benign control passes on both system and uv-managed Python.
- Initial affected selection: 74 passed.
- Expanded affected selection in a clean tracked export: 126 passed in 41.28 s.
  Counts overlap; they are not additive.
- Clean tracked-export Ruff passed; both CI-form mypy checks passed (92 and 39 files).
- Strict vendor/currentness check passed in the clean export.

The two startup substitution probes were not rerun here; only their common benign
fixture setup was exercised. A-F3 remains deferred; this fixture portability fix
is not an adjudication of startup integrity. No native build, container campaign,
public execution, authority, protected-source installation or historical evidence
change occurred. Full-suite and hosted-CI completion are not claimed.

## Lane integration

No runtime source or candidate consumer record changed. A and B should integrate
this ordinary test repair normally. The two changed files under `validation/` are
tests, but a future BuildInputs inventory that includes all validation tests must
record their new bytes. Existing build identities and their evidence remain valid
only for their original frozen source; this change does not rebind those binaries.
