import numpy as np
from napari.util.misc import is_rgb, callsignature, is_pyramid


def test_is_rgb():
    shape = (10, 15)
    assert not is_rgb(shape)

    shape = (10, 15, 6)
    assert not is_rgb(shape)

    shape = (10, 15, 3)
    assert is_rgb(shape)

    shape = (10, 15, 4)
    assert is_rgb(shape)


def test_is_pyramid():
    data = np.random.random((10, 15))
    assert not is_pyramid(data)

    data = np.random.random((10, 15, 6))
    assert not is_pyramid(data)

    data = [np.random.random((10, 15, 6))]
    assert not is_pyramid(data)

    data = [np.random.random((10, 15, 6)), np.random.random((10, 15, 6))]
    assert not is_pyramid(data)

    data = [np.random.random((10, 15, 6)), np.random.random((5, 7, 3))]
    assert is_pyramid(data)

    data = [np.random.random((10, 15, 6)), np.random.random((10, 7, 3))]
    assert is_pyramid(data)


def test_callsignature():
    # no arguments
    assert str(callsignature(lambda: None)) == '()'

    # one arg
    assert str(callsignature(lambda a: None)) == '(a)'

    # multiple args
    assert str(callsignature(lambda a, b: None)) == '(a, b)'

    # arbitrary args
    assert str(callsignature(lambda *args: None)) == '(*args)'

    # arg + arbitrary args
    assert str(callsignature(lambda a, *az: None)) == '(a, *az)'

    # default arg
    assert str(callsignature(lambda a=42: None)) == '(a=a)'

    # multiple default args
    assert str(callsignature(lambda a=0, b=1: None)) == '(a=a, b=b)'

    # arg + default arg
    assert str(callsignature(lambda a, b=42: None)) == '(a, b=b)'

    # arbitrary kwargs
    assert str(callsignature(lambda **kwargs: None)) == '(**kwargs)'

    # default arg + arbitrary kwargs
    assert str(callsignature(lambda a=42, **kwargs: None)) == '(a=a, **kwargs)'

    # arg + default arg + arbitrary kwargs
    assert str(callsignature(lambda a, b=42, **kw: None)) == '(a, b=b, **kw)'

    # arbitary args + arbitrary kwargs
    assert str(callsignature(lambda *args, **kw: None)) == '(*args, **kw)'

    # arg + default arg + arbitrary kwargs
    assert (
        str(callsignature(lambda a, b=42, *args, **kwargs: None))
        == '(a, b=b, *args, **kwargs)'
    )

    # kwonly arg
    assert str(callsignature(lambda *, a: None)) == '(a=a)'

    # arg + kwonly arg
    assert str(callsignature(lambda a, *, b: None)) == '(a, b=b)'

    # default arg + kwonly arg
    assert str(callsignature(lambda a=42, *, b: None)) == '(a=a, b=b)'

    # kwonly args + everything
    assert (
        str(callsignature(lambda a, b=42, *, c, d=5, **kwargs: None))
        == '(a, b=b, c=c, d=d, **kwargs)'
    )
