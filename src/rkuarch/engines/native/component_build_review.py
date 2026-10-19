"""Finite component provenance adapter over B's independent ordinary-build consumer.

Only declared inputs/observed outputs are checked. No build, startup, read closure,
reviewer acceptance or authority is created by these records or functions.
"""

from __future__ import annotations

import hashlib
import io
import re
import tarfile
from pathlib import Path, PurePosixPath
from typing import Any

from uarch_contract.hashing import canonical_json, content_hash, sha256, strict_json_loads

from .component_construction import invocation
from .component_records import ComponentBuildInputsV3, ComponentBuildReceiptV2, ComponentBuildTrust
from .host import _open, _read, _require
from .records import FileBinding, ToolInputs

SOURCE = "inputs/source/"
CACHE = "inputs/cache/"
PYTHON = "inputs/python/"
CACHE_RECORD = "docs/reviews/U4-A-K2-C1-precise-v1/cache-inventory.json"
CACHE_PIN = "sha256:ce219674649c7e77ce84806db559d8473a6c6a62b5bad7aa3ff0e93486f30148"
TOOLS_PIN = "sha256:db8b8956f0c060416d0d3c6c11f8eccc6b3ece7433b5075cb093e602febcb73d"
PRODUCER = "native/tools/component_runtime_candidate.py"
GUARD_FILES = ("intent.json", "pre-existing.json", "created.json", "started.json", "cleanup.json")


def file_binding(root: Path, name: str) -> dict[str, str]:
    binding = FileBinding(path=name, byte_hash="sha256:" + "0" * 64)
    import os

    with _open(root, binding.path) as fd:
        _require(os.fstat(fd).st_size <= 256 * 1024**2, "bounded provenance input")
        with os.fdopen(os.dup(fd), "rb") as stream:
            raw = stream.read()
    return {"path": name, "byte_hash": sha256(raw)}


def _prefixed(prefix: str, item: dict[str, Any]) -> dict[str, str]:
    return {"path": prefix + item["path"], "byte_hash": item["byte_hash"]}


def _git_object(kind: str, data: bytes) -> str:
    return hashlib.sha1(kind.encode() + b" " + str(len(data)).encode() + b"\0" + data).hexdigest()


def archive_tree(
    archive: bytes, commit: bytes, expected_commit: str
) -> tuple[str, dict[str, bytes]]:
    """Derive Git tree from a retained export and verify its exact raw commit object.

    No git invocation or archive extraction. Unsupported archive kinds refuse.
    This assumes ordinary unfiltered git archive; export-subst/ignore would fail
    the exact tree check rather than silently weakening it.
    """
    _require(_git_object("commit", commit) == expected_commit, "actual source commit object")
    first = commit.split(b"\n", 1)[0]
    _require(re.fullmatch(b"tree [0-9a-f]{40}", first) is not None, "source commit tree")
    expected_tree = first[5:].decode()
    entries: dict[str, tuple[str, bytes]] = {}
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:*") as stream:
        for member in stream:
            name = member.name.rstrip("/")
            path = PurePosixPath(name)
            _require(
                bool(name)
                and not path.is_absolute()
                and ".." not in path.parts
                and str(path) == name
                and name not in entries,
                "safe unique archive paths",
            )
            if member.isdir():
                continue
            if member.issym():
                data, mode = member.linkname.encode(), "120000"
            else:
                _require(member.isfile(), "regular source archive members")
                extracted = stream.extractfile(member)
                _require(extracted is not None, "source archive member")
                assert extracted is not None
                data = extracted.read()
                mode = "100755" if member.mode & 0o111 else "100644"
            entries[name] = (mode, data)
    _require(bool(entries), "nonempty source archive")

    def tree(prefix: str) -> str:
        names: dict[str, tuple[str, str]] = {}
        for name, (mode, data) in entries.items():
            if not name.startswith(prefix):
                continue
            head, separator, _ = name[len(prefix) :].partition("/")
            if separator:
                _require(
                    head not in names or names[head][0] == "40000",
                    "archive file/directory collision",
                )
                names[head] = ("40000", "")
            else:
                _require(
                    head not in names or names[head][0] != "40000",
                    "archive file/directory collision",
                )
                names[head] = (mode, _git_object("blob", data))
        rows = []
        for name in sorted(
            names, key=lambda key: (key + ("/" if names[key][0] == "40000" else "")).encode()
        ):
            mode, pin = names[name]
            if mode == "40000":
                pin = tree(prefix + name + "/")
            rows.append(mode.encode() + b" " + name.encode() + b"\0" + bytes.fromhex(pin))
        return _git_object("tree", b"".join(rows))

    actual = tree("")
    _require(actual == expected_tree, "actual source archive/tree join")
    return actual, {name: data for name, (_, data) in entries.items()}


