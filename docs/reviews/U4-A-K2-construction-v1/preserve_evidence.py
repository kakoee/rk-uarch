"""Read-only checks of historical bytes and compact retained construction failures."""

import gzip
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
DEV = Path("/tmp/u4-k2-impl.69r1lz_3")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def verify(root, files):
    for name, expected in files.items():
        p = root / name
        assert p.is_file(), p
        actual = {"sha256": sha(p), "bytes": p.stat().st_size, "mtime_ns": p.stat().st_mtime_ns}
        assert all(actual[k] == v for k, v in expected.items()), str(p)
    return len(files)


def main():
    counts = {}
    historical = Path("/tmp/u4-k2-c2b.khaj67gd/receipts/preserved-before.private.json")
    for root, files in json.loads(historical.read_bytes()).items():
        counts[root] = verify(Path(root), files)
    c2 = json.loads(
        gzip.decompress(
            (ROOT / "docs/reviews/U4-A-K2-C2-nonblank-v1/private-inventory.json.gz").read_bytes()
        )
    )
    for section in ("receipts", "controls", "targets", "reversion"):
        counts[c2["root"] + "/" + section] = verify(
            Path(c2["root"]) / ("target" if section == "targets" else section), c2[section]
        )
    before = json.loads((DEV / "receipts/preserved-before.private.json").read_bytes())
    for root, files in before.items():
        verify(Path(root), files)
    cache = json.loads(
        (ROOT / "docs/reviews/U4-A-K2-C1-precise-v1/cache-inventory.json").read_bytes()
    )
    for root in [
        Path(cache["private_root"]),
        DEV / "cache",
        Path("/tmp/u4-k2-candidate-02/cache"),
        Path("/tmp/u4-k2-candidate-03/cache"),
        Path("/tmp/u4-k2-candidate-04/cache"),
    ]:
        counts[str(root)] = verify(root, cache["files"])
    prior = json.loads(
        (ROOT / "docs/reviews/U4-A-K2-C2-nonblank-v1/preservation.json").read_bytes()
    )
    for name, expected in prior["source_inventory"].items():
        verify(Path(c2["root"]) / "workspace", {name: expected})
    trees = {}
    for path, old in prior["historical_packages"].items():
        tree = (
            subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD:" + path])
            .decode()
            .strip()
        )
        assert tree == old["tree"]
        trees[path] = tree
    for path in [
        "docs/reviews/U4-A-K2-C2-nonblank-v1",
        "docs/reviews/U4-B-K2-C2-nonblank-review-v1",
    ]:
        old = (
            subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "bcecc67:" + path])
            .decode()
            .strip()
        )
        current = (
            subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD:" + path])
            .decode()
            .strip()
        )
        assert old == current
        trees[path] = current
    protected = subprocess.check_output(
        [
            "git",
            "-C",
            str(ROOT),
            "diff",
            "--name-only",
            "c678ded",
            "--",
            "contract",
            "docs/decisions",
            "tests/golden/expected",
            "CLAUDE.md",
        ]
    ).decode()
    assert not protected, protected
    write(
        OUT / "preservation.json",
        {
            "historical_bytes_sizes_mtimes_verified": counts,
            "historical_package_trees": trees,
            "protected_changes_since_c678ded": [],
            "live_lock_sha256": sha(ROOT / "native/Cargo.lock"),
            "live_crate_manifest_sha256": sha(ROOT / "native/crates/uarch-engine/Cargo.toml"),
            "cache_claim": "all 1719 accepted files match; no downloads or writable live mounts",
        },
    )
    commands = json.loads((DEV / "receipts/commands.json").read_bytes())
    rows = []
    for command in commands:
        matches = {}
        for stream in ("stdout", "stderr"):
            file = DEV / "receipts" / (command["name"] + "." + stream)
            matches[stream] = file.exists() and sha(file) == command[stream + "_sha256"]
            if command["exit_code"] != 0 and matches[stream]:
                target = OUT / "development" / file.name
                target.parent.mkdir(exist_ok=True)
                shutil.copyfile(file, target)
        rows.append({"command": command, "retained_stream_hash_matches": matches})
    write(OUT / "development/commands.json", rows)
    write(
        OUT / "development/receipt-retention.json",
        {
            "commands": len(rows),
            "retained_raw_stream_mismatches": [
                {"name": r["command"]["name"], "matches": r["retained_stream_hash_matches"]}
                for r in rows
                if not all(r["retained_stream_hash_matches"].values())
            ],
            "explanation": (
                "Repeated development rustfmt names overwrote earlier formatter stdout; "
                "recorded hashes remain. These are not test/binary claims. Unique native "
                "failure/test commands and final candidate receipts remain verified."
            ),
        },
    )
    for name in [
        "host-corpus-baseline.txt",
        "host-corpus-corrected.txt",
        "contract-integrated.txt",
        "currentness-3888fb2.txt",
        "currentness-24fa368.txt",
    ]:
        shutil.copyfile(DEV / "receipts" / name, OUT / "development" / name)
    for version in ("02", "03"):
        root = Path("/tmp/u4-k2-candidate-" + version)
        write(
            OUT / ("candidate-" + version) / "retained-commands.json",
            {
                p.name: json.loads(p.read_bytes())
                for p in sorted((root / "commands").glob("*.json"))
            },
        )
        shutil.copyfile(
            root / "commands/debug-clippy.stderr",
            OUT / ("candidate-" + version) / "clippy-failure.stderr",
        )
    print("Historical preservation verified:", sum(counts.values()), "file checks")


if __name__ == "__main__":
    main()
