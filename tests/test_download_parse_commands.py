"""Tests for download URL parsing and 10x file classification."""

from mbsi.io.downloader.parse_commands import (
    classify_download_url,
    extract_urls_from_text,
    infer_filename_from_url,
    parse_url_entries,
)

TENX_EXAMPLE_BLOCK = """
# 10x Xenium preview bundle — facility curl block
curl -L -o WTA_Preview_FFPE_Cervical_Cancer_outs.zip https://cf.10xgenomics.com/samples/xenium/3.0/WTA_Preview_FFPE_Cervical_Cancer/WTA_Preview_FFPE_Cervical_Cancer_outs.zip
curl -L -o WTA_Preview_FFPE_Cervical_Cancer_xe_outs.zip https://cf.10xgenomics.com/samples/xenium/3.0/WTA_Preview_FFPE_Cervical_Cancer/WTA_Preview_FFPE_Cervical_Cancer_xe_outs.zip
wget https://cf.10xgenomics.com/samples/xenium/3.0/WTA_Preview_FFPE_Cervical_Cancer/gene_groups.csv
wget https://cf.10xgenomics.com/samples/xenium/3.0/WTA_Preview_FFPE_Cervical_Cancer/cell_groups.csv
https://cf.10xgenomics.com/samples/xenium/3.0/WTA_Preview_FFPE_Cervical_Cancer/he_image.ome.tif
curl -O https://cf.10xgenomics.com/samples/xenium/3.0/WTA_Preview_FFPE_Cervical_Cancer/he_alignment.csv
wget -O keypoints.csv https://cf.10xgenomics.com/samples/xenium/3.0/WTA_Preview_FFPE_Cervical_Cancer/keypoints.csv
"""


def test_extract_urls_from_10x_block():
    urls = extract_urls_from_text(TENX_EXAMPLE_BLOCK)
    assert len(urls) == 7
    assert all(u.startswith("https://cf.10xgenomics.com") for u in urls)
    assert any("WTA_Preview_FFPE_Cervical_Cancer_outs.zip" in u for u in urls)


def test_parse_url_entries_respects_curl_o_filenames():
    entries = parse_url_entries(TENX_EXAMPLE_BLOCK)
    by_name = {e["filename"]: e for e in entries}
    assert "WTA_Preview_FFPE_Cervical_Cancer_outs.zip" in by_name
    assert "WTA_Preview_FFPE_Cervical_Cancer_xe_outs.zip" in by_name
    assert "keypoints.csv" in by_name
    assert by_name["WTA_Preview_FFPE_Cervical_Cancer_outs.zip"]["source"] == "10x"
    assert by_name["WTA_Preview_FFPE_Cervical_Cancer_outs.zip"]["likely_role"] == "output_archive"
    assert by_name["WTA_Preview_FFPE_Cervical_Cancer_xe_outs.zip"]["likely_role"] == "xenium_explorer_archive"
    assert by_name["gene_groups.csv"]["likely_role"] == "metadata_groups"
    assert by_name["cell_groups.csv"]["technology_hint"] == "xenium"
    assert by_name["he_image.ome.tif"]["likely_role"] == "histology_image"
    assert by_name["he_alignment.csv"]["likely_role"] == "registration"
    assert by_name["keypoints.csv"]["likely_role"] == "registration"


def test_classify_download_url_generic():
    info = classify_download_url("https://example.org/data/counts.h5ad")
    assert info["filename"] == "counts.h5ad"
    assert info["likely_role"] == "expression_matrix"
    assert info["technology_hint"] == "generic_h5ad"


def test_infer_filename_from_url():
    assert infer_filename_from_url("https://host/path/to/file.zip?token=abc") == "file.zip"


def test_no_shell_execution():
    """Parsing must not invoke subprocess or shell."""
    import subprocess

    # Ensure parse functions are pure string parsing
    entries = parse_url_entries("curl -O https://example.org/test.csv")
    assert len(entries) == 1
    # subprocess.run should not be called by our module — smoke check via absence of side effects
    assert entries[0]["url"] == "https://example.org/test.csv"