def derive_declaration(root: Path, expected: dict[str, Any], mode: str) -> dict[str, Any]:
    """Derive B's complete expectations from typed payload/BuildInputs anchors."""
    from validation.component.ordinary_build_acceptance import IMAGE, WARNING_POLICY

    def read(item: dict[str, Any]) -> bytes:
        return _read(root, FileBinding.model_validate(item))

    build_file = _prefixed(SOURCE, expected["build_inputs"])
    build = ComponentBuildInputsV3.model_validate_json(read(build_file))
    _require(
        content_hash(build) == expected["build_input_hash"], "ordinary BuildInputs content join"
    )
    _require(build.source_commit == expected["source_commit"], "ordinary source commit join")
    _require(
        [v.model_dump(mode="json") for v in build.source_files] == expected["source_files"],
        "ordinary complete source inventory",
    )
    _require(
        [v.model_dump(mode="json") for v in build.mode_configs] == expected["mode_configs"],
        "ordinary mode declarations",
    )
    _require(
        list(build.generated_identity_output_paths) == expected["generated_identity_output_paths"],
        "ordinary generated paths",
    )
    tools_file = _prefixed(SOURCE, build.tool_inputs_file.model_dump(mode="json"))
    _require(tools_file["byte_hash"] == TOOLS_PIN, "accepted ordinary ToolInputs bytes")
    tools = ToolInputs.model_validate_json(read(tools_file))
    _require(
        content_hash(tools) == build.tool_inputs_hash == expected["tool_inputs_hash"],
        "ordinary tool content join",
    )
    _require(
        build.tool_inputs_file.model_dump(mode="json") == expected["tool_inputs"],
        "ordinary tool binding join",
    )
    trust_file = _prefixed(SOURCE, build.trust_file.model_dump(mode="json"))
    trust = ComponentBuildTrust.model_validate_json(read(trust_file))
    _require(content_hash(trust) == build.trust_hash, "ordinary generated trust join")
    model = [
        v.model_dump(mode="json") for v in build.source_files if v.path in build.model_source_paths
    ]
    engine = expected["engine"]
    _require(
        engine["implementation_hash"] == content_hash(build)
        and engine["compiler_lock_hash"] == content_hash(tools)
        and engine["model"]["implementation_hash"]
        == content_hash(model)
        == build.model_inputs_hash,
        "ordinary full engine/generated identity join",
    )
    archive = file_binding(root, "inputs/source.tar")
    commit = file_binding(root, "inputs/source-commit.raw")
    tree, members = archive_tree(read(archive), read(commit), build.source_commit)
    sources = [_prefixed(SOURCE, v.model_dump(mode="json")) for v in build.source_files]
    for source_item in build.source_files:
        _require(
            source_item.path in members
            and sha256(members[source_item.path]) == source_item.byte_hash,
            "source inventory/archive bytes",
        )
    tool_files = [trust_file]
    for value in tools.model_dump(mode="json").values():
        if isinstance(value, dict) and set(value) == {"path", "byte_hash"}:
            tool_files.append(_prefixed(SOURCE, value))
    tool_files += [
        _prefixed(SOURCE, item.model_dump(mode="json"))
        for item in (trust.semantics_file, trust.registry_file, trust.selection, *trust.profiles)
    ]
    # Trust/selection/profile inputs are generated before compilation and separately
    # hash-bound by BuildTrust; all static tool metadata must match the source archive.
    for item in [tools_file, *tool_files]:
        name = item["path"][len(SOURCE) :]
        if name in members:
            _require(sha256(members[name]) == item["byte_hash"], "tool/archive bytes")
        read(item)
    cache_manifest = {"path": SOURCE + CACHE_RECORD, "byte_hash": CACHE_PIN}
    cache = strict_json_loads(read(cache_manifest))
    _require(
        CACHE_RECORD in members and sha256(members[CACHE_RECORD]) == CACHE_PIN,
        "accepted cache/archive join",
    )
    cache_files = [
        {"path": CACHE + name, "byte_hash": "sha256:" + value["sha256"]}
        for name, value in sorted(cache["files"].items())
    ]
    producer = next((item for item in sources if item["path"] == SOURCE + PRODUCER), None)
    _require(producer is not None, "actual generated identity producer")
    assert producer is not None
    generated = file_binding(root, SOURCE + build.generated_identity_output_paths[0])
    generated_bytes = (
        'pub const ENGINE_JSON: &str = r###"'
        + canonical_json(engine)
        + '"###;\npub const TRUST_JSON: &str = r###"'
        + canonical_json(trust)
        + '"###;\n'
    ).encode()
    _require(read(generated) == generated_bytes, "typed generated identity bytes")
    consumers = expected["consumers"]
    _require(
        content_hash(consumers) == expected["consumer_hash"], "ordinary complete consumer identity"
    )
    _require(bool(consumers["files"]), "ordinary nonempty consumer/source closure")
    consumer_files = [_prefixed(SOURCE, item) for item in consumers["files"]]
    source_map = {item["path"]: item["byte_hash"] for item in sources}
    _require(
        all(source_map.get(item["path"]) == item["byte_hash"] for item in consumer_files),
        "ordinary consumer/source closure",
    )
    consumer_files += [
        _prefixed(SOURCE, consumers[key]) for key in ("independent_binding", "observation_contract")
    ]
    consumer_files += [_prefixed(PYTHON, item) for item in consumers["external_files"]]
    consumer_files.append(_prefixed(PYTHON, consumers["python_executable"]))
    roles = {
        "source_archive": [archive, commit],
        "source_files": sources,
        "build_inputs": [build_file],
        "tool_inputs": [tools_file],
        "tool_files": tool_files,
        "dependency_lock": [_prefixed(SOURCE, tools.cargo_lock.model_dump(mode="json"))],
        "cache_manifest": [cache_manifest],
        "cache_files": cache_files,
        "generated_inputs": [generated],
        "producers": [producer],
        "consumers": consumer_files,
    }
    for role, values in roles.items():
        pins: dict[str, str] = {}
        for item in values:
            _require(
                pins.setdefault(item["path"], item["byte_hash"]) == item["byte_hash"],
                "conflicting input role binding",
            )
            read(item)
        roles[role] = [{"path": path, "byte_hash": pin} for path, pin in sorted(pins.items())]
    argv, environment = invocation(expected["mode_configs"], mode)
    return {
        "source_commit": build.source_commit,
        "source_tree": tree,
        "mode": mode,
        "image_digest": IMAGE,
        "argv": argv,
        "environment": environment,
        "inputs": roles,
        "generated_producers": [
            {
                "output": generated,
                "producer": producer,
                "inputs": [build_file, trust_file, tools_file],
            }
        ],
        "cargo_artifact": f"/target/{mode}/uarch-engine",
        "warning_policy": WARNING_POLICY,
    }


