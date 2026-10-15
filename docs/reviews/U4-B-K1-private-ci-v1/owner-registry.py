"""Owner-run, exact-destination publication/readback. Tokens enter only through a TTY."""

import argparse
import getpass
import json
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

IMAGE_ID = "sha256:e9f69f41498334be985ed4d25973fe3fa3f6519e58c73e6a7b8397d871fa0523"
REPOSITORY = "ghcr.io/kakoee/rk-uarch-k1-builder"
TAG = REPOSITORY + ":k1-892b9ee"
PACKAGE = "/users/kakoee/packages/container/rk-uarch-k1-builder"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def identity(user, scope_header, mode):
    scopes = {s.strip() for s in scope_header.split(",") if s.strip()}
    require(user["login"] == "kakoee", "use the approved namespace owner's classic PAT")
    if mode == "publish":
        require(
            "write:packages" in scopes and scopes <= {"read:packages", "write:packages"},
            "publisher requires only write:packages (implied read is allowed)",
        )
    else:
        require(scopes == {"read:packages"}, "reader requires a separate read:packages-only PAT")


def private(package):
    require(package["name"] == "rk-uarch-k1-builder", "wrong package")
    require(package["package_type"] == "container", "wrong package type")
    require(package["visibility"] == "private", "refuse non-private package")


def tag_conflicts(versions):
    for version in versions:
        if "k1-892b9ee" in version["metadata"]["container"]["tags"]:
            require(version["name"] == IMAGE_ID, "existing tag differs; do not overwrite it")


def image(info):
    require(len(info) == 1 and info[0]["Id"] == IMAGE_ID, "verified local image identity differs")
    require(info[0]["Os"] == "linux" and info[0]["Architecture"] == "amd64", "wrong platform")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["publish", "check-reader"])
    parser.add_argument("receipts", type=Path, help="new directory outside the checkout")
    parser.add_argument("--digest", help="observed GHCR repository@sha256 for readback")
    args = parser.parse_args()
    if args.mode == "check-reader":
        require(
            bool(re.fullmatch(re.escape(REPOSITORY) + r"@sha256:[0-9a-f]{64}", args.digest or "")),
            "supply the observed GHCR digest",
        )
    require(sys.stdin.isatty() and sys.stderr.isatty(), "use an interactive trusted terminal")
    require(
        not args.receipts.resolve().is_relative_to(Path(__file__).resolve().parents[3]),
        "put owner receipts outside the checkout",
    )
    args.receipts.mkdir(mode=0o700, parents=False, exist_ok=False)
    token = getpass.getpass("Owner classic PAT (hidden; never written to receipts): ")

    def api(path):
        require(path.startswith("/") and not path.startswith("//"), "invalid API path")
        request = urllib.request.Request(
            "https://api.github.com" + path,
            headers={
                "Authorization": "Bearer " + token,
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "rk-uarch-owner-handoff",
            },
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.load(response), response.headers.get("X-OAuth-Scopes", "")

    def pages(path):
        result = []
        page = 1
        while True:
            data, _ = api(path + ("&" if "?" in path else "?") + f"per_page=100&page={page}")
            require(isinstance(data, list), "invalid paginated package response")
            result.extend(data)
            if len(data) < 100:
                return result
            page += 1

    def record(name, value):
        (args.receipts / (name + ".json")).write_text(json.dumps(value, indent=2) + "\n")

    user, scopes = api("/user")
    identity(user, scopes, args.mode)
    record("credential-metadata", {"login": user["login"], "scopes": scopes, "mode": args.mode})
    owned = pages("/user/packages?package_type=container")
    found = [p for p in owned if p["name"] == "rk-uarch-k1-builder"]
    require(len(found) <= 1, "ambiguous package")
    if found:
        private(found[0])
        versions = pages(PACKAGE + "/versions")
        if args.mode == "publish":
            tag_conflicts(versions)
        record(
            "package-before",
            {
                key: found[0].get(key)
                for key in ["name", "package_type", "visibility", "repository"]
            },
        )
    else:
        require(args.mode == "publish", "reader cannot find approved private package")
        record("package-before", {"absent_in_complete_authenticated_owner_listing": True})

    def command(name, argv, secret_input=None):
        result = subprocess.run(argv, input=secret_input, capture_output=True, check=False)
        # argv contains no credentials. Docker login takes the token only via stdin.
        record(
            name,
            {
                "argv": argv,
                "exit": result.returncode,
                "stdout": result.stdout.decode(errors="replace").replace(token, "[REDACTED]"),
                "stderr": result.stderr.decode(errors="replace").replace(token, "[REDACTED]"),
            },
        )
        require(result.returncode == 0, name + " failed; inspect non-secret receipt")
        return result.stdout

    original = json.loads(command("local-image", ["docker", "image", "inspect", IMAGE_ID]))
    image(original)
    with tempfile.TemporaryDirectory(prefix="u4-owner-ghcr-") as config:
        docker = ["docker", "--config", config]
        command(
            "login",
            [*docker, "login", "ghcr.io", "--username", "kakoee", "--password-stdin"],
            token.encode(),
        )
        if args.mode == "publish":
            # No build, config modification, added layer, secondary tag or other destination.
            command("tag", [*docker, "tag", IMAGE_ID, TAG])
            command("push", [*docker, "push", TAG])
        subject = TAG if args.mode == "publish" else args.digest
        command("pull", [*docker, "pull", "--platform", "linux/amd64", subject])
        actual = json.loads(command("published-image", [*docker, "image", "inspect", subject]))
        image(actual)
        require(actual[0]["RootFS"] == original[0]["RootFS"], "published image layers differ")
        digests = [d for d in actual[0]["RepoDigests"] if d.startswith(REPOSITORY + "@sha256:")]
        require(len(digests) == 1, "ambiguous published digest")
        if args.mode == "check-reader":
            require(digests == [args.digest], "reader pulled a different digest")
        current, _ = api(PACKAGE)
        private(current)
        record(
            "result",
            {
                "mode": args.mode,
                "image_id": IMAGE_ID,
                "registry_image": digests[0],
                "visibility": current["visibility"],
                "repository": current.get("repository"),
                "owner_ui_acl_verification_still_required": True,
            },
        )
    print("Verified registry pull; temporary Docker credentials removed.")
    print("Non-secret receipts:", args.receipts)


if __name__ == "__main__":
    main()
