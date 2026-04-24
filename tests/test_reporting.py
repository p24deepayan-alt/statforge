from pathlib import Path
from app.analysis.reporting import render_report_html

def test_render_report_html():
    artifacts = [
        {
            "id": "a1",
            "kind": "column_summary",
            "name": "Age Stats",
            "spec_json": '{"is_numeric": true, "mean": 42.0, "std": 12.5, "min": 18, "max": 90, "missing": 0}'
        }
    ]
    
    layout = [
        {"type": "section_heading", "text": "Demographics"},
        {"type": "artifact", "artifact_id": "a1"},
        {"type": "narrative", "html": "<p>This is a test.</p>"},
        {"type": "divider", "style": "dashed"}
    ]
    
    html = render_report_html(artifacts, layout, "Test Session", Path("/fake"))
    
    assert "Test Session" in html
    assert "Demographics" in html
    assert "Age Stats" in html
    assert "42.0" in html
    assert "<p>This is a test.</p>" in html
    assert "section-divider-dashed" in html
