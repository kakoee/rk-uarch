"""Private startup inventory/snapshot, not deployment or startup-integrity proof.

Only copy already accepted external inputs from a pinned inherited payload and
current proposed project sources. No installation, native execution or authority.
The external binding must be supplied by a later exact deployment decision.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import subprocess
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def copy_bound(source: Path, target: Path, expected: str) -> dict:
    data = source.read_bytes()
    pin = hashlib.sha256(data).hexdigest()
    if pin != expected.removeprefix("sha256:"):
        raise ValueError("existing input digest: " + str(source))
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as output:
        output.write(data)
    target.chmod(0o555 if source.stat().st_mode & 0o111 else 0o444)
    return dict(origin=str(source), snapshot=str(target), sha256=pin, bytes=len(data))


def write_manifest(path: Path, roots: list[Path], files: list[Path]) -> tuple[Path, str]:
    roots = [p.resolve(strict=True) for p in roots]
    if not roots or len(set(roots)) != len(roots):
        raise ValueError("unique explicit roots required")
    pins = {}
    for file in sorted(files):
        resolved = file.resolve(strict=True)
        if resolved != file or not any(file.is_relative_to(root) for root in roots):
            raise ValueError("manifest input outside explicit roots")
        pins[str(file)] = digest(file)
    write(path, dict(roots=list(map(str, roots)), files=pins))
    path.chmod(0o444)
    return path, digest(path)


# Benign observation only. Imports match the launcher's pre-manifest imports.
# __cached__ is a possible cache pathname, NOT proof that its bytes were read.
PROBE = """import hashlib,importlib,importlib.machinery,importlib.util,json,sys,types,typing
from pathlib import Path
modules={}
for name,module in sorted(sys.modules.copy().items()):
 spec=getattr(module,'__spec__',None)
 origin=getattr(spec,'origin',None)
 cached=getattr(module,'__cached__',None)
 modules[name]={'origin':origin,'cache_candidate':cached}
maps=Path('/proc/self/maps').read_text()
print(json.dumps({'modules':modules,'maps':maps,'executable':sys.executable,
 'prefix':sys.prefix,'sys_path':sys.path,'site_loaded':'site' in sys.modules,
 'flags':{'isolated':sys.flags.isolated,'no_site':sys.flags.no_site,
 'dont_write_bytecode':sys.flags.dont_write_bytecode}},sort_keys=True))
