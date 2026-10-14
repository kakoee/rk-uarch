"""Select a short CI test run only for an entirely Markdown documentation diff."""

import json
import os
import re
import subprocess
from pathlib import Path, PurePosixPath


def documentation_path(path: str) -> bool:
    """Data, executable examples and unknown paths always need full CI."""
    p = PurePosixPath(path)
    return p.suffix == ".md" and (
        path == "README.md"
        or path.startswith("docs/")
        or path.startswith("rk-sim-side/prompts/")
    )


def documentation_only(root: Path, event_name: str, event: dict) -> bool:
    """Compare the whole push or PR merge checkout; uncertainty means full CI."""
    if event_name == "push":
        base = event.get("before")
    elif event_name == "pull_request":
        base = event.get("pull_request", {}).get("base", {}).get("sha")
    else:
        return False
    if not isinstance(base, str) or not re.fullmatch(r"[0-9a-f]{40}", base):
        return False
    if base == "0" * 40:
        return False

    def git(*args: str) -> bytes:
        return subprocess.check_output(["git", *args], cwd=root, stderr=subprocess.PIPE)

    try:
        # The PR checkout is GitHub's merge commit, so base must be its ancestor.
        # Force pushes, missing history and unrecognized events use the full path.
        git("merge-base", "--is-ancestor", base, "HEAD")
        # Disable rename detection so both the source and destination are classified.
        names = git("diff", "--no-renames", "--name-only", "-z", base, "HEAD")
        paths = [p.decode("utf-8") for p in names.split(b"\0") if p]
        if not paths or not all(documentation_path(p) for p in paths):
            return False
        # Do not treat symlinks, submodules or executable-mode changes as prose.
        for revision in (base, "HEAD"):
            entries = git("ls-tree", "-z", revision, "--", *paths).split(b"\0")
            if any(e and not e.startswith(b"100644 blob ") for e in entries):
                return False
    except (subprocess.CalledProcessError, OSError, UnicodeError):
        return False
    return True


def main() -> None:
    try:
        event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
        short = isinstance(event, dict) and documentation_only(
            Path.cwd(), os.environ.get("GITHUB_EVENT_NAME", ""), event
        )
    except (KeyError, OSError, ValueError, AttributeError):
        short = False
    value = str(short).lower()
    with Path(os.environ["GITHUB_OUTPUT"]).open("a") as output:
        output.write(f"docs_only={value}\n")
    print(f"docs_only={value}: {'Markdown documentation checks' if short else 'full CI'}")


if __name__ == "__main__":
    main()
