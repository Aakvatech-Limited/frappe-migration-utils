# frappe-migration-utils

Lightweight Python helpers for **one-time, JSON-driven Frappe patches**.

This is a Python package, **not a Frappe app**. It does not install DocTypes,
manage Patch Log, sync fixtures, or rerun completed patches. Consuming apps
control execution with Frappe's native `patches.txt`.

## Installation

```bash
pip install frappe-migration-utils
```

In a consuming application's `pyproject.toml`, after the first release:

```toml
dependencies = ["frappe-migration-utils>=0.1,<0.2"]
```

## Usage

```python
from frappe_migration_utils import (
    import_custom_fields,
    import_property_setters,
    import_doctype_records,
)

def execute():
    import_custom_fields(
        "av_tools.patches.custom_fields.custom_fields_json",
        file="new_fields.json",
    )
    import_property_setters(
        "av_tools.patches.property_setter.property_setter_json",
        file="new_setters.json",
    )
    import_doctype_records(
        "av_tools.patches.item_group.item_group_json",
        doctype="Item Group",
        file="new_groups.json",
    )
```

Sources are package directories or filesystem paths containing JSON arrays.
For Custom Field records use Frappe's `dt` and `fieldname` keys; for
Property Setter records use the existing `doc_type`, `field_name`,
`property`, `value`, `property_type`, `doctype_or_field` keys.

Normal DocType records must have an explicit, stable `name`; importer
creates missing records and **never overwrites existing records**. A renamed
record cannot be inferred from its former name: use an application-specific
migration for records with generated names, renames, Singles, or child tables.

## Compatibility and limitations

- Only invoke the helpers from Frappe-managed runtime with a selected site.
- Missing required DocTypes and invalid field dependencies raise errors.
- Pass `optional_doctypes=[...]` to explicitly skip absent integrations.
  Deferred integrations need their own future patch/install event.
- Existing Custom Fields and Property Setters are not updated; user-specific
  labels, Select options and values remain preserved.
- These APIs do not delete records, bypass migration history, or issue raw SQL.
- These helpers do **not** silently repair missing physical columns. Site
  schema health checks and safe native schema repair are follow-up work.
- Initial CI is Python-only; MariaDB-backed Frappe v15/v16 integration tests
  are required before recommending production adoption or publishing a release.

## Guidance for AI coding agents

Read [AGENTS.md](AGENTS.md) before modifying this package or integrating it with a Frappe app. Detailed API usage and caveats are in [docs/AGENT_USAGE.md](docs/AGENT_USAGE.md); new-app layout is in [docs/APP_SCAFFOLDING.md](docs/APP_SCAFFOLDING.md).

A reusable, standalone agent skill and safe patch scaffold generator are included under [skills/frappe-migration-scaffolding](skills/frappe-migration-scaffolding). The generator creates candidate JSON and patch files but deliberately does not edit `patches.txt` or `pyproject.toml` automatically.
