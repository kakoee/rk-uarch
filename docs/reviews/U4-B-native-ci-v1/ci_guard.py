"""Proposal-only CI receipt guards; no native build is invoked by this module."""

import json
import re
import sys
from collections import Counter
from pathlib import Path


def check_source(root: Path, metadata: dict) -> None:
    members = set(metadata["workspace_members"])
    packages = [p for p in metadata["packages"] if p["id"] in members]
    if not members or {p["id"] for p in packages} != members:
        raise ValueError("empty or incomplete workspace")
    for package in packages:
        sources = [Path(t["src_path"]) for t in package["targets"] if t.get("test")]
        if not sources or any(
            not p.resolve().is_relative_to(root.resolve())
            or not p.is_file()
            or not p.read_text().strip()
            for p in sources
        ):
            raise ValueError("missing local source or test target")


def listed_tests(output: str) -> Counter:
    return Counter(re.findall(r"^(.+): test$", output, re.MULTILINE))


def check_tests(listing: str, output: str, required: list[str]) -> None:
    expected = Counter(required)
    if not expected or listed_tests(listing) != expected:
        raise ValueError("empty or changed frozen test inventory")
    passed = Counter(re.findall(r"^test (.+) \.\.\. ok$", output, re.MULTILINE))
    summaries = re.findall(
        r"^test result: (\w+)\. (\d+) passed; (\d+) failed; "
        r"(\d+) ignored;",
        output,
        re.MULTILINE,
    )
    if (
        passed != expected
        or not summaries
        or any(
            status != "ok" or int(failed) or int(ignored)
            for status, _, failed, ignored in summaries
        )
        or sum(int(n) for _, n, _, _ in summaries) != sum(expected.values())
    ):
        raise ValueError("missing, ignored, failing or incomplete test execution")


def main():
    mode, *args = sys.argv[1:]
    if mode == "source":
        root, metadata = args
        check_source(Path(root), json.loads(Path(metadata).read_text()))
    elif mode == "tests":
        listing, output, required = args
        check_tests(
            Path(listing).read_text(),
            Path(output).read_text(),
            json.loads(Path(required).read_text()),
        )
    else:
        raise ValueError("unknown guard mode")


if __name__ == "__main__":
    main()
