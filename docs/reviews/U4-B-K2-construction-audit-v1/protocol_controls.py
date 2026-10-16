"""Invalid-input process controls. Never sends a valid MappedEngineJob."""

import hashlib
import json
import subprocess
from pathlib import Path

# Explicit finite bytes; no success object or synthetic authority is sent.
CASES = (
    ("empty", b"", "InvalidJson"),
    ("invalid-utf8", b"\xff", "InvalidJson"),
    ("truncated", b"{", "InvalidJson"),
    ("duplicate", b'{"protocol":"uarch-engine/3","protocol":"uarch-engine/3"}', "InvalidJson"),
    ("reserved-marker", b'{"$serde_json::private::Number":"1"}', "InvalidJson"),
    ("trailing-object", b"{} {}", "InvalidJson"),
    ("empty-object", b"{}", "UnsupportedProtocol"),
    ("foreign-protocol", b'{"protocol":"foreign"}', "UnsupportedProtocol"),
    ("incomplete-job", b'{"protocol":"uarch-engine/3"}', "UnsupportedCheckpointScope"),
)


def check(executable, expected_sha256, output):
    """Invoke only inside the approved image with this caller-verified actual binary."""
    executable, output = Path(executable), Path(output)
    assert hashlib.sha256(executable.read_bytes()).hexdigest() == expected_sha256
    assert not output.exists()
    rows = []
    for name, payload, code in CASES:
        p = subprocess.run(
            [str(executable), "--protocol", "uarch-engine/3"],
            input=payload,
            capture_output=True,
            timeout=30,
            env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"},
        )
        assert p.returncode == 2 and not p.stdout, (name, p.returncode, p.stdout, p.stderr)
        value = json.loads(p.stderr)
        assert set(value) == {"code", "message", "pointer"} and value["code"] == code
        assert isinstance(value["message"], str)
        assert value["pointer"] is None or isinstance(value["pointer"], str)
        assert (
            json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
            == p.stderr
        )
        rows.append(
            dict(
                case=name,
                input_sha256=hashlib.sha256(payload).hexdigest(),
                exit_code=p.returncode,
                stderr_sha256=hashlib.sha256(p.stderr).hexdigest(),
                code=code,
            )
        )
    output.write_text(
        json.dumps(dict(executable_sha256=expected_sha256, cases=rows), indent=2) + "\n"
    )
    return rows
