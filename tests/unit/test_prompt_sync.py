"""build-spec §8 and docs/prompts/ carry the same prompt texts, byte for byte.

Each §8 section (`### <title>`) has exactly one prompt file whose first line is `# <title>`,
and that file's text blocks equal the section's, in order. No prompt file lacks a section.
"""
import re
from pathlib import Path

import pytest

DOCS = Path(__file__).resolve().parents[2] / "docs"
BLOCK = re.compile(r"```text\n(.*?)\n```", re.S)


def _sections() -> dict[str, list[str]]:
    spec = (DOCS / "build-spec.md").read_text()
    section8 = spec[spec.index("## §8"):]
    heads = list(re.finditer(r"^### (.+)$", section8, re.M))
    out: dict[str, list[str]] = {}
    for i, h in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(section8)
        out[h.group(1).strip()] = BLOCK.findall(section8[h.end():end])
    return out


def _prompt_files() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for p in sorted((DOCS / "prompts").glob("*.md")):
        if p.name.startswith("TEMPLATE"):
            continue
        text = p.read_text()
        title = text.splitlines()[0].removeprefix("# ").strip()
        assert title not in out, f"{p.name}: title {title!r} is used by two prompt files"
        out[title] = BLOCK.findall(text)
    return out


def test_every_section_8_prompt_has_a_file_with_equal_text_blocks() -> None:
    files = _prompt_files()
    for title, blocks in _sections().items():
        assert blocks, f"build-spec §8 section {title!r} has no text block"
        assert title in files, f"no docs/prompts/ file titled {title!r}"
        assert files[title] == blocks, f"{title!r}: text blocks differ from build-spec §8"


def test_every_prompt_file_has_a_section_8_entry() -> None:
    sections = _sections()
    for title in _prompt_files():
        assert title in sections, f"docs/prompts/ file {title!r} has no build-spec §8 section"


@pytest.mark.parametrize(
    "shipped,canonical",
    [
        ("P18-characterized-c2-cost.md", "U-P19-rk-sim-P18-characterized-C2-cost.md"),
        ("P19-stipulations-and-chip-views.md", "U-P20-rk-sim-P19-stipulations-and-chip-views.md"),
    ],
)
def test_shipped_rk_sim_prompt_mirrors(shipped: str, canonical: str) -> None:
    """Shipping a stale boundary prompt can lose required contract checks."""
    expected = BLOCK.findall((DOCS / "prompts" / canonical).read_text())
    actual = BLOCK.findall((DOCS.parent / "rk-sim-side/prompts" / shipped).read_text())
    assert expected, f"{canonical}: missing canonical text block"
    assert actual == expected, f"{shipped}: text blocks differ from {canonical}"
