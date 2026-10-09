"""Shared validation and import result tracking."""

from dataclasses import dataclass

from .exceptions import MigrationError


@dataclass
class ImportResult:
    created: int = 0
    updated: int = 0
    existing: int = 0
    skipped: int = 0


def require_doctype(frappe, doctype: str, optional_doctypes: set[str]) -> bool:
    if frappe.db.exists("DocType", doctype):
        return True
    if doctype in optional_doctypes:
        return False
    raise MigrationError(f"Required DocType {doctype!r} does not exist")


def validate_optional(optional_doctypes) -> set[str]:
    return set(optional_doctypes or ())
