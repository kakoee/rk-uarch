# Coordinator checks on the final A proposal

## Exact subject and environment

- Git export: `111b24b0d8a41280431a35b9e3115d93630b6d24`.
- M patch SHA256: `d392b24304a5f63fe69679ce991c5dbf2f742e95fee867a82dec2b0eef3a25e3`.
- Applied only that patch to a disposable export; all 26 postimage hashes matched
  `U4-A-M-package-v1/package.json`. Live protected files were untouched.
- Used the coordinator's existing `.venv` tools; no installation. Removed PYTHONPATH,
  MYPYPATH, VIRTUAL_ENV and UARCH_HUMAN from subprocess environments. Fresh mypy caches
  and pytest/Hypothesis temporary data were outside the export; bytecode disabled.
- Local scratch receipt/logs: `/tmp/u4-a-final-check-wcl275bc/receipt.json`. These temporary
  files are diagnostics, not durable publication dependencies.

## Executed results

From the patched export root, using the existing Python/tool executables:

| Check | Result |
| --- | --- |
| `pytest -c pyproject.toml --rootdir . -p no:cacheprovider --basetemp <outside> -q contract/tests/mapped` | 65 passed |
| `uarch_contract.generate_mapped --check` | fresh |
| `uarch_contract.generate --check` | fresh |
| `uarch_contract.generate_rotary_v2 --check` | fresh |
| `mypy --cache-dir <fresh-outside> src contract/uarch_contract scripts` | 80 files, pass |
| `mypy --cache-dir <fresh-outside> --no-explicit-package-bases contract/tests` | 32 files, pass |
| `ruff check --no-cache .` | pass |
| `python -B scripts/vendor_rk.py --check` | expected exit 1: input support inventory changed |

Schema modules were invoked via runpy with the export's `contract`, `src` and root
prepended to sys.path and `--check` in argv. No PYTHONPATH/MYPYPATH was supplied to mypy.
The export excludes pre-existing untracked reviewer scripts in the live coordinator clone.

Additional read-only tool-package checks:

- `sha256sum -c package.sha256` from the tool package passed its declared entries.
- All five `native-inputs.sha256` entries match their proposed installation sources:
  workspace manifest, crate manifest, lock, toolchain and deny configuration.
- Cargo.lock contains 27 external registry crates.

These establish internal package consistency, not upstream authenticity, legal acceptance,
image executability or native correctness. No full suite, 252-test reproduction, import-linter
rerun, enforcement-disabled mutation run, combined repair audit, image/native build,
network tool verification, generation/adoption or hosted CI was performed in this check.
Those results must not be inferred from the author receipts or successful local static checks.
