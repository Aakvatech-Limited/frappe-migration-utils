"""One-time JSON-based Frappe migration helpers.

Frappe's patches.txt/Patch Log determines when migrations execute.
"""

from .custom_fields import import_custom_fields
from .documents import import_doctype_records
from .property_setters import import_property_setters

__all__ = ["import_custom_fields", "import_property_setters", "import_doctype_records"]
