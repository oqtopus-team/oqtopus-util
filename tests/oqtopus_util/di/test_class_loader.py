from collections import OrderedDict

import pytest

from oqtopus_util.di import load_class


def test_load_existing_class():
    """Load a class from a fully-qualified path."""
    cls = load_class("collections.OrderedDict")
    assert cls is OrderedDict


def test_load_class_from_test_module():
    """Load a class defined in the test file itself."""
    cls = load_class(f"{__name__}._LocalClass")
    assert cls is _LocalClass


def test_load_nonexistent_module():
    """Raise ImportError when the module does not exist."""
    with pytest.raises((ImportError, ModuleNotFoundError)):
        load_class("no.such.module.ClassName")


def test_load_nonexistent_class_in_existing_module():
    """Raise AttributeError when the class is missing from the module."""
    with pytest.raises(AttributeError):
        load_class("collections.NoSuchClass")


def test_load_class_no_dot_in_path():
    """Raise ValueError when the path has no dot (rsplit fails to split)."""
    with pytest.raises(ValueError, match="not enough values to unpack"):
        load_class("nodotpath")


# ---------------------------------------------------------------------------
# Local test double
# ---------------------------------------------------------------------------
class _LocalClass:
    pass
