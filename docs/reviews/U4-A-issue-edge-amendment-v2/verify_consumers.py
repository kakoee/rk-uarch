"""Read-only replay of focused consumers against an exact private patched export."""

import hashlib
import json
import sys
from pathlib import Path


def main() -> None:
    package = Path(__file__).resolve().parent
    source = Path(sys.argv[1]).resolve()
    manifest = json.loads((package / "manifest.json").read_text())
    for row in manifest["files"]:
        assert (
            hashlib.sha256((source / row["path"]).read_bytes()).hexdigest()
            == row["postimage_sha256"]
        ), row["path"]
    sys.path[:0] = [str(source), str(source / "contract"), str(source / "src")]
    from uarch_contract import mapped

    from validation.component import observations_v3

    assert Path(mapped.__file__).is_relative_to(source)
    assert Path(observations_v3.__file__).is_relative_to(source)
    expected = json.loads(
        (source / "docs/reviews/U4-B-component-stage2-v1/first-use-bindings.json").read_text()
    )["observation_contract"]
    rows = []
    for dependent in ("r00", "r01"):
        folder = package / "private-probes" / dependent
        job = json.loads((folder / "job.json").read_bytes())
        debug = (folder / "debug.json").read_bytes()
        assert debug == (folder / "release.json").read_bytes()
        for mode in ("debug", "release"):
            result = json.loads((folder / f"{mode}.json").read_bytes())
            mapped.validate_result(result, mapped.MappedEngineJob.model_validate(job))
            observations_v3.check_v3(job, result, expected)
            rows.append({"case": dependent, "mode": mode, "both_consumers": "pass"})
    job = json.loads((package / "private-probes/r00/job.json").read_bytes())
    forged = json.loads((package / "private-probes/consistent-ineligible-first.json").read_bytes())
    mapped.validate_result(forged, mapped.MappedEngineJob.model_validate(job))
    try:
        observations_v3.check_v3(job, forged, expected)
    except ValueError as error:
        assert "opportunity eligible grants" in str(error)
        rows.append({"forgery": "structural pass; independent eligibility refusal"})
    else:
        raise AssertionError("ineligible grant accepted")
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
