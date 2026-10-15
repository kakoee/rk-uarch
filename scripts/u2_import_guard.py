"""Proposed closed top-level import namespaces for U0002 tooling, not a sandbox.

Uses only startup-loaded os/sys before other imports. Reserved repository namespaces
are explicit; a new importable top-level name needs review, not an output-equality
exception. Nested consumer modules remain independent unless reached by support.
"""

import os
import sys

# Exact names/types prevent a module/extension replacing an approved directory.
DIRECTORIES = {
    "": frozenset({"scripts", "src", "contract", "tests", "validation", "docs", "hw",
                   "measure", "native", "third_party", "containers"}),
    "scripts": frozenset({"hooks"}),
    "src": frozenset({"rkuarch"}),
    "contract": frozenset({"uarch_contract", "tests", "schema", "fixtures", "vendor",
                           "provenance"}),
}
FILES = {
    "": frozenset(),
    "scripts": frozenset({"__init__.py", "vendor_rk.py", "u2_inputs.py", "u2_support.py",
                          "u2_import_guard.py"}),
    "src": frozenset(),
    "contract": frozenset({"__init__.py"}),
}


def check_import_roots(root: str | None = None) -> None:
    """Refuse new importable names under ROOT/scripts/src/contract, before bodies run.

    Supported bootstrap is normal CPython >=3.12 with frozen os and builtin sys;
    arbitrary startup hooks, hostile interpreter/environment and races are not covered.
    """
    if (
        sys.implementation.name != "cpython" or sys.version_info < (3, 12)
        or os.__spec__ is None or os.__spec__.origin != "frozen"
    ):
        raise ValueError("unsupported import-guard bootstrap")
    root = root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for relative, directories in DIRECTORIES.items():
        directory = os.path.join(root, relative)
        if not os.path.isdir(directory):
            continue
        for name in sorted(os.listdir(directory)):
            if name == "__pycache__" or name.startswith("."):
                continue
            path = os.path.join(directory, name)
            is_directory = os.path.isdir(path)
            stem = name.split(".")[0]
            importable = (is_directory and name.isidentifier()) or (
                stem.isidentifier() and name.endswith((".py", ".pyc", ".so", ".pyd"))
            )
            if not importable:
                continue
            allowed = name in (directories if is_directory else FILES[relative])
            if os.path.islink(path) or not allowed:
                raise ValueError("unreviewed import name: " + os.path.relpath(path, root))
