import json

import pytest

from frappe_migration_utils.exceptions import MigrationError
from frappe_migration_utils.json_loader import load_records


def test_sorted_json_files(tmp_path):
    (tmp_path / "b.json").write_text(json.dumps([{"name": "B"}]))
    (tmp_path / "a.json").write_text(json.dumps([{"name": "A"}]))
    assert [r["name"] for r in load_records(str(tmp_path))] == ["A", "B"]


def test_bad_json_shape_fails(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text('{"name":"invalid"}')
    with pytest.raises(MigrationError, match="JSON array"):
        load_records(str(path))


def test_empty_folder_is_error(tmp_path):
    with pytest.raises(MigrationError, match="No JSON"):
        load_records(str(tmp_path))
