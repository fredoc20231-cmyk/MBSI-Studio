"""Contract and numerical checks for experimental morphology STIE."""
import numpy as np
import pytest

from mbsi.reconstruction.morphology_stie import _fista, _objective, fit_morphology_stie


def fixture():
    E = np.array([[8., 2.], [2., 8.], [7., 3.]])
    G = np.array([[1., 0.], [0., 1.]])
    M = np.array([[0., 1.], [0.1, 1.1], [3., 4.], [3.2, 4.2]])
    cells = np.array([[0., 0.], [0.1, 0.], [10., 0.], [10.1, 0.]])
    spots = np.array([[0., 0.], [10., 0.], [20., 0.]])
    return E, G, M, cells, spots


def test_fista_decreases_correct_objective():
    E, G, *_ = fixture()
    P = np.array([[.8, .2], [.2, .8], [.7, .3]])
    A = np.ones((3, 2))
    fitted = _fista(E, G, P, A, 2.0, 500, 1e-9)
    assert np.all(fitted >= 0)
    assert _objective(E, G, fitted, P, 2.0) < _objective(E, G, A, P, 2.0)


def test_probabilities_are_finite_and_reproducible():
    data = fixture()
    first = fit_morphology_stie(*data, em_iters=5, fista_iters=50, random_state=12)
    second = fit_morphology_stie(*data, em_iters=5, fista_iters=50, random_state=12)
    assert first.spot_abundance.shape == (3, 2)
    assert first.cell_probabilities.shape == (4, 2)
    np.testing.assert_allclose(first.cell_probabilities.sum(axis=1), 1, atol=1e-8)
    np.testing.assert_allclose(first.spot_abundance, second.spot_abundance)
    assert np.isfinite(first.spot_abundance).all()
    assert np.isfinite(first.cell_confidence).all()


def test_missing_spot_nuclei_and_registered_distance_gate():
    data = fixture()
    result = fit_morphology_stie(*data, em_iters=2)
    assert len(result.spot_abundance) == 3
    with pytest.raises(ValueError, match="outside"):
        fit_morphology_stie(*data, max_assignment_distance=.01)


def test_rejects_misaligned_and_invalid_inputs():
    E, G, M, cells, spots = fixture()
    with pytest.raises(ValueError, match="dimensions"):
        fit_morphology_stie(E, G[:-1], M, cells, spots)
    with pytest.raises(ValueError, match="nonnegative"):
        fit_morphology_stie(-E, G, M, cells, spots)
