import numpy as np

from napari.layers.utils.transform_utils import (
    compose_linear_matrix,
    decompose_linear_matrix,
)


def test_decompose_linear_matrix():
    """Test composing and decomposing a linear matrix."""
    np.random.seed(0)

    # Decompose linear matrix
    A = np.random.random((2, 2))
    rotate, scale, shear = decompose_linear_matrix(A)

    # Compose linear matrix and check it matches
    B = compose_linear_matrix(rotate, scale, shear)
    np.testing.assert_almost_equal(A, B)

    # Deompose linear matrix and check it matches
    rotate_B, scale_B, shear_B = decompose_linear_matrix(B)
    np.testing.assert_almost_equal(rotate, rotate_B)
    np.testing.assert_almost_equal(scale, scale_B)
    np.testing.assert_almost_equal(shear, shear_B)

    # Compose linear matrix and check it matches
    C = compose_linear_matrix(rotate_B, scale_B, shear_B)
    np.testing.assert_almost_equal(B, C)