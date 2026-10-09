"""Generic Frappe DocType initialization. Existing records are site-owned."""

from .common import ImportResult, require_doctype, validate_optional
from .exceptions import MigrationError
from .json_loader import load_records


def import_doctype_records(
    source: str,
    doctype: str,
    *,
    file: str | None = None,
    optional_doctypes=None,
) -> ImportResult:
    """Insert missing named documents, never update existing business data.

    Names must be explicit for normal DocTypes. Generated naming/renames need
    an app-specific patch because a stable identity cannot be inferred.
    """
    import frappe

    result = ImportResult()
    optional = validate_optional(optional_doctypes)
    if not require_doctype(frappe, doctype, optional):
        result.skipped = len(load_records(source, file))
        return result
    meta = frappe.get_meta(doctype)
    if meta.issingle or meta.istable:
        raise MigrationError(f"{doctype}: Single/child DocTypes require an explicit application patch")
    for record in load_records(source, file):
        if record.get("doctype") not in (None, doctype):
            raise MigrationError(f"{doctype}: JSON record declares another DocType")
        name = record.get("name")
        if not isinstance(name, str) or not name.strip():
            raise MigrationError(f"{doctype}: explicit record name required to avoid duplicate master data")
        if frappe.db.exists(doctype, name):
            result.existing += 1
            continue
        values = {**record, "doctype": doctype}
        try:
            frappe.get_doc(values).insert(ignore_permissions=True)
        except Exception as exc:
            raise MigrationError(f"Failed creating {doctype} {name!r}: {exc}") from exc
        result.created += 1
    return result
