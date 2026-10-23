"""Exercise archive replay while rejecting imports of the reference producers."""

import importlib.abc
import runpy
import sys
from pathlib import Path


class NoProducers(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname in {"rkuarch.workload.reference", "rkuarch.mapping.reference"}:
            raise RuntimeError("preparation producer is disabled: " + fullname)
        return None


if __name__ == "__main__":
    sys.meta_path.insert(0, NoProducers())
    script = Path(__file__).with_name("freeze.py")
    sys.argv = [str(script), "replay", *sys.argv[1:]]
    runpy.run_path(str(script), run_name="__main__")
