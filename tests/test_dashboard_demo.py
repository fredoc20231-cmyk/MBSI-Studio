"""Tests for dashboard demo data generator."""

def test_generate_dashboard_demo():
    from app.components.demo_data import generate_dashboard_demo
    demo = generate_dashboard_demo(seed=42)
    assert "histology_image" in demo
    assert len(demo["cells"]) > 5000
    assert len(demo["pathways"]) == 10
    assert demo["summary"]["cells"] == 27842
    assert demo["boundaries"]
    assert "x" in demo["boundaries"][0] or "x0" in demo["boundaries"][0]


def test_make_histology_overlay():
    from app.components.demo_data import generate_dashboard_demo
    from app.components.histology import make_histology_overlay
    demo = generate_dashboard_demo(seed=42)
    fig = make_histology_overlay(
        demo["histology_image"],
        demo["cells"],
        boundaries=demo["boundaries"],
    )
    assert fig is not None
