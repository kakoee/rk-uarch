"""Deterministic in-memory presentation of already assessed metrics.

This B2 seam is not the file-based report entry point. A2's reviewed loader and complete
runtime context are required before wiring CLI/table reports or per-op roofline plots.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, nodes
from uarch_contract.hashing import verify_identity
from uarch_contract.report_context import RenderSpec

from .badged import Badged

TEMPLATES = Path(__file__).with_name("templates")


def lint_template(source: str) -> None:
    """Only escaped label text and Badged.text may reach this restricted metric template."""
    tree = Environment().parse(source)
    for output in tree.find_all(nodes.Output):
        for item in output.nodes:
            if isinstance(item, nodes.TemplateData):
                continue
            if isinstance(item, nodes.Name) and item.name == "label":
                continue
            if (
                isinstance(item, nodes.Getattr)
                and isinstance(item.node, nodes.Name)
                and item.node.name == "metric"
                and item.attr == "text"
            ):
                continue
            if (
                isinstance(item, nodes.Filter)
                and item.name == "safe"
                and isinstance(item.node, nodes.Getattr)
                and isinstance(item.node.node, nodes.Name)
                and item.node.node.name == "plot"
                and item.node.attr == "svg"
            ):
                continue
            if (
                isinstance(item, nodes.Getattr)
                and isinstance(item.node, nodes.Name)
                and item.node.name == "plot"
                and item.attr == "markdown"
            ):
                continue
            raise ValueError("UnbadgedTemplateValue: only Badged.text is permitted")


def _markdown(value: str) -> str:
    for token in ("\\", "`", "*", "_", "[", "]", "<", ">", "#", "|"):
        value = value.replace(token, "\\" + token)
    return value.replace("\n", " ").replace("\r", " ")


def render_metrics(metrics: Mapping[str, Badged], permissions: RenderSpec) -> tuple[str, str]:
    verify_identity(permissions, "render_hash")
    for metric in metrics.values():
        if not isinstance(metric, Badged) or metric.render_hash != permissions.render_hash:
            raise ValueError("RenderPermissionMismatch: use the same bound RenderSpec")
    env = Environment(
        loader=FileSystemLoader(TEMPLATES),
        undefined=StrictUndefined,
        autoescape=True,
        keep_trailing_newline=True,
    )
    items = tuple(sorted(metrics.items()))
    for name in ("report.html.j2", "report.md.j2"):
        lint_template((TEMPLATES / name).read_text())
    html = env.get_template("report.html.j2").render(metrics=items)
    # The Markdown twin consumes escaped guarded text through its own template.
    md_env = Environment(
        loader=FileSystemLoader(TEMPLATES),
        undefined=StrictUndefined,
        autoescape=False,
        keep_trailing_newline=True,
    )
    markdown = md_env.get_template("report.md.j2").render(
        metrics=tuple(
            (_markdown(label), replace(metric, text=_markdown(metric.text)))
            for label, metric in items
        )
    )
    return html, markdown
