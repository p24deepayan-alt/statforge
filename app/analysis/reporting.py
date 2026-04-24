"""Report generation — HTML and PDF export.

Uses a single Jinja2 template rendered to HTML, then optionally piped through
WeasyPrint for PDF.  Each artifact is rendered in an isolated try/except so a
single failure cannot kill the entire export.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "resources" / "templates"


def _b64_image(path: Path) -> str:
    """Embed an image as a data-URI string."""
    if not path.exists():
        return ""
    data = path.read_bytes()
    encoded = base64.b64encode(data).decode("ascii")
    suffix = path.suffix.lstrip(".").lower()
    mime = {"png": "image/png", "svg": "image/svg+xml", "jpg": "image/jpeg"}.get(
        suffix, "application/octet-stream"
    )
    return f"data:{mime};base64,{encoded}"


def render_report_html(
    artifacts: list[dict[str, Any]],
    layout: list[dict[str, Any]],
    session_name: str,
    blobs_root: Path,
) -> str:
    """Render the report to a self-contained HTML string.

    ``layout`` is a list of dicts, each with a ``type`` key:
      - ``{"type": "artifact", "artifact_id": "..."}``
      - ``{"type": "narrative", "html": "..."}``
      - ``{"type": "divider"}``
      - ``{"type": "section_heading", "text": "..."}``

    ``artifacts`` is the full list of artifact dicts from the store (keyed by id
    for quick lookup inside the template).
    """
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=True,
    )
    env.globals["b64_image"] = _b64_image
    env.globals["json_loads"] = json.loads

    template = env.get_template("report.html")

    # Build a lookup map for artifacts by id.
    artifact_map = {a["id"]: a for a in artifacts}

    html = template.render(
        session_name=session_name,
        layout=layout,
        artifacts=artifact_map,
        blobs_root=blobs_root,
    )
    return html


def export_html(
    artifacts: list[dict[str, Any]],
    layout: list[dict[str, Any]],
    session_name: str,
    blobs_root: Path,
    output_path: Path,
) -> Path:
    """Export the report as a standalone HTML file."""
    html = render_report_html(artifacts, layout, session_name, blobs_root)
    output_path.write_text(html, encoding="utf-8")
    return output_path


def export_pdf(
    artifacts: list[dict[str, Any]],
    layout: list[dict[str, Any]],
    session_name: str,
    blobs_root: Path,
    output_path: Path,
) -> Path:
    """Export the report as a PDF via WeasyPrint."""
    html = render_report_html(artifacts, layout, session_name, blobs_root)
    try:
        from weasyprint import HTML  # type: ignore[import-untyped]

        HTML(string=html).write_pdf(str(output_path))
    except ImportError:
        raise RuntimeError(
            "WeasyPrint is not installed. Install it to enable PDF export."
        )
    return output_path
