# AI agent instructions — frappe-migration-utils

Read this file before modifying this repository or using the package in a consuming Frappe app. Detailed instructions: [docs/AGENT_USAGE.md](docs/AGENT_USAGE.md). New-app layout: [docs/APP_SCAFFOLDING.md](docs/APP_SCAFFOLDING.md).

## Intent
This library centralizes JSON import helpers. **Frappe's native `patches.txt` and Patch Log govern once-only execution.** This library is not a Frappe application, fixture sync process, migration runner, or manifest system.

## Non-negotiable rules
1. Preserve existing site data and user modifications, especially Select options and renamed master records. Never reapply completed JSON batches as continuous reconciliation.
2. Keep a separate DocType folder and new JSON file for each new patch batch; never rewrite previously released migration inputs.
3. Do not add manifests, private migration journals, new Frappe DocTypes, or recurring `after_migrate` synchronization.
4. Consume native supported Frappe APIs and ORM, not `frappe.db.sql` or raw SQL.
5. Raise on missing required DocTypes, incompatible metadata, or unresolved `insert_after` references. Explicitly allow optional integrations only when intentional.
6. Do not automatically delete records, reset existing Custom Fields/Property Setters, or update existing master data.
7. Do not change historical Frappe Patch Log or historical patches.
8. Verify compatibility with actual MariaDB-backed Frappe v15 and v16 before production release; Python-only tests are not enough.
9. Do not infer that missing physical columns are repaired by the current package: the initial library does **not** implement schema repair or full physical schema verification.
10. Do not publish releases, merge PRs, or modify consuming repositories without explicit request.

## Published API in PR1
```python
from frappe_migration_utils import (
    import_custom_fields,
    import_property_setters,
    import_doctype_records,
)
```
All importers accept a source directory or file path; `file=` selects one JSON batch. Generic document importer requires `doctype=`. See documentation for exact signatures and exclusions.

## AI-assisted changes
Inspect actual `pyproject.toml`, `patches.txt`, `hooks.py`, and existing JSON structures before scaffolding. Keep edits limited to the requested app and avoid duplicating this library's internal code. Explicitly report unit-test versus integration-test coverage.
