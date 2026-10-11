"""Static captured rooflines: only already-permitted quantities influence geometry."""

from __future__ import annotations

import html
from dataclasses import dataclass

from uarch_contract.report_context import RenderSpec

from .badged import Badged, badged
from .prose import CapturedIdentifier, safe_prose


@dataclass(frozen=True)
class Plot:
    svg: str
    markdown: str
    render_hash: str


def roofline(
    points: tuple[tuple[str | CapturedIdentifier, Badged, Badged, Badged, Badged], ...],
    permissions: RenderSpec,
) -> Plot:
    for _, *metrics in points:
        for metric in metrics:
            if not isinstance(metric, Badged) or metric.render_hash != permissions.render_hash:
                raise ValueError("RenderPermissionMismatch: roofline")
    visible = [p for p in points if p[1].number is not None and p[2].number is not None]
    if not visible:
        text = "Roofline: no permitted finite point; hidden or not modelled. No numeric axes."
        return Plot("<p>" + text + "</p>", text, permissions.render_hash)
    xs = [p[1] for p in visible] + [p[3] for p in visible if p[3].number is not None]
    ys = [p[2] for p in visible] + [p[4] for p in visible if p[4].number is not None]
    xmax = max(xs, key=lambda m: float(m.number or "0"))
    ymax = max(ys, key=lambda m: float(m.number or "0"))
    dx = float(xmax.number or "0")
    dy = float(ymax.number or "0")

    def coordinate(value: float, metric: Badged) -> str:
        rendered = badged(
            value, "plot coordinate", metric.assessment, permissions, execution="executed"
        )
        if rendered.number is None:
            raise ValueError("RenderPermissionMismatch: coordinate")
        return rendered.number

    def xy(x: Badged, y: Badged) -> tuple[str, str]:
        return (
            coordinate(40 + 500 * (float(x.number or "0") / dx if dx else 0), x),
            coordinate(300 - 260 * (float(y.number or "0") / dy if dy else 0), y),
        )

    caption = (
        "Captured matrix operational intensity (op/byte) against achieved matrix throughput (op/s)."
    )
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 360" role="img">',
        "<title>" + caption + "</title>",
        '<path d="M40 40V300H540" fill="none" stroke="black"/>',
    ]
    descriptions = []
    for label, x, y, ridge, peak in visible:
        cx, cy = xy(x, y)
        name = label.value if isinstance(label, CapturedIdentifier) else safe_prose(label)
        text = name + ": " + x.text + "; " + y.text
        out.append(
            '<circle cx="'
            + cx
            + '" cy="'
            + cy
            + '" r="3" fill="navy"><title>'
            + html.escape(text)
            + "</title></circle>"
        )
        if ridge.number is not None and peak.number is not None:
            rx, ry = xy(ridge, peak)
            right = coordinate(540, peak)
            out.append(
                '<polyline points="40,300 '
                + rx
                + ","
                + ry
                + " "
                + right
                + ","
                + ry
                + '" fill="none" stroke="gray"><title>'
                + html.escape(ridge.text + "; " + peak.text)
                + "</title></polyline>"
            )
        descriptions.append(text)
    out.extend(
        ["</svg>", "<p>" + html.escape("Axis maximum: " + xmax.text + "; " + ymax.text) + "</p>"]
    )
    # Markdown embeds the same static SVG and retains textual point descriptions.
    svg = "".join(out)
    return Plot(
        svg,
        svg + "\n\n" + "\n\n".join(html.escape(d) for d in descriptions),
        permissions.render_hash,
    )
