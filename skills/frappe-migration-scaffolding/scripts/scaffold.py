#!/usr/bin/env python3
"""Generate candidate per-DocType JSON patch files without altering existing app metadata."""

import argparse
import json
import re
from pathlib import Path


def slug(value):
    result = re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
    if not result:
        raise ValueError("Empty identifier")
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--app-path", required=True, help="Python app package path, e.g. ./sample_app/sample_app")
    p.add_argument("--app-name", required=True, help="Python package name, e.g. sample_app")
    p.add_argument("--doctype", required=True, help="Frappe DocType, e.g. Custom Field or Item Group")
    p.add_argument("--batch", required=True, help="Unique snake_case batch name, e.g. add_reference_20261009")
    args = p.parse_args()
    app_path = Path(args.app_path)
    if not app_path.is_dir() or not (app_path / "__init__.py").is_file():
        p.error("--app-path must be an existing Python package directory (with __init__.py)")
    if not re.fullmatch(r"[a-z][a-z0-9_]*", args.app_name):
        p.error("--app-name must be a Python package name")
    if not re.fullmatch(r"[a-z][a-z0-9_]*", args.batch):
        p.error("--batch must be a valid snake_case module name")
    folder = slug(args.doctype)
    patch_root = app_path / "patches" / folder
    json_folder = patch_root / (folder + "_json")
    module_path = patch_root / (args.batch + ".py")
    json_path = json_folder / (args.batch + ".json")
    for path in (module_path, json_path):
        if path.exists():
            p.error(f"Refusing to overwrite existing file: {path}")
    patch_root.mkdir(parents=True, exist_ok=True)
    json_folder.mkdir(parents=True, exist_ok=True)
    if folder == "custom_field":
        symbol = "import_custom_fields"
        call = f'{symbol}("{args.app_name}.patches.{folder}.{folder}_json", file="{args.batch}.json")'
    elif folder == "property_setter":
        symbol = "import_property_setters"
        call = f'{symbol}("{args.app_name}.patches.{folder}.{folder}_json", file="{args.batch}.json")'
    else:
        symbol = "import_doctype_records"
        call = (f'{symbol}("{args.app_name}.patches.{folder}.{folder}_json", '
                f'doctype={args.doctype!r}, file="{args.batch}.json")')
    module_path.write_text(
        f"from frappe_migration_utils import {symbol}\n\ndef execute():\n    {call}\n",
        encoding="utf-8",
    )
    json_path.write_text(json.dumps([], indent=2) + "\n", encoding="utf-8")
    print(f"Created {module_path}")
    print(f"Created {json_path} (populate record definitions before executing)")
    print(f"Append under [post_model_sync] in patches.txt: {args.app_name}.patches.{folder}.{args.batch}")
    print("Review dependencies, add bounded package requirement and test on Frappe sites.")


if __name__ == "__main__":
    main()
