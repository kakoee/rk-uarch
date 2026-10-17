# Reproduce the exact private proposal

From a checkout containing this package and its pinned preparation base, use the existing
Python 3.12 environment. This creates a new private directory and verifies all preimages,
23 postimages and nine activation inputs. It does not install protected changes.

```sh
.venv/bin/python -I -B docs/reviews/U4-A-component-stage2-v1/reconstruct.py /tmp/component-stage2-review
.venv/bin/python -I -B docs/reviews/U4-A-component-stage2-v1/isolated.py /tmp/component-stage2-review pytest -q tests/unit/test_u4_a_component_mapper.py tests/unit/test_u4_a_mapped_loader.py tests/unit/test_u4_component_mapper_v2.py contract/tests/mapped validation/component -m 'not native'
```

The executed final affected result is 488 passed, two explicit human-work skips and one
native deselection. Default discovery uses pyproject.toml's existing tests/contract/tests/
validation roots. To inspect activation without running other tests:

```sh
.venv/bin/python -I -B docs/reviews/U4-A-component-stage2-v1/isolated.py /tmp/component-stage2-review pytest --collect-only -q -m 'not native and not nightly and not silicon'
```

[discovery.json](discovery.json) lists exact candidate collection IDs: 233 nodes across
11 paths. No test-time copies or import/discovery waivers are used. The origin-checked runner
removes editable-install project paths, changes to the private root and verifies loaded
project module origins after execution.

For schemas, use the same runner with `module uarch_contract.generate --check`,
`module uarch_contract.generate_rotary_v2 --check` and
`module uarch_contract.generate_mapped --check`. From the private root use the existing
venv's ruff and mypy binaries, with PYTHONPATH/MYPYPATH unset for mypy and caches outside Git.
The exact checked surfaces and log hashes are in [verification.json](verification.json).

The successful behavioral run used B's 7b972d0 preparation commit. The final preparation base
also contains the stable-import-only correction to B's freeze_selection.py and final author
reports. All 23 source/test/schema/text bytes and all activation inputs remain identical;
full-tree lint passes on the latter. No combined-suite replay was performed for that
proposal-helper/document-only change. The source patch itself remains 81b81c6c…2bdebe3.

Historical evidence remains attributed to its original source. Synthetic carriers, fixture
profiles and mutation controls are never native results. Human workings and execution gates
are still separate, and this reconstruction grants no protected installation permission.
