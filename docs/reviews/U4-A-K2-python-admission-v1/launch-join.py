import json
import subprocess
import sys
from pathlib import Path

root = Path("/tmp/u4-a-admission.0i3ay8e8")
label, source = sys.argv[1:3]
driver = sys.argv[3] if len(sys.argv) > 3 else "driver.py"
out = root / "receipts" / label
out.mkdir()
sealed = Path("/var/lib/rkuarch/k2/candidate-04-first-use-v1")
image = "sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523"
base = ["/usr/bin/docker", "--host", "unix:///var/run/docker.sock"]
env = {"PATH": "/usr/bin:/bin", "DOCKER_CONFIG": str(root / "docker-config")}
inspect = subprocess.run(base + ["image", "inspect", image], env=env, capture_output=True)
(out / "image-inspect.json").write_bytes(inspect.stdout)
assert inspect.returncode == 0 and json.loads(inspect.stdout)[0]["Id"] == image
cmd = base + [
    "run",
    "--name",
    "u4-a-admission-" + label,
    "--rm",
    "--pull",
    "never",
    "--platform",
    "linux/amd64",
    "--network",
    "none",
    "--read-only",
    "--user",
    "1000:1000",
    "--cap-drop",
    "ALL",
    "--security-opt",
    "no-new-privileges",
    "--tmpfs",
    "/tmp:rw,nosuid,nodev,noexec,size=64m,mode=1777",
    "--workdir",
    "/tmp",
]
for src, dst, mode in [
    (sealed / n, "/" + n, "ro") for n in ["candidate", "python", "site", "campaign", "manifests"]
] + [
    (sealed / "authority/k2-host-selector.json", "/etc/rkuarch/k2-host-selector.json", "ro"),
    (Path("/tmp/u4-k2-approved-campaign"), "/saved", "ro"),
    (Path(source), "/proposal", "ro"),
    (root / "tests-join", "/checks", "ro"),
    (out, "/receipts", "rw"),
]:
    cmd += ["--volume", f"{src}:{dst}:{mode}"]
cmd += ["--volume", f"{root}:/sources:ro"]
cmd += [
    "--entrypoint",
    "/usr/bin/env",
    image,
    "-i",
    "PATH=/usr/bin:/bin",
    "LC_ALL=C",
    "/python/bin/python3.12",
    "-I",
    "-S",
    "-B",
    "/checks/" + driver,
]
(out / "command.json").write_text(json.dumps({"argv": cmd, "environment": env}, indent=2) + "\n")
with (out / "stdout.txt").open("wb") as stdout, (out / "stderr.txt").open("wb") as stderr:
    result = subprocess.run(cmd, env=env, stdout=stdout, stderr=stderr)
(out / "exit.json").write_text(json.dumps({"exit": result.returncode}) + "\n")
print(label, result.returncode)
