import tempfile
import unittest
from pathlib import Path

from ci_guard import check_source, check_tests

LISTING = "clock::edge: test\nowner::zero: test\n\n2 tests, 0 benchmarks\n"
OUTPUT = (
    "running 2 tests\ntest clock::edge ... ok\ntest owner::zero ... ok\n"
    "test result: ok. 2 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;\n"
)
REQUIRED = ["clock::edge", "owner::zero"]


class GuardControls(unittest.TestCase):
    def test_nonempty_control(self):
        check_tests(LISTING, OUTPUT, REQUIRED)

    def test_empty_missing_ignored_failed_and_filter_refuse(self):
        for listing, output, required in [
            ("", "", []),
            ("", OUTPUT, REQUIRED),
            (LISTING, "", REQUIRED),
            (LISTING, OUTPUT.replace("zero ... ok", "zero ... ignored"), REQUIRED),
            (LISTING, OUTPUT.replace("0 failed", "1 failed"), REQUIRED),
            (LISTING, OUTPUT.replace("0 ignored", "1 ignored"), REQUIRED),
            (LISTING, OUTPUT.replace("2 passed", "1 passed"), REQUIRED),
            (LISTING, OUTPUT.replace("test owner::zero ... ok\n", ""), REQUIRED),
        ]:
            with self.assertRaises(ValueError):
                check_tests(listing, output, required)

    def test_duplicate_or_changed_inventory_refuses(self):
        with self.assertRaises(ValueError):
            check_tests(LISTING + "clock::edge: test\n", OUTPUT, REQUIRED)
        with self.assertRaises(ValueError):
            check_tests(LISTING, OUTPUT, ["replacement"])

    def test_source_guards(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            src = root / "lib.rs"
            src.write_text("#[test] fn example() {}\n")
            metadata = {
                "workspace_members": ["engine"],
                "packages": [{"id": "engine", "targets": [{"src_path": str(src), "test": True}]}],
            }
            check_source(root, metadata)
            src.write_text("")
            with self.assertRaises(ValueError):
                check_source(root, metadata)
            src.unlink()
            with self.assertRaises(ValueError):
                check_source(root, metadata)
            with self.assertRaises(ValueError):
                check_source(root, {"workspace_members": [], "packages": []})


if __name__ == "__main__":
    unittest.main()
