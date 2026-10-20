"""Reviewer installed-package smoke, run INSIDE a container that has no source checkout.

Usage (container): RUNTIME_PYTHON installed_smoke.py run|replay
Mounts: /rt (runtime, ro, at its host path via RT env), /inputs, /mutants (ro), /outputs (rw),
/native (ro, run mode only). Uses the shipping CLI `python -m rkuarch.engines.native.ordinary`
and the shipping `uarch-engine` binaries, not a test adapter.
"""

import json
import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

PY = sys.executable
CLI = [PY, "-m", "rkuarch.engines.native.ordinary"]
mode = sys.argv[1]
INP, MUT, OUT = Path("/inputs"), Path("/mutants"), Path("/outputs")
report = {"mode": mode, "checks": [], "failures": []}


def record(name, ok, **detail):
    report["checks"].append(dict(name=name, ok=bool(ok), **detail))
    if not ok:
        report["failures"].append(name)


def cli(*args, env_extra=None):
    env = {"PATH": "/usr/bin:/bin", "LC_ALL": "C"}
    env.update(env_extra or {})
    p = subprocess.run([*CLI, *args], capture_output=True, timeout=120, env=env, cwd="/scratch")
    return p.returncode, p.stdout.decode(), p.stderr.decode()


def native(binary, payload, test_only=False):
    p = subprocess.run([binary, "--protocol", "uarch-engine/4"] + (["--test-only"] if test_only else []),
                       input=payload, capture_output=True, timeout=60)
    code = None
    if p.returncode == 2 and p.stderr:
        try:
            code = json.loads(p.stderr)["code"]
        except ValueError:
            code = "unparseable"
    return p.returncode, code, p.stdout


# Environment: no checkout, no git, no developer paths, installed non-editable.
for path in ("/home", "/work", "/cargo-home", "/src"):
    record(f"absent:{path}", not Path(path).exists() or not any(Path(path).iterdir()))
cwd_git = [str(p) for p in [Path("/scratch"), *Path("/scratch").parents] if (p / ".git").exists()]
record("no .git above cwd", not cwd_git, found=cwd_git)
import rkuarch  # noqa: E402
import uarch_contract  # noqa: E402

site = Path(rkuarch.__file__).parents[1]
record("installed under runtime site-packages", str(site).endswith("site-packages"), site=str(site))
record("no editable/pth hooks", not list(site.glob("*.pth")) and not list(site.glob("__editable__*")))
record("historical host modules absent", not (site / "rkuarch/engines/native/component_host.py").exists()
       and not (site / "rkuarch/engines/native/runner.py").exists())

positives = sorted(p.name for p in INP.glob("*.json"))

