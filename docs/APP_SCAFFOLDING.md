# Scaffold a new Frappe application to use frappe-migration-utils

## Expected layout
```text
my_app/
  pyproject.toml
  my_app/
    __init__.py
    patches.txt
    patches/
      custom_field/
        add_reference_20261009.py
        custom_field_json/
          add_reference_20261009.json
      property_setter/
        update_label_20261009.py
        property_setter_json/
          update_label_20261009.json
      item_group/
        add_groups_20261009.py
        item_group_json/
          add_groups_20261009.json
```

The new scaffold does **not** create a manifest or custom journal. Keep a fresh one-time patch function per new JSON batch and register the dotted module under `[post_model_sync]` in your app's existing `patches.txt`.

## Install dependency
After publishing an appropriate stable release, add a bounded requirement to the existing `[project].dependencies` array; do not replace its contents:
```toml
"frappe-migration-utils>=0.1,<0.2"
```
Only declare a version which exists on your chosen package index. A git tag pin may be used for testing before PyPI publishing; do not assume PR1 is already published. Do not add this library to Frappe `apps.txt` because it is not a Frappe app.

## Example
```python
from frappe_migration_utils import import_doctype_records

def execute():
    import_doctype_records(
        "my_app.patches.item_group.item_group_json",
        doctype="Item Group",
        file="add_groups_20261009.json",
    )
```
The JSON file holds a **list** of documents with explicit stable `name` attributes.

## Migration safety
- Do not overwrite existing master data or Custom Field properties. Users may rename and edit records.
- Never modify a historical patch or completed batch; create a new file and patch for new changes.
- Do not remove legacy hooks as part of new-app scaffolding. Existing apps need separate migration baseline review.
- For optional integrations use an explicitly declared optional DocType and plan its later installation separately.
- For unsupported schema repair/Single/child/renaming cases, write carefully scoped app-specific patches.

## AI agent distribution
The repository root `AGENTS.md` provides canonical instructions for coding agents. The companion skill is kept under `skills/frappe-migration-scaffolding/SKILL.md` with a deterministic scaffold script and can be packaged independently for compatible agent hosts. Its output must be reviewed before committing and does not silently touch `pyproject.toml` or `patches.txt`.
