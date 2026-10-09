"""Resolve dotted package directories or JSON files without depending on CWD."""

import importlib.util
import json
from pathlib import Path

from .exceptions import MigrationError


def resolve_source(source: str, file: str | None = None) -> Path:
    path = Path(source)
    if not path.exists():
        spec = importlib.util.find_spec(source)
        if spec and spec.submodule_search_locations:
            path = Path(next(iter(spec.submodule_search_locations)))
        elif spec and spec.origin:
            path = Path(spec.origin)
        else:
            raise MigrationError(f"Migration source not found: {source}")
    if file:
        path = path / file
    if not path.exists():
        raise MigrationError(f"Migration source not found: {path}")
    return path


def load_records(source: str, file: str | None = None) -> list[dict]:
    path = resolve_source(source, file)
    paths = sorted(path.glob("*.json")) if path.is_dir() else [path]
    if not paths:
        raise MigrationError(f"No JSON definitions found in {path}")
    records = []
    for json_file in paths:
        if json_file.suffix != ".json":
            raise MigrationError(f"Migration file must be JSON: {json_file}")
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise MigrationError(f"Cannot parse {json_file}: {exc}") from exc
        if not isinstance(data, list) or any(not isinstance(item, dict) for item in data):
            raise MigrationError(f"{json_file}: expected a JSON array of document objects")
        records.extend(data)
    return records
