"""Closed payload and external publication joins; hashes alone never grant authority."""

import hashlib
import json
import re
import stat
from pathlib import Path

OLD = Path("/var/lib/rkuarch/k2/candidate-04-first-use-v1")
NEW = Path("/var/lib/rkuarch/k2/candidate-04-combined-runtime-v2")
PACKAGE = "docs/reviews/U4-B-K2-combined-runtime-stage2-v1/"
DECISION = "docs/reviews/U4-K2-combined-runtime-authorization-v2/decision.json"
PLACEMENT = "docs/reviews/U4-K2-combined-runtime-authorization-v2/placement.json"


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
        if file is None:
            raise ValueError("project module without file")
        path = Path(file).resolve()
        need(path.is_relative_to(Path(project).resolve()), "wrong project import origin: " + name)
        result[name] = str(path)
    need(
        "rkuarch.engines.native.host" in result and "uarch_contract.hardware" in result,
        "nonempty actual project imports",
    )
    return result


def module_origins(modules):
    result = {}
    for name, module in tuple(modules.items()):
        spec = getattr(module, "__spec__", None)
        origin = getattr(spec, "origin", None)
        file = getattr(module, "__file__", None)
        result[name] = {
            "file": str(Path(file).resolve()) if file else None,
            "kind": origin if origin in ("built-in", "frozen") else ("file" if file else "no-file"),
        }
    return result


def helper_origins(modules, expected):
    result = {}
    for name, binding in expected.items():
        module = modules.get(name)
        if name == "runtime_entry" and module is None:
            module = modules.get("__main__")
        file = getattr(module, "__file__", None)
        if file is None:
            raise ValueError("helper origin: " + name)
        need(
            Path(file).resolve() == Path(binding["path"]),
            "helper origin: " + name,
        )
        need(digest(Path(file).read_bytes()) == binding["sha256"], "helper origin bytes: " + name)
        result[name] = {"path": str(Path(file).resolve()), "sha256": binding["sha256"]}
    return result


def mount_observations(text):
    result = {}
    for line in text.splitlines():
        fields = line.split()
        split = fields.index("-")

        def unescape(value):
            return re.sub(r"\\([0-7]{3})", lambda m: chr(int(m.group(1), 8)), value)

        result[unescape(fields[4])] = {
            "source_root": unescape(fields[3]),
            "mount_options": fields[5].split(","),
            "filesystem": fields[split + 1],
            "source": unescape(fields[split + 2]),
            "super_options": fields[split + 3].split(","),
        }
    return result


def observed_payload(root, expected, *, sealed):
    inventory(root, expected, sealed=sealed)
    nodes = [Path(root), *Path(root).rglob("*")]
    stats = [p.lstat() for p in nodes]
    return {
        "container_root": str(root),
        "seal_check_enforced": sealed,
        "all_root_owned": all(s.st_uid == 0 for s in stats),
        "all_inodes_readonly": all(not s.st_mode & 0o222 for s in stats),
        "inventory_hash": digest(encoded(expected)),
        "files_checked": sorted(expected),
        "root_uid": stats[0].st_uid,
        "root_mode": stat.S_IMODE(stats[0].st_mode),
    }


def check_preflight(preflight, candidate_bytes, publication):
    need(
        preflight["status"] == "combined-runtime-import-preflight-passed",
        "actual placed preflight required",
    )
    need(preflight["binding"] == identity(candidate_bytes), "preflight identity")
    need(preflight["publication"] == publication, "preflight publication")
    need("observations" in preflight, "actual observed seal/mount evidence required")
    obs = preflight["observations"]
    c = json.loads(candidate_bytes)
    expected = {"/project": ("project", c["project"]), "/combined": ("helpers", c["helpers"])}
    record = {
        "candidate.json": digest(candidate_bytes),
        "publication.json": digest(encoded(publication)),
    }
    expected["/combined-record"] = ("record", record)
    for mount, (suffix, members) in expected.items():
        seal = obs["payload"][mount]
        need(
            seal["seal_check_enforced"] is True
            and seal["all_root_owned"] is True
            and seal["all_inodes_readonly"] is True
            and seal["root_uid"] == 0
            and not seal["root_mode"] & 0o222,
            "observed production seal required",
        )
        need(
            seal["inventory_hash"] == digest(encoded(members))
            and seal["files_checked"] == sorted(members),
            "observed exact inventory",
        )
        observed = obs["mounts"][mount]
        need(
            observed["source_root"] == str(NEW / suffix) and "ro" in observed["mount_options"],
            "observed deployment bind source/read-only mount",
        )
    need(
        obs["authority_selector_present"] is False and obs["runtime_authority_present"] is False,
        "observed authority-free mounts",
    )
    need(
        preflight["native_calls"] == 0 and preflight["authority_resolved"] is False,
        "authority-free preflight",
    )
    need(
        preflight["private_test"] is False and bool(preflight["all_module_origins"]),
        "private tests are not placement",
    )
    need(preflight["helper_origins"] == c["helper_imports"], "observed exact helper origins")


DECISION_FIELDS = {
    "format",
    "accepted_by",
    "reply_verbatim",
    "accepted",
    "disposition",
    "conditions",
    "decision_id",
    "scope",
    "amendment_hash",
    "policy_hash",
    "binding",
    "publication",
}


def check_decision(decision, candidate_bytes, publication):
    need(set(decision) == DECISION_FIELDS, "exact decision schema fields")
    need(
        decision["binding"] == identity(candidate_bytes) and decision["publication"] == publication,
        "decision exact candidate",
    )
    c = json.loads(candidate_bytes)
    need(
        decision["format"] == "uarch-k2-combined-human-decision/2"
        and decision["accepted_by"] == "Javid (@jjaffari)",
        "actual human decision required",
    )
    need(
        type(decision["reply_verbatim"]) is str and bool(decision["reply_verbatim"].strip()),
        "verbatim human reply required",
    )
    need(
        decision["accepted"] is True
        and decision["disposition"] == "accepted-unconditional"
        and decision["conditions"] == [],
        "unresolved conditions/rejection cannot authorize",
    )
    need(
        decision["decision_id"] == c["decision_id"] and decision["policy_hash"] == c["policy_hash"],
        "exact decision/policy identity",
    )
    need(
        decision["scope"] == "isolated-protected-runtime-placement-preflight-and-798-call-restart",
        "exact bounded approval",
    )
    need(decision["amendment_hash"] == c["amendment_hash"], "exact normative text")


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
    check_decision(decision, candidate_bytes, publication)
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
    check_preflight(read(directory / "preflight.json"), candidate_bytes, publication)
    return {
        **binding,
        "runtime_selector_hash": digest((directory / "selector.json").read_bytes()),
        "release_hash": digest((directory / "release.json").read_bytes()),
        "publication": publication,
        "decision_commit": selector["decision_commit"],
        "placement_commit": selector["placement_commit"],
    }
