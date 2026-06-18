from dataclasses import dataclass

import pytest

from oqtopus_util.di import CircularDependencyError, DiContainer


# ----------------------------------------------------------------------
# Test helper classes (local test doubles)
# ----------------------------------------------------------------------
@dataclass
class DummyA:
    """A simple class for singleton/prototype tests."""

    x: int
    label: str


@dataclass
class DummyB:
    """Another class for constructor mismatch testing."""

    value: int


# Fully-qualified path strings for the test classes above.
# These must match the actual module path where this test file lives.
# If your tests are located under tests/, adjust accordingly.
DUMMYA_PATH = f"{__name__}.DummyA"
DUMMYB_PATH = f"{__name__}.DummyB"


# ----------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------
def test_singleton_scope_default():
    """
    Default scope should be singleton when _scope_ is omitted.
    get() must return the same instance.
    """
    config = {
        "obj": {
            "_target_": DUMMYA_PATH,
            "x": 123,
            "label": "abc",
        }
    }
    dicon = DiContainer(config)

    a1 = dicon.get("obj")
    a2 = dicon.get("obj")

    assert a1 is a2
    assert a1.x == 123
    assert a1.label == "abc"


def test_explicit_singleton_scope():
    """
    _scope_: singleton should behave identically to omitted scope.
    """
    config = {
        "obj": {
            "_target_": DUMMYA_PATH,
            "_scope_": "singleton",
            "x": 5,
            "label": "hello",
        }
    }
    dicon = DiContainer(config)

    a1 = dicon.get("obj")
    a2 = dicon.get("obj")

    assert a1 is a2
    assert a1.label == "hello"


def test_prototype_scope():
    """
    _scope_: prototype should produce a new instance every time.
    """
    config = {
        "obj": {
            "_target_": DUMMYA_PATH,
            "_scope_": "prototype",
            "x": 1,
            "label": "x",
        }
    }
    dicon = DiContainer(config)

    a1 = dicon.get("obj")
    a2 = dicon.get("obj")

    assert a1 is not a2
    assert a1.x == 1
    assert a2.x == 1


def test_unknown_dependency_key():
    """
    get() must raise KeyError for missing component names.
    """
    dicon = DiContainer({})
    with pytest.raises(KeyError):
        dicon.get("notdefined")


def test_missing_target_error():
    """
    Missing _target_ should raise ValueError.
    """
    config = {
        "obj": {
            "x": 1,
            "label": "no_target",
        }
    }
    dicon = DiContainer(config)

    with pytest.raises(ValueError, match="Missing _target_ for dependency obj"):
        dicon.get("obj")


def test_invalid_target_path():
    """
    An invalid _target_ string should raise ImportError.
    """
    config = {
        "obj": {
            "_target_": "no.such.module.ClassName",
            "x": 10,
            "label": "z",
        }
    }
    dicon = DiContainer(config)

    with pytest.raises(ImportError):
        dicon.get("obj")


def test_constructor_argument_mismatch():
    """
    If constructor arguments do not match, TypeError should be raised.
    """
    config = {
        "obj": {
            "_target_": DUMMYB_PATH,  # DummyB expects only 'value'
            "wrong": 999,  # wrong kwarg
        }
    }
    dicon = DiContainer(config)

    with pytest.raises(TypeError):
        dicon.get("obj")


def test_underbar_keys_are_excluded_from_kwargs():
    """
    Keys starting with '_' are excluded from constructor kwargs.
    Only non-underscore keys must be passed to the constructor.
    """
    config = {
        "obj": {
            "_target_": DUMMYA_PATH,
            "_scope_": "singleton",
            "_meta1": 999,
            "x": 42,
            "label": "ok",
        }
    }
    dicon = DiContainer(config)

    obj = dicon.get("obj")

    assert isinstance(obj, DummyA)
    assert obj.x == 42
    assert obj.label == "ok"


# ----------------------------------------------------------------------
# @-reference resolution
# ----------------------------------------------------------------------
@dataclass
class DummyC:
    """Holds a reference to another dependency."""

    dep: object
    name: str


DUMMYC_PATH = f"{__name__}.DummyC"


def test_at_reference_resolves_dependency():
    """String values starting with '@' must be resolved as dependencies."""
    config = {
        "inner": {
            "_target_": DUMMYB_PATH,
            "value": 7,
        },
        "outer": {
            "_target_": DUMMYC_PATH,
            "dep": "@inner",
            "name": "wrap",
        },
    }
    dicon = DiContainer(config)
    outer = dicon.get("outer")

    assert isinstance(outer.dep, DummyB)
    assert outer.dep.value == 7
    assert outer.name == "wrap"


