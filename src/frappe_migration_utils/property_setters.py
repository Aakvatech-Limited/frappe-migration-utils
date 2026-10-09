"""Initialize missing Property Setters using native Frappe APIs."""

import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

from .common import ImportResult, require_doctype, validate_optional
from .exceptions import MigrationError
from .json_loader import load_records


def import_property_setters(
    source: str,
    *,
    file: str | None = None,
    optional_doctypes=None,
) -> ImportResult:
    """Only create absent setters; existing site-specific values stay untouched."""
    optional = validate_optional(optional_doctypes)
    result = ImportResult()
    for entry in load_records(source, file):
        dt = entry.get("doc_type") or entry.get("doc_type_name")
        prop = entry.get("property")
        field = entry.get("field_name")
        for_doctype = entry.get("doctype_or_field") == "DocType"
        if not dt or not prop:
            raise MigrationError(f"Invalid Property Setter definition: {entry}")
        if not require_doctype(frappe, dt, optional):
            result.skipped += 1
            continue
        if not for_doctype:
            if not field or not frappe.get_meta(dt).has_field(field):
                raise MigrationError(f"{dt}.{field}: Property Setter target field does not exist")
        filters = {
            "doc_type": dt,
            "doctype_or_field": "DocType" if for_doctype else "DocField",
            "property": prop,
        }
        if not for_doctype:
            filters["field_name"] = field
        if frappe.db.exists("Property Setter", filters):
            result.existing += 1
            continue
        try:
            make_property_setter(
                doctype=dt,
                fieldname=None if for_doctype else field,
                property=prop,
                value=entry.get("value"),
                property_type=entry.get("property_type"),
                for_doctype=for_doctype,
                validate_fields_for_doctype=True,
            )
        except Exception as exc:
            raise MigrationError(f"Failed creating Property Setter {dt}.{field}.{prop}: {exc}") from exc
        result.created += 1
    return result
