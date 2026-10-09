# Migration-utils scaffolding usage

Use only inside a Frappe bench site during actual patch execution; installing the PyPI Python package does not make it a Frappe app.

Example generated patch for Custom Field:

```python
from frappe_migration_utils import import_custom_fields

def execute():
    import_custom_fields(
        "sample_app.patches.custom_field.custom_field_json",
        file="add_sales_invoice_reference.json",
    )
```

Example JSON:

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

Append exactly one new dotted patch module entry under `[post_model_sync]` in `patches.txt`. No patch manifest or proprietary execution journal. Preserve old entries. Use a new entry to change data in the future. A completed patch does not replay user-customized metadata.

Test the real site on Frappe v15 and v16 and verify actual schema behavior. The first PR version does not implement missing-column repair. Do not switch an installed app's legacy after_migrate hooks without a separate baseline adoption review.
