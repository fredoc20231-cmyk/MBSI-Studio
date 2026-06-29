"""Tests for Stereo-seq IO stub detection."""

from mbsi.io.detect import detect_platform
from mbsi.io.stereo_seq import detect_stereo_seq_assets, load_stereo_qc_html


def test_detect_stereo_seq_gef():
    d = detect_platform(["sample.gef", "SAW_output/report.html", "registered_he.tif"])
    assert d["platform"] == "stereo_seq"
    assert d["technology_key"] == "stereo_seq"
    assert d["partial_support"] is True
    assert "gef_matrix" in d["required_found"]


def test_detect_stereo_seq_assets():
    names = [
        "sample.cgef",
        "StereoMap/cluster_umap.csv",
        "lasso_region_1.csv",
        "qc_report.html",
    ]
    info = detect_stereo_seq_assets(names)
    assert info["platform"] == "stereo_seq"
    assert info["assets"]["cgef"] is True
    assert info["assets"]["clustering_outputs"] is True
    assert info["assets"]["lasso_regions"] is True
    assert info["assets"]["html_qc_report"] is True
    assert info["partial_support"] is True


def test_stereo_qc_html_stub(tmp_path):
    report = tmp_path / "stereo_qc_report.html"
    report.write_text("<html><body>QC</body></html>")
    result = load_stereo_qc_html(tmp_path)
    assert result["found"] is True
    assert result["partial_support"] is True