if mode == "run":
    for name in positives:
        test_only = name.startswith("test-")
        flag = ["--test-only"] if test_only else []
        outs = {}
        for binary in ("debug", "release"):
            target = OUT / f"{name[:-5]}-{binary}.json"
            status, so, se = cli("run", "--job", str(INP / name), "--executable", f"/native/{binary}",
                                 "--output", str(target), *flag)
            outs[binary] = target.read_bytes() if status == 0 and target.exists() else None
            record(f"cli-run:{name}:{binary}", status == 0, stderr=se[-300:])
        equal = outs["debug"] is not None and outs["debug"] == outs["release"]
        r = json.loads(outs["release"]) if outs["release"] else {}
        record(f"debug==release:{name}", equal, duration_ps=r.get("duration_ps"),
               result_hash=r.get("result_hash"), eligibility=r.get("admission", {}).get("eligibility"))
        status, so, se = cli("replay", "--job", str(INP / name), "--output",
                             str(OUT / f"{name[:-5]}-release.json"), *flag)
        record(f"cli-replay-with-binary-present:{name}", status == 0, stderr=se[-300:])
    # Explicit invocation discipline at both layers.
    status, _, se = cli("run", "--job", str(INP / "production.json"), "--executable", "/native/release",
                        "--output", str(OUT / "x1.json"), "--test-only")
    record("cli: production job with --test-only refused", status == 2 and "AdmissionMismatch" in se,
           stderr=se[-200:])
    test_job = INP / "test-synthetic-stage2-cc-v3.json"
    status, _, se = cli("run", "--job", str(test_job), "--executable", "/native/release",
                        "--output", str(OUT / "x2.json"))
    record("cli: test job without --test-only refused", status == 2 and "AdmissionMismatch" in se,
           stderr=se[-200:])
    st, code, so = native("/native/release", test_job.read_bytes(), test_only=False)
    record("native: test job without --test-only refused", st == 2 and code == "AdmissionMismatch" and not so,
           status=st, code=code)
    st, code, so = native("/native/release", (INP / "production.json").read_bytes(), test_only=True)
    record("native: production job with --test-only refused", st == 2 and code == "AdmissionMismatch",
           status=st, code=code)
    st, code, so = native("/native/release", (INP / "production.json").read_bytes() + b"\n")
    record("native: trailing newline accepted (EOF framing)", st in (0, 2), status=st, code=code)
    p = subprocess.run(["/native/release", "--protocol", "uarch-engine/3"], input=b"{}", capture_output=True)
    record("native: /3 argv refused", p.returncode == 2 and json.loads(p.stderr)["code"] == "UnsupportedProtocol")
    # Mutants through Python (load_job, then CLI) and directly through the binary.
    from rkuarch.engines.native.ordinary import load_job

    for m in json.loads((MUT / "manifest.json").read_text()):
        payload = (MUT / f"{m['name']}.json").read_bytes()
        try:
            load_job(payload, test_only=m["test_only"])
            py, mro = "accept", []
        except Exception as e:  # noqa: BLE001 - record class and full message (codes follow line 1)
            py = f"{type(e).__name__}: {' '.join(str(e).split())[:300]}"
            mro = [c.__name__ for c in type(e).__mro__]
        expect_py = m["expect_python"].split("|")
        py_ok = (py == "accept") if expect_py == ["accept"] else any(
            x in py or x in mro for x in expect_py)
        outputs = {}
        for binary in ("debug", "release"):
            outputs[binary] = native(f"/native/{binary}", payload, m["test_only"])
        st, code, so = outputs["release"]
        expect_nat = m["expect_native"].split("|")
        if expect_nat == ["accept"]:
            nat_ok = st == 0
        elif expect_nat == ["accept-or-refuse"]:
            nat_ok = st in (0, 2)
        else:
            nat_ok = st == 2 and code in expect_nat and not so
        same = outputs["debug"] == outputs["release"]
        if st == 0:
            (OUT / f"mutant-{m['name']}-release.json").write_bytes(so)
        record(f"mutant:{m['name']}", py_ok and nat_ok and same, python=py, native_status=st,
               native_code=code, debug_release_same=same, expected_python=m["expect_python"],
               expected_native=m["expect_native"])
    # Python-side API run of the altered-hardware test job, for replay-mode faults.
    from rkuarch.engines.native.ordinary import run as api_run

    # Finding F1 probe: binary admits and runs altered test hardware (status 0, saved above);
    # the ordinary consumer's packaged checker refuses it. Recorded, not asserted as success.
    try:
        res = api_run(MUT / "hw-altered-test.json", executable=Path("/native/release"), test_only=True)
        got = f"accepted duration_ps={res.duration_ps}"
    except Exception as e:  # noqa: BLE001
        got = f"{type(e).__name__}: {str(e)[:120]}"
    report["observations"] = {"api-run hw-altered-test (native status 0)": got}
    status, _, se = cli("run", "--job", str(MUT / "hw-altered-test.json"), "--executable",
                        "/native/release", "--output", str(OUT / "x3.json"), "--test-only")
    report["observations"]["cli-run hw-altered-test"] = {"exit": status, "stderr": se[-160:]}

