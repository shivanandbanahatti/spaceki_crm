import frappe


def execute():
	name = frappe.db.get_value(
		"Custom Field", {"dt": "CRM Lead", "fieldname": "zoho_company"}
	)
	if name:
		frappe.db.set_value("Custom Field", name, "label", "Company")
	frappe.clear_cache(doctype="CRM Lead")
