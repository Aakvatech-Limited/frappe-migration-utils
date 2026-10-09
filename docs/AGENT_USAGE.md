# Agent usage and safe migration conventions

## 1. Purpose and lifecycle
`frappe-migration-utils` is an installable Python library, **not** a Frappe app. Each consuming application owns its JSON files and its one-time Python patch modules. Frappe native `patches.txt` and Patch Log control execution. Never call importers on every `after_migrate`; that would recreate the problem with fixtures.

## 2. API (PR1 initial implementation)
```python
import_custom_fields(source: str, *, file: str | None = None, optional_doctypes=None)
import_property_setters(source: str, *, file: str | None = None, optional_doctypes=None)
import_doctype_records(source: str, doctype: str, *, file: str | None = None, optional_doctypes=None)
```
`source` may be a filesystem path or importable Python package directory. `file` limits the migration to one JSON file; **always prefer an explicit file for new patches**. Source JSON must be an array of record objects. Functions return `ImportResult(created, updated, existing, skipped)`. `updated` is reserved; current default is insert-missing only.

Example:
```python
from frappe_migration_utils import import_custom_fields

def execute():
    import_custom_fields(
        "my_app.patches.custom_field.custom_field_json",
        file="add_external_ref_20261009.json",
    )
```
```json
[
  {
    "dt": "Sales Invoice",
    "fieldname": "custom_external_reference",
    "label": "External Reference",
    "fieldtype": "Data",
    "insert_after": "customer"
  }
]
```
Register a unique dotted patch module under `[post_model_sync]` in `patches.txt` and leave existing history intact.

## 3. Other DocTypes
For Property Setters, preserve the existing AV Tools keys: `doc_type`, `doctype_or_field` (`DocType` or `DocField`), `field_name`, `property`, `value`, `property_type`. They are created only if absent; existing setters are not overwritten.

For generic master data:
```python
import_doctype_records(
    "my_app.patches.item_group.item_group_json",
    doctype="Item Group",
    file="add_groups_20261009.json",
)
```
Every record must have an explicit, stable `name` and must be a normal (non-Single, non-child) DocType. Customer renames and generated names are **not** traceable by this generic importer; write a specialized app patch when stable document identity is unavailable.

## 4. Validation and failures
- Missing mandatory DocType: fail the patch, do not silently skip.
- Explicit optional integration: pass `optional_doctypes=["Integration DocType"]`; note that if the patch completes, a future patch/install event is required to create the skipped record.
- Existing standard field with the requested fieldname: fail, not recreate.
- Existing Custom Field with different fieldtype: fail.
- `insert_after` must resolve to an existing field or another field in the same input. Cycles and missing targets fail.
- Existing matching Custom Fields, Property Setters, or named masters are preserved without updates.
- **Not supported in PR1:** automatic missing physical DB column repair; full schema integrity verification; generated-name generic imports; Single and child DocTypes; transactional rename tracking; arbitrary dependent master data ordering.
- Duplicate Document writes are not safe when names change; plan app-specific reconciliation rather than assuming original names are still current.

## 5. Review checklist
1. Read current package source and pinned version before giving AI agents code tasks.
2. Verify per-DocType JSON array shape against the current API.
3. Check ownership and site data implications; always preserve customer-modified Select options.
4. Keep new batches immutable and give every patch module a unique identifier.
5. Test clean site and existing customer site on both Frappe v15 and v16, with MariaDB and actual schema.
6. Run package unit tests, Ruff and wheel build.
7. Do not claim that Python-only unit tests establish production compatibility.
