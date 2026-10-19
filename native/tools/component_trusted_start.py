"""Private prospective launcher: python -I -S -B THIS MANIFEST SHA256 MODULE.

The externally pinned interpreter, this file and its bootstrap stdlib are the TCB.
This is not an in-process sandbox. Activation must supply an immutable manifest,
roots, interpreter/DSOs and launcher; a caller-chosen digest is not authority.
"""

import hashlib
import importlib
import importlib.machinery as machinery
import importlib.util
import json
import sys
import types
import typing as _typing
from pathlib import Path


def require(condition, message):
    if not condition:
        raise RuntimeError("trusted startup: " + message)


def main():
    require(
        sys.flags.isolated and sys.flags.no_site and sys.flags.dont_write_bytecode,
        "requires -I -S -B",
    )
    require(
        not any(n in sys.modules for n in ("site", "sitecustomize", "usercustomize")),
        "automatic site initialization",
    )
    require(
        sys.meta_path
        == [machinery.BuiltinImporter, machinery.FrozenImporter, machinery.PathFinder],
        "initial import hooks",
    )
    manifest_path, expected, entry = sys.argv[1:4]
    raw = Path(manifest_path).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == expected, "manifest digest")
    manifest = json.loads(raw)
    require(set(manifest) == {"roots", "files"}, "manifest shape")
    roots = tuple(str(Path(p).resolve(strict=True)) for p in manifest["roots"])
    pins = manifest["files"]
    require(roots and len(roots) == len(set(roots)), "roots")

    def checked(path):
        resolved = str(Path(path).resolve(strict=True))
        require(resolved == str(path) and resolved in pins, "unlisted origin: " + str(path))
        require(any(Path(resolved).is_relative_to(p) for p in roots), "origin outside roots")
        data = Path(resolved).read_bytes()
        require(hashlib.sha256(data).hexdigest() == pins[resolved], "changed source: " + resolved)
        return data

    class Source(machinery.SourceFileLoader):
        def get_code(self, fullname):
            # Never ask SourceFileLoader for code: -B does not disable pyc reads.
            return compile(checked(self.path), self.path, "exec", dont_inherit=True)

    class Extension(machinery.ExtensionFileLoader):
        def create_module(self, spec):
            checked(self.path)
            return super().create_module(spec)

        def exec_module(self, module):
            checked(self.path)
            return super().exec_module(module)

    class Finder:
        def find_spec(self, fullname, path=None, target=None):
            search = roots if path is None else path
            namespaces = []
            for directory in search:
                directory = str(Path(directory).resolve(strict=True))
                require(any(Path(directory).is_relative_to(p) for p in roots), "package path")
                finder = machinery.FileFinder(
                    directory,
                    (Source, machinery.SOURCE_SUFFIXES),
                    (Extension, machinery.EXTENSION_SUFFIXES),
                )
                spec = finder.find_spec(fullname)
                if spec is None:
                    continue
                if spec.loader is not None:
                    checked(spec.origin)
                    return spec
                namespaces.extend(spec.submodule_search_locations or [])
            if namespaces:
                spec = machinery.ModuleSpec(fullname, None, is_package=True)
                spec.submodule_search_locations = namespaces
                return spec
            # Do not fall through to zip, editable or arbitrary path hooks.
            raise ModuleNotFoundError("trusted startup: unlisted module " + fullname)

    # typing.io/re are stdlib-created compatibility pseudo-modules without specs.
    # Import typing in the externally pinned bootstrap, then retain exact identities
    # in baseline. Do not allow arbitrary spec-less post-manifest modules.
    require(sys.modules["typing"] is _typing, "bootstrap typing identity")
    baseline = dict(sys.modules)
    finder = Finder()
    allowed = (machinery.BuiltinImporter, machinery.FrozenImporter, finder)
    sys.path[:] = roots
    sys.path_hooks[:] = []
    sys.path_importer_cache.clear()
    sys.meta_path[:] = allowed

    def refresh():
        require(
            tuple(sys.path) == roots and tuple(sys.meta_path) == allowed,
            "changed import paths/hooks",
        )
        require(not sys.path_hooks, "changed path hooks")
        require(
            not any(n in sys.modules for n in ("site", "sitecustomize", "usercustomize")),
            "site loaded",
        )
        for path in pins:
            checked(path)
        for name, module in sys.modules.copy().items():
            if name in baseline:
                require(module is baseline[name], "replaced bootstrap module")
                continue
            if name == "_rkuarch_trusted_startup":
                require(module is state, "replaced startup state")
                continue
            spec = getattr(module, "__spec__", None)
            require(spec is not None, "missing module spec: " + name)
            loader = spec.loader
            if loader in (machinery.BuiltinImporter, machinery.FrozenImporter):
                continue
            if isinstance(loader, (Source, Extension)):
                checked(spec.origin)
            else:
                require(
                    spec.origin is None and spec.submodule_search_locations is not None,
                    "untrusted loader: " + name,
                )
                require(
                    all(
                        any(Path(p).is_relative_to(r) for r in roots)
                        for p in spec.submodule_search_locations
                    ),
                    "namespace paths",
                )

    state = types.ModuleType("_rkuarch_trusted_startup")
    state.refresh = refresh
    state.manifest_sha256 = expected
    sys.modules[state.__name__] = state
    refresh()
    sys.argv = [entry, *sys.argv[4:]]
    importlib.import_module(entry)
    refresh()


if __name__ == "__main__":
    main()
