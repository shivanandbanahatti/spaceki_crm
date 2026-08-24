import frappe


def _erpnext_enabled() -> bool:
	if not frappe.db.exists("DocType", "ERPNext CRM Settings"):
		return False
	try:
		return bool(frappe.db.get_single_value("ERPNext CRM Settings", "enabled"))
	except Exception:
		return False


@frappe.whitelist()
def get_related_counts(doctype: str, name: str) -> dict:
	"""Lightweight related-record counts for form-script header actions."""
	frappe.has_permission(doctype, "read", name, throw=True)

	filters = {"reference_doctype": doctype, "reference_docname": name}
	file_filters = {"attached_to_doctype": doctype, "attached_to_name": name}

	counts = {
		"notes": frappe.db.count("FCRM Note", filters),
		"tasks": frappe.db.count("CRM Task", filters),
		"calls": frappe.db.count("CRM Call Log", filters),
		"attachments": frappe.db.count("File", file_filters),
		"comments": frappe.db.count(
			"Comment",
			{"reference_doctype": doctype, "reference_name": name, "comment_type": "Comment"},
		),
		"boq": 0,
		"erpnext_enabled": _erpnext_enabled(),
	}
	counts["work"] = counts["tasks"] + counts["comments"]

	if frappe.db.exists("DocType", "Deal BOQ Item"):
		if doctype == "CRM Lead":
			counts["boq"] = frappe.db.count("Deal BOQ Item", {"lead": name})
		elif doctype == "CRM Deal":
			counts["boq"] = frappe.db.count("Deal BOQ Item", {"deal": name})

	return counts
