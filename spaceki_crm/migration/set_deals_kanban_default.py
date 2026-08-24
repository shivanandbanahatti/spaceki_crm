import frappe

from spaceki_crm.overrides.crm_view_settings import set_deals_kanban_as_default


def apply():
	set_deals_kanban_as_default()
	frappe.db.commit()
	return "CRM Deal kanban set as default view"
