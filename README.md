# Frappe Migration Utils

**Safe, one-time JSON-driven migrations for Frappe applications.**

`frappe-migration-utils` is a lightweight, installable Python library that helps Frappe app maintainers introduce Custom Fields, Property Setters, and named DocType records through **versioned patches**. It is **not itself a Frappe app**, migration runner, fixture-sync engine, or custom patch journal.

> **Release status:** Version `0.1.0` is defined in the draft implementation in [PR #1](https://github.com/Aakvatech-Limited/frappe-migration-utils/pull/1), but the package is **not yet published to PyPI** and Frappe v15/v16 MariaDB integration testing remains outstanding. Do not treat these instructions as production certification.

## Why this exists

Apps often ship customizations that must be installed once but remain editable by site owners afterwards. Replaying exported JSON or fixtures on every migration can overwrite site-specific labels, Select options, or master-data changes.

| Common problem | Intended approach |
| --- | --- |
| Repeated synchronization resets user edits | Run an immutable batch once through Frappe's own patch mechanism |
| Individual apps duplicate JSON-import utilities | Reuse a small common Python package |
| New Custom Fields depend on other new fields | Resolve `insert_after` dependencies before creation |
| Missing integration DocTypes cause ambiguous failures | Require dependencies by default; permit explicit optional DocTypes |
| Historical migrations become difficult to audit | Keep distinct patch modules and JSON files; do not rewrite completed batches |

**Intended users:** Frappe/ERPNext application developers, implementers, migration maintainers, and repository-aware coding agents. **Not intended for:** end-user bulk data imports, recurring synchronization, data reconciliation, arbitrary schema repair, or automatic upgrades of edited customer records.

## Implemented functionality in PR #1

| Function | Purpose | Existing records |
| --- | --- | --- |
| `import_custom_fields(source, *, file=None, optional_doctypes=None)` | Create missing Custom Fields with native `create_custom_fields`; validate fields and `insert_after` ordering | Preserve matching fields; reject fieldtype conflicts |
| `import_property_setters(source, *, file=None, optional_doctypes=None)` | Create missing DocType-level or field-level Property Setters via native `make_property_setter` | Preserve existing setters |
| `import_doctype_records(source, doctype, *, file=None, optional_doctypes=None)` | Insert missing regular DocType documents with explicit stable names | Preserve existing named documents |

Each importer returns `ImportResult(created, updated, existing, skipped)`. `updated` is currently reserved; imports are insert-missing-only by design. JSON input must be an **array of objects**. `source` can be an importable package directory or filesystem path; `file` selects a particular JSON file in that directory.

The implementation uses native Frappe APIs and ORM, not raw SQL. Frappe owns patch transaction handling and maintains the authoritative Patch Log.

## Installation

**For development/testing from the PR branch** (within the Python environment used by your Frappe bench):

```bash
python -m pip install "git+https://github.com/Aakvatech-Limited/frappe-migration-utils.git@feat/initial-migration-utilities"
```

After a stable package is published, a consuming app may add a bounded dependency to its existing `[project].dependencies` in `pyproject.toml`, for example:

```toml
dependencies = [
  "frappe-migration-utils>=0.1,<0.2"
]
```

**Do not run `bench get-app` or add `frappe_migration_utils` to `apps.txt`**: this library is not a Frappe application. Do not assume that `pip install frappe-migration-utils` works until an actual release is published.

## Quick start: add a Custom Field

In a consuming Frappe app, keep each new migration batch in its own JSON file and create a corresponding one-time patch.

```text
my_app/
├── pyproject.toml
└── my_app/
    ├── patches.txt
    └── patches/
        └── custom_field/
            ├── __init__.py
            ├── add_external_reference_20261009.py
            └── custom_field_json/
                ├── __init__.py
                └── add_external_reference_20261009.json
```

**JSON** — `my_app/my_app/patches/custom_field/custom_field_json/add_external_reference_20261009.json`:

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

**Patch** — `my_app/my_app/patches/custom_field/add_external_reference_20261009.py`:

```python
from frappe_migration_utils import import_custom_fields


def execute():
    import_custom_fields(
        "my_app.patches.custom_field.custom_field_json",
        file="add_external_reference_20261009.json",
    )
```

**Patch registration** — append a *new* dotted entry beneath `[post_model_sync]` in the consuming app's `patches.txt`:

```text
[post_model_sync]
my_app.patches.custom_field.add_external_reference_20261009
```

Keep all existing patch entries intact. Run the consuming application's normal `bench --site <site-name> migrate` workflow from the bench. Frappe handles once-only execution through its Patch Log.

## Property Setter example

```json
[
  {
    "doc_type": "Sales Invoice",
    "doctype_or_field": "DocField",
    "field_name": "customer",
    "property": "description",
    "value": "Customer linked to this invoice",
    "property_type": "Small Text"
  }
]
```

```python
from frappe_migration_utils import import_property_setters


def execute():
    import_property_setters(
        "my_app.patches.property_setter.property_setter_json",
        file="add_customer_description_20261009.json",
    )
```

For DocType-wide settings, use `doctype_or_field: "DocType"`. Field-level setters require a real target field. Existing matching setters are not overwritten.

## Named master-record example

```json
[
  {"name": "Implementation Services", "is_group": 0}
]
```

```python
from frappe_migration_utils import import_doctype_records


def execute():
    import_doctype_records(
        "my_app.patches.item_group.item_group_json",
        doctype="Item Group",
        file="add_implementation_services_20261009.json",
    )
```

Every record needs a stable `name`. The generic importer intentionally does not resolve renamed documents, auto-generated naming, Single DocTypes, or child-table records. Use an app-specific migration for those cases.

## Optional integrations

Missing DocTypes **fail by default**. For a truly optional installed-app integration, specify the exact optional DocType:

```python
import_custom_fields(
    "my_app.patches.custom_field.custom_field_json",
    file="optional_fields_20261009.json",
    optional_doctypes=["Optional Integration DocType"],
)
```

An optional DocType absent during execution is skipped. **Once Frappe records the patch as completed, installing that optional app later will not rerun the patch.** Add a separate later patch or installation event for deferred initialization.

## Migration safety contract

- **Never silently overwrite or delete site-owned records.** Existing Custom Fields, Property Setters, and named documents are kept as-is.
- **Do not edit released migration JSON or historical patches.** For a new change, create a new JSON batch and unique patch entry.
- **Do not invoke these importers from recurring `after_migrate` hooks.** They are designed for native one-time patches.
- **Fail visibly on incompatible metadata.** Required missing DocTypes, standard-field collisions, conflicting Custom Field types, unresolved/circular `insert_after` references, and invalid Property Setter targets raise migration errors.
- **Do not assume successful metadata presence proves database-column health.** PR #1 does not implement automatic repair of missing physical columns or full physical-schema verification.
- **Avoid ambiguous master identity.** Renames and generated names require specialized migrations.
- **Do not change historical Frappe Patch Log entries** to force reruns.

### What happens on rerun?

If a patch is already in Frappe's Patch Log, Frappe normally does not rerun it. If an importer is called directly on data that already exists, it counts matching records as `existing` and does not update them; incompatible definitions may still raise errors. This behavior is not a substitute for the native Patch Log or a promise of transactional recovery.

## Compatibility, validation, and release readiness

| Area | Current status |
| --- | --- |
| Python | `>=3.10`, defined in `pyproject.toml` |
| Package | Hatchling build; package version declared as `0.1.0` |
| Frappe | Requires a site-initialized Frappe runtime when importers execute |
| ERPNext | Not a package dependency; examples using ERPNext DocTypes require ERPNext at runtime |
| CI | Ruff, pytest, package build, and Twine validation on Python 3.10–3.12 |
| Frappe v15 / v16 + MariaDB | **Integration testing outstanding** |
| PyPI | **Not published as of PR #1** |

Before production use, verify on disposable Frappe v15 and v16 sites: clean installs, re-migration, existing customer-edited values, field dependencies, physical table columns, optional integration behavior, and failure/rollback cases. Python-only CI is not sufficient evidence of production compatibility.

## Developer workflow

From a checkout of the PR implementation:

```bash
python -m pip install -e ".[dev]"
python -m ruff check src tests
python -m pytest -q
python -m build
python -m twine check dist/*
```

Project layout:

```text
src/frappe_migration_utils/
  __init__.py
  common.py
  custom_fields.py
  documents.py
  exceptions.py
  json_loader.py
  property_setters.py
tests/
docs/
skills/frappe-migration-scaffolding/
```

The repository also includes guidance for AI agents and a candidate patch-scaffolding script. It does not automatically edit a consuming app's dependency declarations or `patches.txt`.

## Troubleshooting

| Symptom | Likely cause / action |
| --- | --- |
| `Migration source not found` | Check Python package importability, actual JSON location, and `file` name |
| `expected a JSON array of document objects` | Wrap entries in a JSON list; do not supply a single object |
| Required DocType missing | Install/sync the owning app before this patch or deliberately mark it optional |
| Unresolved `insert_after` | Fix the referenced field name or circular dependency |
| Custom Field fieldtype conflict | Write an explicit migration after reviewing existing site metadata |
| Field metadata exists but database column is absent | Stop and investigate with Frappe's supported schema tools; PR #1 does not auto-repair it |
| Optional integration installed after patch ran | Add a new patch; completed patches will not replay |

## AI agents and app scaffolding

- [AGENTS.md](AGENTS.md) — repository-wide instructions and non-negotiable safeguards
- [docs/AGENT_USAGE.md](docs/AGENT_USAGE.md) — importer API and operational rules
- [docs/APP_SCAFFOLDING.md](docs/APP_SCAFFOLDING.md) — layout for consuming applications
- [skills/frappe-migration-scaffolding](skills/frappe-migration-scaffolding) — reusable agent skill and scaffold generator

## Versioning, contributing, and license

The initial package declares version `0.1.0`. Treat API changes as versioned changes and avoid silently replacing behavior relied upon by existing app patches. Contributions should include focused tests, documentation, and verification of safe migration behavior. Production-facing changes should also be tested against actual Frappe/MariaDB sites.

Licensed under [MIT](LICENSE). Maintained by [Aakvatech Limited](https://github.com/Aakvatech-Limited).

### Implementation references

This README is based on the source and documentation proposed in [PR #1](https://github.com/Aakvatech-Limited/frappe-migration-utils/pull/1), particularly `src/frappe_migration_utils/custom_fields.py`, `property_setters.py`, `documents.py`, `json_loader.py`, `common.py`, `pyproject.toml`, and the accompanying guidance documents. The unmerged `main` branch does not yet contain this implementation.
