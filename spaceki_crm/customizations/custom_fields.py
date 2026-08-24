"""Custom fields that SpaceKi CRM depends on.

These were originally created out-of-band during the Zoho migration and were NOT
provisioned by the app, so a fresh install on another instance was missing them
(most importantly `deal_name`, which is the kanban/list title field). Creating
them here — idempotently — makes `spaceki_crm` self-contained.

`organization_name` and `next_step` are intentionally absent: they are standard
Frappe CRM fields and must not be redefined as Custom Fields.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

# Ordered so that fields referenced by a later field's `insert_after` are created
# first. `insert_after` is best-effort anyway — the field is still created if the
# anchor is missing.
CUSTOM_FIELDS = {
	"CRM Deal": [
		{"fieldname": "zoho_id", "label": "Zoho Record Id", "fieldtype": "Data", "read_only": 1, "insert_after": "name"},
		{"fieldname": "custom_description", "label": "Zoho Description", "fieldtype": "Text", "read_only": 1, "insert_after": "name"},
		{"fieldname": "zoho_record_id", "label": "Zoho Record ID", "fieldtype": "Data", "read_only": 1, "insert_after": "lost_notes"},
		# The one field the UI hard-depends on (kanban/list title field).
		{"fieldname": "deal_name", "label": "Deal Name", "fieldtype": "Data", "insert_after": "zoho_record_id"},
		{"fieldname": "erpnext_customer", "label": "Customer in ERPNext", "fieldtype": "Data", "insert_after": "lead_name"},
		{"fieldname": "zoho_created_time", "label": "Zoho Created Time", "fieldtype": "Datetime", "read_only": 1, "insert_after": "next_follow_up"},
		{"fieldname": "zoho_modified_time", "label": "Zoho Modified Time", "fieldtype": "Datetime", "read_only": 1, "insert_after": "zoho_created_time"},
	],
	"CRM Lead": [
		{"fieldname": "zoho_company", "label": "Company", "fieldtype": "Data", "insert_after": "lead_managed_by"},
	],
}


def ensure_custom_fields():
	"""Create/refresh the custom fields SpaceKi CRM relies on. Idempotent."""
	create_custom_fields(CUSTOM_FIELDS, update=True)
	frappe.clear_cache(doctype="CRM Deal")
	frappe.clear_cache(doctype="CRM Lead")
