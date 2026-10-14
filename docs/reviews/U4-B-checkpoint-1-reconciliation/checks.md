# Coordinator-executed bounded checks

Published target: `dd75b7c860ed57ec1f03c9705378cbde467a6d4e`. Private export: `/tmp/u4-b-reconcile-uxnh6zxb/export`.
Applied only the reviewed repair and A's early M patch in this disposable export:

- Repair SHA256 `c238574b284ebecb6f0f1253922ce01af87259f0187aad38bcda628757e8fe6b`.
- M SHA256 `3e47b970de619b013b8d46d754e9451c604d010b2763e5a0cfce9ff9d755a63b`.

Used the existing coordinator CPython3.12 environment, no dependency installation.
PYTHONPATH/MYPYPATH/VIRTUAL_ENV/UARCH_HUMAN were absent, bytecode and pytest cache writes
were disabled. Pytest used explicit export config/root; the inventory probe used explicit
export sys.path entries and checked module origins. Patch destinations were checked before
running tests. Hypothesis and pytest temporary directories were outside the exported tree.

| Executed check | Result |
| --- | --- |
| B standard-library arithmetic unittest discovery | 6 passed |
| B CI guard unittest discovery | 4 passed; synthetic logs/sources only |
| Pristine exported vendor --check | Passed |
| Public policy, script-entry and M prototype pytest selection | 130 passed, 1 skipped, 36.81 seconds |
| Skip identity | Real new-policy human generation/adoption absent; not a synthetic substitute |
| Combined proposed inventory | 56; broad101; all56 path/hash pairs equal B's published audit |
| Module origins | Patched exported scripts and mapped carrier, not live editable source |
| Export source preservation during combined tests | 1737 files unchanged in bytes and mtimes |
| Combined vendor --check | Expected exit1: input support inventory changed |
| Ruff on the patched export | Passed |

Commands from the private export, using the existing coordinator Python interpreter:

```sh
python -B -m unittest discover -s docs/reviews/U4-B-verification-inputs-v1 -p 'test_*.py'
python -B -m unittest discover -s docs/reviews/U4-B-native-ci-v1 -p 'test_*.py'
python -B -m pytest -c pyproject.toml --rootdir . -p no:cacheprovider \
  --basetemp /tmp/u4-b-coordinator-test-temp -q -rs \
  tests/unit/test_u2_support_policy.py tests/unit/test_vendor_script_entry.py \
  contract/tests/mapped/test_admission.py
python -B scripts/vendor_rk.py --check
ruff check --no-cache .
```

The initial coordinator attempt incorrectly supplied PYTHONPATH and gave129 passed,
1 failed,1 skipped: the environment guard caught it. It is not credited as a valid run
or a B finding. A new clean export with that variable removed produced the results above.
Raw logs and receipt remain under `/tmp/u4-b-reconcile-uxnh6zxb`; no source-wide manifest or copied checkpoint
is published. No full suite, new fault campaign, mypy rerun, native execution, generation,
adoption or hosted CI pass is claimed. Author-only results keep their original attribution.
