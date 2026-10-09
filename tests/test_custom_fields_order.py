import pytest

from frappe_migration_utils.custom_fields import _ordered
from frappe_migration_utils.exceptions import MigrationError


def test_dependency_ordering():
    fields = [
        {"fieldname": "second", "insert_after": "first"},
        {"fieldname": "first", "insert_after": "subject"},
    ]
    assert [x["fieldname"] for x in _ordered(fields, "Task", {"subject"})] == ["first", "second"]


def test_circular_dependency():
    fields = [
        {"fieldname": "a", "insert_after": "b"},
        {"fieldname": "b", "insert_after": "a"},
    ]
    with pytest.raises(MigrationError, match="circular"):
        _ordered(fields, "Task", set())


def test_missing_dependency():
    with pytest.raises(MigrationError, match="unresolved"):
        _ordered([{"fieldname": "a", "insert_after": "nonexistent"}], "Task", set())
