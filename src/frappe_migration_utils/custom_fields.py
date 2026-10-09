"""Custom Field initialization with native Frappe creation and safe retries."""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from .common import ImportResult, require_doctype, validate_optional
from .exceptions import MigrationError
from .json_loader import load_records


def _ordered(fields: list[dict], doctype: str, existing_fields: set[str]) -> list[dict]:
    remaining = {item["fieldname"]: item for item in fields}
    if len(remaining) != len(fields):
        raise MigrationError(f"{doctype}: duplicate Custom Field fieldnames")
    ordered = []
    while remaining:
        ready = [
            name for name, definition in remaining.items()
            if not definition.get("insert_after")
            or definition["insert_after"] in existing_fields
            or definition["insert_after"] in {item["fieldname"] for item in ordered}
        ]
        if not ready:
            raise MigrationError(
                f"{doctype}: unresolved/circular insert_after dependencies: "
                + ", ".join(f"{n} -> {v.get('insert_after')}" for n, v in remaining.items())
            )
        for name in ready:
            ordered.append(remaining.pop(name))
    return ordered


def import_custom_fields(
    source: str,
    *,
    file: str | None = None,
    optional_doctypes=None,
) -> ImportResult:
    """Create missing fields only; never reset existing site-edited definitions.

    A missing physical column on an existing field is an error, not authority
    to overwrite or silently rebuild an unknown site's schema.
    """
    optional = validate_optional(optional_doctypes)
    result = ImportResult()
    grouped = {}
    for item in load_records(source, file):
        dt, name = item.get("dt"), item.get("fieldname")
        if not dt or not name or not item.get("fieldtype"):
            raise MigrationError(f"Custom Field definition requires dt, fieldname, fieldtype: {item}")
        grouped.setdefault(dt, []).append(item)
    for dt, definitions in grouped.items():
        if not require_doctype(frappe, dt, optional):
            result.skipped += len(definitions)
            continue
        meta = frappe.get_meta(dt)
        standard = {field.fieldname for field in frappe.get_doc("DocType", dt).fields}
        existing = {field.fieldname for field in meta.fields}
        for item in definitions:
            name = item["fieldname"]
            if name in standard:
                raise MigrationError(f"{dt}.{name}: conflicts with a standard DocField")
        ordered = _ordered(definitions, dt, existing)
        pending = []
        for item in ordered:
            name = item["fieldname"]
            if name in existing:
                stored = frappe.db.get_value(
                    "Custom Field", {"dt": dt, "fieldname": name}, ["fieldtype"], as_dict=True
                )
                if not stored:
                    raise MigrationError(f"{dt}.{name}: metadata exists but is not a Custom Field")
                if stored.fieldtype != item["fieldtype"]:
                    raise MigrationError(
                        f"{dt}.{name}: existing fieldtype {stored.fieldtype} differs from "
                        f"requested {item['fieldtype']}"
                    )
                result.existing += 1
            else:
                pending.append(item)
                existing.add(name)
        if pending:
            # No existing definition is passed to update=True; preserve site customizations.
            try:
                create_custom_fields({dt: pending}, update=True)
            except Exception as exc:
                raise MigrationError(f"Failed creating Custom Fields on {dt}: {exc}") from exc
            frappe.clear_cache(doctype=dt)
            for item in pending:
                if not frappe.db.exists("Custom Field", {"dt": dt, "fieldname": item["fieldname"]}):
                    raise MigrationError(f"{dt}.{item['fieldname']}: creation did not persist")
            result.created += len(pending)
    return result
