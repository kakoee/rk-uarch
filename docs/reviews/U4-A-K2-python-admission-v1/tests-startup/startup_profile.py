"""Timing-only instrumentation of the existing resolver body, not alternate checks."""

import ast
import copy
import time
from pathlib import Path


class Phases:
    def __init__(self):
        self.current = None
        self.since = None
        self.rows = {}
        self.reads = {}

    def phase(self, label):
        now = time.perf_counter()
        if self.current is not None:
            self.rows[self.current] = self.rows.get(self.current, 0) + now - self.since
        self.current, self.since = label, now

    def finish(self):
        self.phase(None)

    def install(self, host):
        name = "_validated_installation" if hasattr(host, "_validated_installation") else "_resolve"
        tree = ast.parse(Path(host.__file__).read_text())
        node = copy.deepcopy(
            next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
        )
        body = []
        for i, statement in enumerate(node.body):
            stage = "common_records_approval_sources" if i == 1 else None
            if isinstance(statement, ast.Assign):
                names = [x.id for x in statement.targets if isinstance(x, ast.Name)]
                if "profiles" in names:
                    stage = "profiles_registry"
                elif "inventory" in names:
                    stage = "corpus_and_job_admission"
                elif "selector_data" in names:
                    stage = "immutable_state_preparation"
            if (
                isinstance(statement, ast.For)
                and isinstance(statement.target, ast.Name)
                and statement.target.id == "executable"
            ):
                stage = "mode_receipts_and_binaries"
            if stage:
                marker = ast.Expr(
                    value=ast.Call(
                        func=ast.Name(id="_diagnostic_phase", ctx=ast.Load()),
                        args=[ast.Constant(stage)],
                        keywords=[],
                    )
                )
                body.append(ast.copy_location(marker, statement))
            body.append(statement)
        node.body = body
        instrumented = ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[]))
        host.__dict__["_diagnostic_phase"] = self.phase
        original_function = getattr(host, name)
        exec(compile(instrumented, host.__file__, "exec"), host.__dict__)
        original_read = host._read

        def read(root, binding):
            start = time.perf_counter()
            try:
                return original_read(root, binding)
            finally:
                entry = self.reads.setdefault(self.current, {"count": 0, "seconds": 0.0})
                entry["count"] += 1
                entry["seconds"] += time.perf_counter() - start

        host._read = read

        def restore():
            setattr(host, name, original_function)
            host._read = original_read
            del host.__dict__["_diagnostic_phase"]

        return restore
