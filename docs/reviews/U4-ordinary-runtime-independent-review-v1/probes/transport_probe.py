"""Installed transport/process-handling probe with tiny fake executables (no mapped jobs).

Usage: RUNTIME_PYTHON -I transport_probe.py WORK_DIR PRODUCTION_JOB
Each fake marks its descendants with a unique `sleep <marker>` argument; after every exchange
the probe scans /proc for survivors, records them, and kills ONLY those exact PIDs.
"""

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from rkuarch.engines.native.transport import Limits, _decode_envelope, _exchange

work, job = Path(sys.argv[1]), Path(sys.argv[2])
work.mkdir(parents=True, exist_ok=True)
rows = []


def fake(name, body):
    path = work / name
    path.write_text("#!/bin/sh\n" + body + "\n")
    path.chmod(0o755)
    return path


def survivors(marker):
    found = []
    for pid in os.listdir("/proc"):
        if pid.isdigit():
            try:
                cmd = (Path("/proc") / pid / "cmdline").read_bytes().split(b"\0")
            except OSError:
                continue
            if cmd[:2] == [b"sleep", marker.encode()]:
                found.append(int(pid))
    return found


def exchange(label, script, *, marker=None, limits=Limits(timeout_s=2.0), request=b"{}",
             expect=None, decode=True):
    fd = os.open(script, os.O_RDONLY)
    start = time.monotonic()
    try:
        so, se, st = _exchange(fd, request, limits, protocol="uarch-engine/4")
        outcome = f"returned status={st} stdout={len(so)}B stderr={len(se)}B"
        if decode:
            try:
                _decode_envelope(so, se, st)
                outcome += " -> decoded"
            except Exception as e:  # noqa: BLE001
                outcome += f" -> {type(e).__name__}: {e}"
    except Exception as e:  # noqa: BLE001
        outcome = f"{type(e).__name__}: {e}"
    finally:
        os.close(fd)
    elapsed = round(time.monotonic() - start, 2)
    time.sleep(0.2)
    left = survivors(marker) if marker else []
    for pid in left:
        os.kill(pid, signal.SIGKILL)  # reviewer cleanup of its own exact fake descendants
    ok = (expect in outcome) if expect else True
    rows.append(dict(case=label, outcome=outcome, elapsed_s=elapsed, survivors=len(left),
                     expected=expect, ok=ok))
    print(json.dumps(rows[-1]))


exchange("hang with grandchild -> Timeout, group killed",
         fake("hang", "sleep 3011 &\nexec sleep 3011"), marker="3011", expect="Timeout")
exchange("child exits, grandchild keeps stdout -> Timeout, group killed",
         fake("orphan_pipe", "sleep 3012 &\nexit 0"), marker="3012", expect="Timeout")
exchange("stdout over cap -> StdoutLimit",
         fake("flood", "sleep 3013 &\nhead -c 200000 /dev/zero; wait"), marker="3013",
         limits=Limits(timeout_s=5.0, stdout_bytes=1000), expect="StdoutLimit")
exchange("stderr over cap -> StderrLimit",
         fake("flood_err", "head -c 200000 /dev/zero >&2"), limits=Limits(timeout_s=5.0, stderr_bytes=1000),
         expect="StderrLimit")
exchange("status 3 -> ProtocolViolation", fake("st3", "cat >/dev/null; printf '{}'; exit 3"),
         expect="ProtocolViolation")
exchange("status 0 with stderr -> ProtocolViolation",
         fake("noise", "cat >/dev/null; printf '{}'; printf warn >&2; exit 0"), expect="ProtocolViolation")
exchange("status 2 with stdout -> ProtocolViolation",
         fake("st2out", "cat >/dev/null; printf '{}'; exit 2"), expect="ProtocolViolation")
exchange("status 2 valid refusal -> decoded (NativeRefusal in consume)",
         fake("refuse", "cat >/dev/null; printf '%s' '{\"code\":\"InvalidJson\",\"message\":\"x\",\"pointer\":null}' >&2; exit 2"),
         expect="decoded")
exchange("status 2 unknown code -> ProtocolViolation",
         fake("refuse_bad", "cat >/dev/null; printf '%s' '{\"code\":\"Made\",\"message\":\"x\",\"pointer\":null}' >&2; exit 2"),
         expect="ProtocolViolation")
exchange("killed by SIGKILL -> OperationalFailure NativeExit:-9",
         fake("selfkill", "cat >/dev/null; kill -9 $$"), expect="NativeExit:-9")
exchange("status 1 -> OperationalFailure NativeExit:1", fake("st1", "exit 1"), expect="NativeExit:1")
exchange("does not read 1 MiB stdin, exits 0 silently -> ProtocolViolation",
         fake("noread", "exit 0"), request=b"x" * (1 << 20), expect="ProtocolViolation")
exchange("success with detached grandchild (pipes closed) -> returns; descendant survives",
         fake("detached", "cat >/dev/null; sleep 3014 </dev/null >/dev/null 2>&1 &\nprintf '{}'"),
         marker="3014", expect="returned status=0")
nonexec = work / "nonexec"
nonexec.write_text("#!/bin/sh\nexit 0\n")
nonexec.chmod(0o644)
exchange("non-executable file -> SpawnFailure", nonexec, expect="SpawnFailure")

# Shipping CLI: operational failure is nonzero and writes no output file.
cli = [sys.executable, "-m", "rkuarch.engines.native.ordinary", "run", "--job", str(job)]
for label, exe, expect_rc in [("CLI with self-killing executable", work / "selfkill", 2),
                              ("CLI with missing executable", work / "missing", 2)]:
    out = work / f"{exe.name}-out.json"
    p = subprocess.run([*cli, "--executable", str(exe), "--output", str(out)], capture_output=True,
                       timeout=60, cwd=work)
    ok = p.returncode == expect_rc and not out.exists()
    rows.append(dict(case=label, outcome=f"exit={p.returncode} stderr={p.stderr.decode().strip()[-120:]}",
                     output_written=out.exists(), ok=ok))
    print(json.dumps(rows[-1]))
(work / "transport_probe.json").write_text(json.dumps(rows, indent=1) + "\n")
sys.exit(0 if all(r["ok"] for r in rows) else 1)
