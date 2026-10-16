"""Host-only discriminating controls for monitor boundaries; no tracer execution."""

import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "trace_monitor", Path(__file__).with_name("trace_monitor.py")
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_exact_limits_and_restoration():
    assert m.limit_reason(29.9, 16 * 1024**2 - 1, 30, 16 * 1024**2) is None
    assert m.limit_reason(30, 1, 30, 16 * 1024**2) == "time limit"
    assert m.limit_reason(1, 16 * 1024**2, 30, 16 * 1024**2) == "output size limit"
    assert m.limit_reason(599, 512 * 1024**2 - 1, 600, 512 * 1024**2) is None
    assert m.limit_reason(600, 1, 600, 512 * 1024**2) == "time limit"
    assert m.limit_reason(1, 512 * 1024**2, 600, 512 * 1024**2) == "output size limit"


def test_output_accounting_refuses_symlink(tmp_path):
    (tmp_path / "trace.1").write_bytes(b"abc")
    assert m.size(tmp_path) == 3
    (tmp_path / "trace.2").symlink_to("trace.1")
    with pytest.raises(ValueError, match="symlink"):
        m.size(tmp_path)
    (tmp_path / "trace.2").unlink()
    assert m.size(tmp_path) == 3


def test_private_command_security_and_negative_controls(tmp_path):
    name, args = m.build_command(
        tmp_path, "canary", tmp_path / "out", tmp_path / "target", ["/bin/true"], trace=True
    )
    m.validate(args, name)
    assert "--library-path" in args
    for flag in ["--privileged", "--cap-add", "--pid", "LD_LIBRARY_PATH=/diagnostics"]:
        with pytest.raises(AssertionError):
            m.validate(args + [flag], name)
    bad = list(args)
    bad[bad.index("--network") + 1] = "host"
    with pytest.raises(AssertionError):
        m.validate(bad, name)
    m.validate(args, name)


def test_trace_parser_refuses_missing_child_and_tail():
    spec = importlib.util.spec_from_file_location(
        "trace_canary", Path(__file__).with_name("trace_canary.py")
    )
    c = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(c)
    logs = {
        1: "1.0 clone(flags=SIGCHLD) = 2\n1.1 +++ exited with 0 +++\n",
        2: '1.0 execve("/bin/true", ["/bin/true"], []) = 0\n1.1 +++ exited with 0 +++\n',
    }
    assert len(c.parse(logs)[0]) == 2
    with pytest.raises(c.CoverageError, match="missing child"):
        c.parse({1: logs[1]})
    with pytest.raises(c.CoverageError, match="terminal"):
        c.parse({1: logs[1], 2: logs[2].splitlines()[0]})
    assert len(c.parse(logs)[0]) == 2
