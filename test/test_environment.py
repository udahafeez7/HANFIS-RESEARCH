import sys

import numpy as np


def test_python_version():
    assert sys.version_info >= (3, 12)


def test_numpy_available():
    assert np.__version__


def test_basic_numpy_calculation():
    values = np.array([1, 2, 3, 4, 5])
    assert values.mean() == 3.0