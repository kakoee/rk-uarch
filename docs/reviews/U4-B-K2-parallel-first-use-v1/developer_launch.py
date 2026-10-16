"""Print by default; bounded authority-free saved-output checks in the accepted image."""

import argparse
import json
import os
import shutil
import subprocess
import tempfile
import time
import uuid
from pathlib import Path

from launch import HERE, base_deployment
from parallel_core import digest, require


def command(profile, saved, output, helpers):
    require(profile in ("fast", "regression"), "explicit saved developer profile")
    saved, output, helpers = map(lambda p: Path(p).resolve(), (saved, output, helpers))
    require(not output.is_relative_to(saved), "preserve saved inputs")
    argv = base_deployment().docker_argv("preflight", output, False)
    index = argv.index("--entrypoint")
    argv[index:index] = [
        "--mount",
        f"type=bind,src={helpers},dst=/developer,readonly,bind-propagation=rprivate",
        "--mount",
        f"type=bind,src={saved},dst=/saved,readonly,bind-propagation=rprivate",
    ]
    argv[-2:] = [
        "-c",
        'import runpy,sys;sys.path.insert(0,"/developer");'
        'sys.argv=["/developer/developer_checks.py","' + profile + '",'
        '"--saved","/saved","--output","/receipts/checks"];'
        'runpy.run_path(sys.argv[0],run_name="__main__")',
    ]
    return argv


def launch(profile, saved, output, execute):
    output = Path(output).resolve()
    require(not output.exists(), "new private developer output required")
    argv = command(profile, saved, output, HERE)
    if not execute:
        print(json.dumps(argv, indent=2))
        return
    require(os.getuid() == os.geteuid() == 1000, "existing UID1000 required")
    output.mkdir()
    started = time.monotonic()
    reason = None
    limit = 180 if profile == "fast" else 3600
    with tempfile.TemporaryDirectory(prefix="u4-k2-developer-") as temp:
        private = Path(temp)
        helpers = private / "helpers"
        helpers.mkdir()
        for name in ("developer_checks.py", "parallel_core.py"):
            shutil.copyfile(HERE / name, helpers / name)
        hashes = {p.name: digest(p.read_bytes()) for p in helpers.iterdir()}
        argv = command(profile, saved, output, helpers)
        name = "u4-k2-developer-" + uuid.uuid4().hex
        argv[4:4] = ["--name", name]
        config = private / "docker-config"
        config.mkdir()
        env = {"PATH": "/usr/bin:/bin", "DOCKER_CONFIG": str(config)}
        with (output / "stdout").open("xb") as out, (output / "stderr").open("xb") as err:
            proc = subprocess.Popen(argv, env=env, stdout=out, stderr=err, start_new_session=True)
            try:
                while proc.poll() is None:
                    require(time.monotonic() - started < limit, "developer deadline")
                    files = list(output.rglob("*"))
                    require(not any(p.is_symlink() for p in files), "output symlink")
                    require(
                        sum(p.stat().st_size for p in files if p.is_file()) < 16 * 1024**2,
                        "developer receipt cap",
                    )
                    time.sleep(0.1)
            except BaseException as exc:
                reason = repr(exc)
            finally:
                if proc.poll() is None:
                    subprocess.run(
                        argv[:3] + ["kill", "--signal", "KILL", name],
                        env=env,
                        capture_output=True,
                        timeout=10,
                        check=False,
                    )
                code = proc.wait(timeout=20)
        require(
            hashes == {p.name: digest(p.read_bytes()) for p in helpers.iterdir()},
            "diagnostic helper drift",
        )
    (output / "launch.json").write_text(
        json.dumps(
            {
                "argv": argv,
                "exit_code": code,
                "stop_reason": reason,
                "elapsed_seconds": time.monotonic() - started,
                "limit_seconds": limit,
                "helper_hashes": hashes,
                "native_calls": 0,
                "authority_resolutions": 0,
            },
            indent=2,
        )
        + "\n"
    )
    require(code == 0 and reason is None, "developer check failed; preserve receipt")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("profile", choices=["fast", "regression"])
    p.add_argument("--saved", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--execute-saved", action="store_true")
    args = p.parse_args()
    launch(args.profile, args.saved, args.output, args.execute_saved)