def consume_provenance(
    root: Path, record: dict[str, Any], expected: dict[str, Any]
) -> list[FileBinding]:
    """Verify both modes through B, then retain every nested file for host refresh."""
    from native.tools.component_ordinary_build import LIMITS, verify_transport
    from validation.component.ordinary_build_acceptance import consume_build

    _require(
        set(record) == {"format", "subject", "builds", "required_checks_review"},
        "exact component build provenance",
    )
    _require(
        record["format"] == "uarch-component-build-provenance/1",
        "component build provenance version",
    )
    subject = {key: expected[key] for key in ("runtime_payload_byte_hash", "consumer_hash")}
    _require(record["subject"] == subject, "component build provenance subject")
    _require(
        [item["mode"] for item in record["builds"]] == ["debug", "release"],
        "both independent ordinary build modes",
    )
    files: dict[str, FileBinding] = {}

    def read(item: dict[str, Any]) -> bytes:
        binding = FileBinding.model_validate(item)
        _require(
            files.setdefault(binding.path, binding) == binding, "conflicting provenance binding"
        )
        return _read(root, binding)

    for row, executable in zip(record["builds"], expected["executables"], strict=True):
        _require(
            set(row) == {"mode", "root", "expectation", "receipt", "transport"},
            "exact mode provenance row",
        )
        prefix = FileBinding(path=row["root"] + "/file", byte_hash="sha256:" + "0" * 64).path[:-4]
        build_root = root / row["root"]
        _require(
            build_root.resolve().is_relative_to(root.resolve()) and not build_root.is_symlink(),
            "relative ordinary evidence root",
        )
        _require(executable["mode"] == row["mode"], "payload build mode order")
        outer = ComponentBuildReceiptV2.model_validate_json(read(executable["receipt"]))
        _require(
            outer.engine.model_dump(mode="json") == expected["engine"]
            and outer.build_input_hash == expected["build_input_hash"]
            and outer.mode == row["mode"]
            and outer.executable.model_dump(mode="json") == executable["executable"]
            and outer.ordinary_receipt.model_dump(mode="json") == row["receipt"],
            "ordinary payload/receipt/executable join",
        )
        for outer_file in (outer.generated_identity, outer.environment):
            read(outer_file.model_dump(mode="json"))
        _require(
            row["receipt"]["path"] == prefix + "ordinary-build-receipt.json",
            "ordinary receipt root join",
        )
        declaration = derive_declaration(build_root, expected, row["mode"])
        wanted = strict_json_loads(read(row["expectation"]))
        _require(
            wanted["declaration"] == declaration, "typed independently derived ordinary declaration"
        )
        _require(
            executable["executable"] == _prefixed(prefix, wanted["executable"]),
            "ordinary payload actual executable",
        )
        _require(
            all(
                wanted[key] == LIMITS[key] for key in ("timeout_s", "stdout_bytes", "stderr_bytes")
            ),
            "ordinary fixed execution limits",
        )
        generated = declaration["inputs"]["generated_inputs"][0]
        _require(
            outer.generated_identity.path in expected["generated_identity_output_paths"]
            and outer.generated_identity.byte_hash == generated["byte_hash"],
            "ordinary outer generated identity",
        )
        _require(
            strict_json_loads(_read(root, outer.environment)) == declaration["environment"],
            "ordinary outer environment",
        )
        receipt = strict_json_loads(read(row["receipt"]))
        consumed = consume_build(build_root, receipt, wanted)
        for item in consumed["required_files"]:
            read(_prefixed(prefix, item))
        transport = strict_json_loads(read(row["transport"]))
        for item in verify_transport(build_root, transport, declaration, receipt):
            read(_prefixed(prefix, item))
    checks = strict_json_loads(read(record["required_checks_review"]))
    _require(
        set(checks) == {"format", "subject", "required_checks", "evidence"}
        and checks["format"] == "uarch-component-required-checks-review/1"
        and checks["subject"]
        == {
            **subject,
            "build_input_hash": expected["build_input_hash"],
            "executables": expected["executables"],
        }
        and checks["required_checks"]
        == [
            "native-and-python-scope",
            "independent-consumers-and-replay",
            "lint-types-and-clippy-deny-warnings",
        ]
        and bool(checks["evidence"]),
        "independently bound required test/warning review",
    )
    # This is independently reviewed support evidence pinned by runtime-review/2,
    # not a success receipt generated by the build runner or an authority source.
    for item in checks["evidence"]:
        read(item)
    return [files[path] for path in sorted(files)]
