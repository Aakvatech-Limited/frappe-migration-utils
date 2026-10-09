---
name: frappe-migration-scaffolding
description: Scaffold or review one-time JSON migration patches in Frappe and ERPNext apps using the public frappe-migration-utils Python package. Use when creating a new Frappe app, adding per-DocType JSON patch folders, integrating the package into pyproject.toml, generating a patches.txt entry, or migrating an app from copied Custom Field/Property Setter import helpers. Preserve historical patches, user-customized site data, Frappe Patch Log, and v15/v16 compatibility.
---

# Frappe migration scaffolding

## Workflow
1. Inspect the target app's `pyproject.toml`, `hooks.py`, `patches.txt`, existing migration helpers, and JSON format. Never assume its structure.
2. Read `AGENTS.md` and `docs/AGENT_USAGE.md` from the currently selected release or branch. Match API signatures to installed version; never assume unpublished behavior.
3. Maintain native Frappe once-only execution using `patches.txt`; **do not** introduce manifests, custom journals, fixtures, or `after_migrate` replay loops.
4. Add bounded `frappe-migration-utils` to existing `project.dependencies` only when distribution is available in the application's deployment environment. Avoid replacing existing dependencies or changing unrelated packaging.
5. Use `scripts/scaffold.py` to generate a candidate new patch, JSON folder and patch entry instruction. Review paths, choose a unique patch module name, then append the module path under `[post_model_sync]` in the app's `patches.txt`. Do not silently append or reorder old entries.
6. Use a **new** JSON file for each migration; never modify released JSON consumed by completed patches. Historical patch functions and Patch Log must remain unchanged.
7. Test against disposable sites running supported Frappe/ERPNext major versions, including fresh install, repeated migrate, user-edited Select options, and master-data renames. No raw SQL; verify schema where applicable.
8. Produce diff, tests and a PR. Do not merge automatically.

## Source formats and safety
- Per DocType directory: `app/patches/<snake_case_doctype>/<snake_case_doctype>_json/<new_batch>.json`.
- JSON source must be an **array of objects**; wrapper calls the appropriate package helper.
- `import_custom_fields(source, file=...)`: each record requires `dt`, `fieldname`, `fieldtype`; use the native Frappe creation API.
- `import_property_setters(source, file=...)`: use `doc_type`, `field_name`, `property`, `value`, `property_type`, `doctype_or_field` as defined by the package.
- `import_doctype_records(source, doctype=..., file=...)`: supply an explicit stable `name` for normal DocTypes. Generated names, Single/child documents, renamed master records or destructive transformations need app-specific patch logic.
- Existing Custom Fields / Property Setters and master data are **not** reset. Skip optional missing integration DocTypes only when explicitly declared; note a completed patch will not retry those skipped records.
- Existing metadata with missing physical database columns is not repaired automatically by initial library release; raise or audit this separately, and do not assert full schema health.

## Files
- Read [reference usage](references/usage.md) for wrapper examples, limitations and manual checks.
- Run `python scripts/scaffold.py --help` for generator arguments. It never edits `patches.txt` or `pyproject.toml` and refuses to overwrite files.