else:  # replay: no native binary is mounted
    record("native binary absent", not Path("/native").exists())
    from uarch_contract.hashing import canonical_json, content_hash, strict_json_loads
    from uarch_contract.ordinary import OrdinaryJob, validate_result

    from rkuarch.engines.native.ordinary import UNREPRESENTED, replay
    from rkuarch.verification.component.observations_v3 import check_v3

    for name in positives:
        flag = ["--test-only"] if name.startswith("test-") else []
        status, _, se = cli("replay", "--job", str(INP / name), "--output",
                            str(OUT / f"{name[:-5]}-release.json"), *flag)
        record(f"cli-replay-binary-free:{name}", status == 0, stderr=se[-300:])
    prod_job = INP / "production.json"
    prod_out = OUT / "production-release.json"
    alt_job = MUT / "hw-altered-test.json"
    alt_out = OUT / "mutant-hw-altered-test-release.json"

    def attempt(label, job_path, out_bytes, test_only=False, *, expect_refuse=True, extra=None):
        tmp = Path("/tmp") / f"{label}.json"
        tmp.write_bytes(out_bytes)
        try:
            replay(job_path, tmp, test_only=test_only)
            got = "accepted"
        except Exception as e:  # noqa: BLE001
            got = f"{type(e).__name__}: {' '.join(str(e).split())[:200]}"
        record(f"replay-fault:{label}", (got != "accepted") == expect_refuse, got=got, **(extra or {}))

    attempt("cross-job-binding", alt_job, prod_out.read_bytes(), test_only=True)
    base = strict_json_loads(prod_out.read_bytes())
    bad = deepcopy(base)
    bad["engine"]["package_version"] = "0.0.2"
    bad["result_hash"] = content_hash(bad, exclude=("result_hash",))
    attempt("result-package-version", prod_job, canonical_json(bad).encode())
    attempt("noncanonical-result", prod_job, json.dumps(base, indent=1).encode())
    attempt("empty-result", prod_job, b"")
    test_name = "test-synthetic-stage2-cc-v3"
    tmp = OUT / f"{test_name}-release.json"
    try:
        replay(INP / f"{test_name}.json", tmp, test_only=False)
        got = "accepted"
    except Exception as e:  # noqa: BLE001
        got = type(e).__name__
    record("replay-fault:test-result-without-test-flag", got != "accepted", got=got)
    # Wrong-law result: native output for 16-cycle overhead hardware relabelled to the
    # production job. Data hashes/bindings are made consistent; only model laws differ.
    job = OrdinaryJob.model_validate(strict_json_loads(prod_job.read_bytes()))
    wrong = strict_json_loads(alt_out.read_bytes())
    wrong["job_hash"] = job.job_hash
    wrong["admission"] = job.admission.model_dump(mode="json")
    wrong["result_hash"] = content_hash(wrong, exclude=("result_hash",))
    try:
        validate_result(wrong, job)
        structural = "accepted"
    except Exception as e:  # noqa: BLE001
        structural = f"{type(e).__name__}: {str(e)[:120]}"
    try:
        check_v3(job.model_dump(mode="json"), wrong, {"unrepresented": UNREPRESENTED})
        independent = "accepted"
    except Exception as e:  # noqa: BLE001
        independent = f"{type(e).__name__}: {str(e)[:120]}"
    wrong_bytes = canonical_json(wrong).encode()
    attempt("wrong-law-relabelled", prod_job, wrong_bytes,
            extra={"structural_validate_result": structural, "independent_check_v3": independent,
                   "duration_ps": wrong["duration_ps"]})
    (Path("/tmp") / "wrong.json").write_bytes(wrong_bytes)
    status, _, se = cli("replay", "--job", str(prod_job), "--output", "/tmp/wrong.json",
                        env_extra={"PYTHONOPTIMIZE": "2"})
    record("replay-fault:wrong-law-relabelled under -OO", status == 2, stderr=se[-200:])
    report["modules"] = sorted({m.__name__ for m in list(sys.modules.values())
                                if getattr(m, "__name__", "").startswith(("rkuarch", "uarch_contract"))})
    record("no mapping producer imported", not any(m.startswith("rkuarch.mapping") for m in report["modules"]))

report["module_files"] = sorted({str(getattr(m, "__file__", "")) for m in list(sys.modules.values())
                                 if getattr(m, "__name__", "").startswith(("rkuarch", "uarch_contract"))})
record("all rkuarch/uarch_contract modules from runtime", all(
    f.startswith(str(site)) for f in report["module_files"] if f))
print(json.dumps(report, indent=1, sort_keys=True))
sys.exit(1 if report["failures"] else 0)