def test_at_reference_singleton_is_shared():
    """Two components that reference the same singleton get the same instance."""
    config = {
        "shared": {
            "_target_": DUMMYB_PATH,
            "value": 99,
        },
        "first": {
            "_target_": DUMMYC_PATH,
            "dep": "@shared",
            "name": "first",
        },
        "second": {
            "_target_": DUMMYC_PATH,
            "dep": "@shared",
            "name": "second",
        },
    }
    dicon = DiContainer(config)
    first = dicon.get("first")
    second = dicon.get("second")

    assert first.dep is second.dep


def test_at_reference_with_whitespace_stripped():
    """'@ inner' (with trailing space after @) should resolve 'inner'."""
    config = {
        "inner": {
            "_target_": DUMMYB_PATH,
            "value": 3,
        },
        "outer": {
            "_target_": DUMMYC_PATH,
            "dep": "@ inner",
            "name": "ws",
        },
    }
    dicon = DiContainer(config)
    outer = dicon.get("outer")

    assert isinstance(outer.dep, DummyB)


def test_invalid_at_reference_raises_value_error():
    """'@' alone (no dependency name) must raise ValueError."""
    config = {
        "obj": {
            "_target_": DUMMYC_PATH,
            "dep": "@",
            "name": "bad",
        },
    }
    dicon = DiContainer(config)
    with pytest.raises(ValueError, match="Invalid dependency reference"):
        dicon.get("obj")


# ----------------------------------------------------------------------
# Circular dependency detection
# ----------------------------------------------------------------------
def test_circular_dependency_raises_error():
    """A → B → A cycle must raise CircularDependencyError."""
    config = {
        "a": {
            "_target_": DUMMYC_PATH,
            "dep": "@b",
            "name": "a",
        },
        "b": {
            "_target_": DUMMYC_PATH,
            "dep": "@a",
            "name": "b",
        },
    }
    dicon = DiContainer(config)
    with pytest.raises(CircularDependencyError, match="Circular dependency"):
        dicon.get("a")


def test_self_referential_dependency_raises_error():
    """A component that references itself must raise CircularDependencyError."""
    config = {
        "self_ref": {
            "_target_": DUMMYC_PATH,
            "dep": "@self_ref",
            "name": "loop",
        },
    }
    dicon = DiContainer(config)
    with pytest.raises(CircularDependencyError):
        dicon.get("self_ref")


# ----------------------------------------------------------------------
# _resolve_value: dict and list recursion
# ----------------------------------------------------------------------
@dataclass
class DummyDict:
    mapping: dict


@dataclass
class DummyList:
    items: list


DUMMYDICT_PATH = f"{__name__}.DummyDict"
DUMMYLIST_PATH = f"{__name__}.DummyList"


def test_resolve_value_dict_recursive():
    """Dict values containing @-refs must be resolved recursively."""
    config = {
        "inner": {
            "_target_": DUMMYB_PATH,
            "value": 55,
        },
        "outer": {
            "_target_": DUMMYDICT_PATH,
            "mapping": {"key": "@inner"},
        },
    }
    dicon = DiContainer(config)
    outer = dicon.get("outer")

    assert isinstance(outer.mapping["key"], DummyB)
    assert outer.mapping["key"].value == 55


def test_resolve_value_list_recursive():
    """List values containing @-refs must be resolved recursively."""
    config = {
        "inner": {
            "_target_": DUMMYB_PATH,
            "value": 11,
        },
        "outer": {
            "_target_": DUMMYLIST_PATH,
            "items": ["@inner", 42],
        },
    }
    dicon = DiContainer(config)
    outer = dicon.get("outer")

    assert isinstance(outer.items[0], DummyB)
    assert outer.items[1] == 42


# ----------------------------------------------------------------------
# _load_class error paths
# ----------------------------------------------------------------------
def test_load_class_no_dot_raises_import_error():
    """_target_ with no dot should raise ImportError."""
    config = {
        "obj": {
            "_target_": "NoDotPath",
        },
    }
    dicon = DiContainer(config)
    with pytest.raises(ImportError, match="Invalid _target_ format"):
        dicon.get("obj")


def test_load_class_missing_class_in_module_raises_import_error():
    """_target_ pointing to a missing class in a real module raises ImportError."""
    config = {
        "obj": {
            "_target_": "collections.NoSuchClass",
        },
    }
    dicon = DiContainer(config)
    with pytest.raises(ImportError, match="has no class"):
        dicon.get("obj")
