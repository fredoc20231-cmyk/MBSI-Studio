"""Scientific method identity and library provenance regression tests."""
import pytest
from mbsi.analysis.clustering import run_clustering_method
from mbsi.analysis.visium import read_visium_spaceranger


@pytest.mark.unit
@pytest.mark.parametrize("method", ["BayesSpace", "GraphST", "STAGATE", "Louvain"])
def test_unavailable_methods_never_silently_substitute(method):
    import anndata as ad
    import numpy as np
    a = ad.AnnData(X=np.ones((12, 3)))
    with pytest.raises(ValueError, match="BackendUnavailable"):
        run_clustering_method(a, method=method)


@pytest.mark.unit
def test_spatial_graph_uses_squidpy_grid_name():
    import inspect
    from mbsi.visium_core.spatial import build_spatial_graph
    assert '"grid"' in inspect.getsource(build_spatial_graph)


@pytest.mark.unit
def test_visium_ingest_uses_folder_identity():
    import inspect
    source = inspect.getsource(read_visium_spaceranger)
    assert 'library_id = "sample"' not in source
    assert 'adata.obs["library_id"]' in source
