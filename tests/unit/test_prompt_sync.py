"""build-spec §8 and docs/prompts/ carry the same prompt texts, byte for byte."""
import re
from pathlib import Path

DOCS = Path(__file__).resolve().parents[2] / "docs"
BLOCK = re.compile(r"```text\n(.*?)\n```", re.S)


def _prompt_files() -> list[Path]:
    return sorted(p for p in (DOCS / "prompts").glob("*.md") if not p.name.startswith("TEMPLATE"))


def test_every_prompt_text_appears_verbatim_in_build_spec_section_8() -> None:
    spec = (DOCS / "build-spec.md").read_text()
    section8 = spec[spec.index("## §8"):]
    for f in _prompt_files():
        blocks = BLOCK.findall(f.read_text())
        assert blocks, f"{f.name} has no text block"
        for b in blocks:
            assert b in section8, f"{f.name}: text block differs from build-spec §8"
