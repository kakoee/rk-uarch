"""Closed payload and external publication joins; hashes alone never grant authority."""

import hashlib
import json
import re
import stat
from pathlib import Path

OLD = Path("/var/lib/rkuarch/k2/candidate-04-first-use-v1")
NEW = Path("/var/lib/rkuarch/k2/candidate-04-combined-runtime-v1")
PACKAGE = "docs/reviews/U4-B-K2-combined-runtime-v1/"
DECISION = "docs/reviews/U4-K2-combined-runtime-authorization-v1/decision.json"
PLACEMENT = "docs/reviews/U4-K2-combined-runtime-authorization-v1/placement.json"


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def digest(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()


def read(path):
    return json.loads(Path(path).read_bytes())


def relative(name):
    need(isinstance(name, str) and re.fullmatch(r"[A-Za-z0-9_./-]+", name), "safe path")
    need(
        not name.startswith("/") and all(x not in ("", ".", "..") for x in name.split("/")),
        "relative path",
    )
    return Path(name)


def inventory(root, expected, *, sealed):
    root = Path(root)
    need(root.is_dir() and not root.is_symlink(), "real payload root")
    files = {str(p.relative_to(root)) for p in root.rglob("*") if not p.is_dir() or p.is_symlink()}
    need(files == set(expected), "exact payload membership")
    wanted_dirs = {
        str(parent) for name in expected for parent in relative(name).parents if str(parent) != "."
    }
    actual_dirs = {str(p.relative_to(root)) for p in root.rglob("*") if p.is_dir()}
    need(actual_dirs == wanted_dirs, "exact payload directory membership")
    for p in (root, *root.rglob("*")):
        s = p.lstat()
        need(not p.is_symlink(), "no payload symlink")
        need(stat.S_ISDIR(s.st_mode) or stat.S_ISREG(s.st_mode), "regular payload")
        if p.is_file():
            need(s.st_nlink == 1, "single payload inode")
        if sealed:
            need(s.st_uid == 0 and not s.st_mode & 0o222, "sealed root-owned payload")
    for name, expected_hash in expected.items():
        need(
            digest((root / relative(name)).read_bytes()) == expected_hash, "payload bytes: " + name
        )


def identity(candidate_bytes):
    c = json.loads(candidate_bytes)
    return {
        "candidate_hash": digest(candidate_bytes),
        "python_closure_hash": digest(encoded(c["project"])),
        "helpers_hash": digest(encoded(c["helpers"])),
        "combined_helper_hash": c["helpers"]["parallel_entrypoint.py"],
        "native_source": c["native_source"],
        "native_subject": c["native_subject"],
        "original_runtime_release_hash": c["old_files"]["manifests/runtime-release.json"],
    }


def check_payload(project, helpers, record, *, sealed=True):
    data = (Path(record) / "candidate.json").read_bytes()
    c = json.loads(data)
    inventory(project, c["project"], sealed=sealed)
    inventory(helpers, c["helpers"], sealed=sealed)
    publication = read(Path(record) / "publication.json")
    need(publication["candidate_hash"] == digest(data), "publication candidate join")
    need(
        re.fullmatch("[0-9a-f]{40}", publication["helper_commit"]) is not None,
        "full helper publication",
    )
    inventory(
        record,
        {"candidate.json": digest(data), "publication.json": digest(encoded(publication))},
        sealed=sealed,
    )
    return c, data, publication


def old_bindings(root, candidate):
    for name, expected in candidate["old_files"].items():
        need(
            digest((Path(root) / relative(name)).read_bytes()) == expected,
            "original native/runtime binding: " + name,
        )


def origins(modules, project):
    result = {}
    for name, module in tuple(modules.items()):
        if name.split(".")[0] not in ("rkuarch", "uarch_contract"):
            continue
        file = getattr(module, "__file__", None)
        need(file is not None, "project module without file")
        path = Path(file).resolve()
        need(path.is_relative_to(Path(project).resolve()), "wrong project import origin: " + name)
        result[name] = str(path)
    need(
        "rkuarch.engines.native.host" in result and "uarch_contract.hardware" in result,
        "nonempty actual project imports",
    )
    return result


def check_preflight(preflight, candidate_bytes, publication):
    need(
        preflight["status"] == "combined-runtime-import-preflight-passed",
        "actual placed preflight required",
    )
    need(preflight["binding"] == identity(candidate_bytes), "preflight identity")
    need(preflight["publication"] == publication, "preflight publication")
    need(
        preflight["root"] == str(NEW) and preflight["immutable_mounts_checked"] is True,
        "actual immutable-root preflight",
    )
    need(
        preflight["native_calls"] == 0 and preflight["authority_resolved"] is False,
        "authority-free preflight",
    )
    need(
        preflight["private_test"] is False and bool(preflight["origins"]),
        "private tests are not placement",
    )


def check_decision(decision, candidate_bytes, publication):
    need(
        decision["binding"] == identity(candidate_bytes) and decision["publication"] == publication,
        "decision exact candidate",
    )
    need(
        decision["format"] == "uarch-k2-combined-human-decision/1"
        and decision["accepted_by"] == "Javid (@jjaffari)"
        and decision["reply"] == "yes",
        "actual human decision required",
    )
    need(
        decision["scope"] == "isolated-protected-runtime-placement-preflight-and-798-call-restart",
        "exact bounded approval",
    )
    need(
        decision["amendment_hash"] == json.loads(candidate_bytes)["amendment_hash"],
        "exact normative text",
    )


def check_authority(directory, candidate_bytes, publication):
    directory = Path(directory)
    names = {"selector.json", "decision.json", "placement.json", "preflight.json", "release.json"}
    need({p.name for p in directory.iterdir()} == names, "complete exact runtime authority")
    selector = read(directory / "selector.json")
    for name in names - {"selector.json"}:
        need(
            digest((directory / name).read_bytes()) == selector["files"][name],
            "external selector binding: " + name,
        )
    need(set(selector["files"]) == names - {"selector.json"}, "selector exact members")
    binding = identity(candidate_bytes)
    decision, placement, release = [
        read(directory / n) for n in ("decision.json", "placement.json", "release.json")
    ]
    for obj in (selector, decision, placement, release):
        need(
            obj["binding"] == binding and obj["publication"] == publication,
            "unapproved/swapped runtime binding",
        )
    need(
        decision["format"] == "uarch-k2-combined-human-decision/1"
        and decision["accepted_by"] == "Javid (@jjaffari)"
        and decision["reply"] == "yes",
        "actual human decision required",
    )
    need(
        decision["scope"] == "isolated-protected-runtime-placement-preflight-and-798-call-restart",
        "exact bounded approval",
    )
    need(
        decision["amendment_hash"] == json.loads(candidate_bytes)["amendment_hash"],
        "exact normative text",
    )
    need(
        placement["status"] == "actual-placement-and-preflight-reconciled",
        "actual coordinator placement",
    )
    need(
        placement["decision_commit"] == selector["decision_commit"]
        and placement["decision_hash"] == selector["files"]["decision.json"],
        "placement decision join",
    )
    need(
        placement["preflight_hash"] == selector["files"]["preflight.json"],
        "placement preflight join",
    )
    need(
        release["status"] == "human-authorized-combined-runtime" and release["root"] == str(NEW),
        "runtime release state",
    )
    need(
        release["decision_commit"] == selector["decision_commit"]
        and release["placement_commit"] == selector["placement_commit"],
        "release publication join",
    )
    need(
        release["decision_hash"] == selector["files"]["decision.json"]
        and release["placement_hash"] == selector["files"]["placement.json"]
        and release["preflight_hash"] == selector["files"]["preflight.json"],
        "release evidence join",
    )
    for key in ("decision_commit", "placement_commit"):
        need(re.fullmatch("[0-9a-f]{40}", selector[key]) is not None, "real publication required")
    check_decision(decision, candidate_bytes, publication)
    check_preflight(read(directory / "preflight.json"), candidate_bytes, publication)
    return {
        **binding,
        "runtime_selector_hash": digest((directory / "selector.json").read_bytes()),
        "release_hash": digest((directory / "release.json").read_bytes()),
        "publication": publication,
        "decision_commit": selector["decision_commit"],
        "placement_commit": selector["placement_commit"],
    }