"""


def elf_interpreter(path: Path) -> str | None:
    """Read the actual ELF64 little-endian PT_INTERP without invoking a new tool."""
    raw = path.read_bytes()
    if raw[:6] != b"\x7fELF\x02\x01":
        raise ValueError("expected accepted ELF64 interpreter")
    offset = struct.unpack_from("<Q", raw, 32)[0]
    size, count = struct.unpack_from("<HH", raw, 54)
    for index in range(count):
        header = offset + size * index
        kind = struct.unpack_from("<I", raw, header)[0]
        if kind == 3:
            start = struct.unpack_from("<Q", raw, header + 8)[0]
            length = struct.unpack_from("<Q", raw, header + 32)[0]
            return raw[start : start + length].rstrip(b"\0").decode()
    return None


def construct(source: Path, payload_path: Path, expected_payload: str, output: Path) -> dict:
    if digest(payload_path) != expected_payload.removeprefix("sha256:"):
        raise ValueError("inherited payload digest")
    source, output = source.resolve(strict=True), output.resolve()
    if not output.is_relative_to(Path("/tmp")):
        raise ValueError("private /tmp package required")
    output.mkdir(exist_ok=False)
    payload = json.loads(payload_path.read_bytes())
    consumer = payload["consumers"]
    snapshot = output / "snapshot"
    rows = []
    project = snapshot / "project"
    for folder in ("src/rkuarch", "contract/uarch_contract", "validation", "native/tools"):
        for file in sorted((source / folder).rglob("*.py")):
            rows.append(copy_bound(file, project / file.relative_to(source), digest(file)))
    external = snapshot / "external"
    for binding in consumer["external_files"]:
        origin = Path("/") / binding["path"]
        rows.append(copy_bound(origin, external / binding["path"], binding["byte_hash"]))
    interpreter = consumer["python_executable"]
    python = Path("/") / interpreter["path"]
    rows.append(copy_bound(python, external / interpreter["path"], interpreter["byte_hash"]))
    bootstrap = output / "bootstrap-probe.py"
    bootstrap.write_text(PROBE)
    run = subprocess.run(
        [str(python), "-I", "-S", "-B", str(bootstrap)],
        env={"LC_ALL": "C"},
        capture_output=True,
        timeout=20,
    )
    (output / "bootstrap.stdout").write_bytes(run.stdout)
    (output / "bootstrap.stderr").write_bytes(run.stderr)
    if run.returncode:
        raise ValueError("benign bootstrap observation failed")
    observed = json.loads(run.stdout)
    stdlib = Path(observed["prefix"]) / "lib" / ("python" + python.name.removeprefix("python"))
    if not stdlib.is_dir():
        raise ValueError("explicit interpreter stdlib root unavailable")
    # Accepted external inventory defines allowed dependency roots; never scan new packages.
    site_roots = set()
    for binding in consumer["external_files"]:
        path = Path("/") / binding["path"]
        for parent in path.parents:
            if parent.name == "site-packages":
                site_roots.add(parent)
                break
    roots = [
        project / "src",
        project / "contract",
        project,
        *[external / p.relative_to("/") for p in sorted(site_roots)],
        external / stdlib.relative_to("/"),
        external / (stdlib / "lib-dynload").relative_to("/"),
        stdlib,
        stdlib / "lib-dynload",
    ]
    for root in roots:
        root.mkdir(parents=True, exist_ok=True)
    # Inventory observed mappings plus existing cache candidates independently of source imports.
    # The host loader, interpreter and bootstrap remain externally protected TCB requirements.
    tcb_paths = {python, source / "native/tools/component_trusted_start.py"}
    for line in observed["maps"].splitlines():
        fields = line.split(maxsplit=5)
        if len(fields) == 6 and fields[5].startswith("/"):
            tcb_paths.add(Path(fields[5]))
    for item in observed["modules"].values():
        for field in ("origin", "cache_candidate"):
            value = item[field]
            if value and Path(value).is_absolute() and Path(value).is_file():
                tcb_paths.add(Path(value))
    tcb = []
    for origin in sorted(tcb_paths):
        tcb.append(copy_bound(origin, snapshot / "tcb" / origin.relative_to("/"), digest(origin)))
    loader = elf_interpreter(python)
    loader_configuration = []
    for path in [
        Path("/etc/ld.so.cache"),
        Path("/etc/ld.so.conf"),
        *sorted(Path("/etc/ld.so.conf.d").glob("*.conf")),
    ]:
        if path.is_file():
            loader_configuration.append(
                copy_bound(path, snapshot / "loader-config" / path.relative_to("/"), digest(path))
            )
    caches = []
    for root in [stdlib, *sorted(site_roots)]:
        for path in sorted(root.rglob("*.pyc")):
            if root == stdlib and "site-packages" in path.parts:
                continue
            caches.append(
                dict(
                    snapshot=copy_bound(
                        path, snapshot / "cache-candidates" / path.relative_to("/"), digest(path)
                    )["snapshot"],
                    path=str(path),
                    sha256=digest(path),
                    bytes=path.stat().st_size,
                    read_observed=False,
                )
            )
    # A new benign entry is preparation code, not an integrity probe or a successful native job.
    entry = project / "component_inventory_entry.py"
    entry.write_text(
        "import json,sys\nfrom pathlib import Path\n"
        "from rkuarch.engines.native import component_image\n"
        "from validation.component.observations_v3 import check_v3\n"
        "print(json.dumps({'adapter':component_image.__file__,"
        "'checker':check_v3.__module__,'site':'site' in sys.modules,"
        "'modules':{n:getattr(m,'__file__',None) for n,m in "
        "sorted(sys.modules.copy().items())},"
        "'maps':Path('/proc/self/maps').read_text()},sort_keys=True))\n"
    )
    entry.chmod(0o444)
    files = [Path(r["snapshot"]) for r in rows if Path(r["snapshot"]).suffix in (".py", ".so")]
    files.extend(
        Path("/") / row["path"]
        for row in consumer["external_files"]
        if (Path("/") / row["path"]).is_relative_to(stdlib)
    )
    files.append(entry)
    manifest, pin = write_manifest(output / "startup-manifest.json", roots, files)
    launcher = project / "native/tools/component_trusted_start.py"
    argv = [
        str(python),
        "-I",
        "-S",
        "-B",
        str(launcher),
        str(manifest),
        pin,
        "component_inventory_entry",
    ]
    binding = dict(
        format="component-startup-preparation/1",
        execution_authority=False,
        inherited_payload_sha256=digest(payload_path),
        source_root=str(source),
        manifest_sha256=pin,
        interpreter=interpreter,
        interpreter_resolved=str(python.resolve(strict=True)),
        elf_interpreter=loader,
        elf_interpreter_resolved=str(Path(loader).resolve(strict=True)) if loader else None,
        loader_configuration=loader_configuration,
        launcher_sha256=digest(launcher),
        argv=argv,
        environment={"LC_ALL": "C"},
        files=rows,
        bootstrap_tcb=tcb,
        cache_candidates=caches,
        bootstrap_observation_sha256=digest(output / "bootstrap.stdout"),
        limitations=[
            "Read-only private copies are not immutable deployment.",
            "Host interpreter/bootstrap/loader/cache paths remain external TCB.",
            "Inventory is not read completeness or A-F3 closure.",
            "No native job, startup substitution or defense revert ran.",
        ],
    )
    # Benign import-only invocation; never executes a native job or authority preparation.
    launch = subprocess.run(argv, env={"LC_ALL": "C"}, capture_output=True, timeout=30)
    (output / "launch.stdout").write_bytes(launch.stdout)
    (output / "launch.stderr").write_bytes(launch.stderr)
    binding["launch_status"] = launch.returncode
    binding["launch_stdout_sha256"] = digest(output / "launch.stdout")
    binding["launch_stderr_sha256"] = digest(output / "launch.stderr")
    if launch.returncode == 0:
        imported = json.loads(launch.stdout)
        loaded = set()
        for line in imported["maps"].splitlines():
            fields = line.split(maxsplit=5)
            if len(fields) == 6 and fields[5].startswith("/"):
                loaded.add(Path(fields[5]))
        binding["observed_loaded_files"] = [
            dict(path=str(path), sha256=digest(path), bytes=path.stat().st_size)
            for path in sorted(loaded)
        ]
        binding["launch_observation"] = "benign imports only; not startup-integrity proof"
    write(output / "package.json", binding)
    # Make snapshot directories read-only too; owner can still change modes: no immutability claim.
    for path in sorted(snapshot.rglob("*"), reverse=True):
        if path.is_dir():
            path.chmod(0o555)
    snapshot.chmod(0o555)
    return binding


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("inherited_payload", type=Path)
    parser.add_argument("expected_payload_sha256")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    construct(args.source, args.inherited_payload, args.expected_payload_sha256, args.output)


if __name__ == "__main__":
    main()
