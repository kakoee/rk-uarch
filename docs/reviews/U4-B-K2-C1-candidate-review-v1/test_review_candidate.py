"""Host-only refusals on actual candidate data, with no Cargo invocation or writes."""

import copy
import importlib.util
import json
import sys
import tomllib
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("b_c1_review", HERE / "review_candidate.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
assert Path(m.__file__).resolve() == HERE / "review_candidate.py"
ROOT = Path(sys.argv.pop(1)).resolve()
PACKAGE = ROOT / "docs/reviews/U4-A-K2-C1-precise-v1"
PLAN = json.loads(
    (ROOT / "docs/reviews/U4-A-K2-semantic-construction-v1/construction-plan.json").read_bytes()
)
ENTRIES = m.tuples(tomllib.loads((PACKAGE / "candidate.Cargo.lock").read_text())["package"])


class CandidateControls(unittest.TestCase):
    def test_exact_actual_candidate(self):
        m.retained_gate(ROOT)(ENTRIES, PLAN)

    def test_lock_refusals(self):
        gate = m.retained_gate(ROOT)
        mutations = {}
        for label, name in [("missing_old", "r-efi"), ("missing_new", "sha2")]:
            mutations[label] = [x for x in ENTRIES if x["name"] != name]
        mutations["duplicate"] = ENTRIES + [ENTRIES[0]]
        mutations["extra"] = ENTRIES + [{"name": "unapproved", "version": "0.1.0"}]
        for field, value in [
            ("checksum", "0" * 64),
            ("source", "git+https://invalid.invalid"),
            ("version", "99.0.0"),
        ]:
            bad = copy.deepcopy(ENTRIES)
            bad[0][field] = value
            mutations[field] = bad
        for name in ("input-rejected.Cargo.lock", "after-crypto-common.Cargo.lock"):
            mutations[name] = m.tuples(tomllib.loads((PACKAGE / name).read_text())["package"])
        for name, bad in mutations.items():
            with self.subTest(name=name), self.assertRaises(AssertionError):
                gate(bad, PLAN)
        gate(ENTRIES, PLAN)

    def test_actual_full_and_linux_graphs(self):
        for view in ("full", "linux"):
            meta = m.read(PACKAGE / f"metadata-{view}.stdout")
            baseline = m.read(
                ROOT / f"docs/reviews/U4-K1-installed-verification-v1/cargo-metadata.{view}.json"
            )
            m.check_graph(meta, baseline, PLAN, ENTRIES, linux=view == "linux")

    def test_graph_refusals(self):
        meta = m.read(PACKAGE / "metadata-full.stdout")
        baseline = m.read(
            ROOT / "docs/reviews/U4-K1-installed-verification-v1/cargo-metadata.full.json"
        )
        ids = {p["name"]: p["id"] for p in meta["packages"]}
        mutations = {}
        for label in (
            "missing_full_only",
            "wrong_source",
            "missing_numeric_feature",
            "extra_sha_feature",
            "edge_drift",
        ):
            bad = copy.deepcopy(meta)
            if label == "missing_full_only":
                bad["resolve"]["nodes"] = [
                    n for n in bad["resolve"]["nodes"] if n["id"] != ids["r-efi"]
                ]
            elif label == "wrong_source":
                bad["packages"][0]["source"] = "git+https://invalid.invalid"
            elif label == "missing_numeric_feature":
                next(n for n in bad["resolve"]["nodes"] if n["id"] == ids["serde_json"])[
                    "features"
                ].remove("arbitrary_precision")
            elif label == "extra_sha_feature":
                next(n for n in bad["resolve"]["nodes"] if n["id"] == ids["sha2"])[
                    "features"
                ].append("asm")
            else:
                next(n for n in bad["resolve"]["nodes"] if n["id"] == ids["generic-array"])[
                    "deps"
                ] = []
            mutations[label] = bad
        for name, bad in mutations.items():
            with self.subTest(name=name), self.assertRaises(AssertionError):
                m.check_graph(bad, baseline, PLAN, ENTRIES)
        m.check_graph(meta, baseline, PLAN, ENTRIES)

    def test_declaration_is_not_a_licence_text(self):
        for data in (b"MIT OR Apache-2.0", b"Permission is hereby granted, free of charge"):
            with self.subTest(data=data), self.assertRaises(AssertionError):
                m.licence_texts({"LICENSE": data})


if __name__ == "__main__":
    unittest.main(verbosity=2)
