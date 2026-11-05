"""Correct Auto Create Customer trigger: Qualification → Closed Won.

ERPNext CRM Settings had deal_status=Qualification, which created ERPNext
Customers as soon as a deal entered an early pipeline stage. Align with the
intended Closed Won handoff (same point as Project creation in cost_estimate).
"""

import frappe

TARGET_STATUS = "Closed Won"


def execute():
	if not frappe.db.exists("DocType", "ERPNext CRM Settings"):
		return
	if not frappe.db.exists("CRM Deal Status", TARGET_STATUS):
		frappe.log_error(
			message=f"CRM Deal Status '{TARGET_STATUS}' missing; left ERPNext CRM Settings.deal_status unchanged",
			title="Spaceki CRM: skip deal_status patch",
		)
		return

	current = frappe.db.get_single_value("ERPNext CRM Settings", "deal_status")
	if current == TARGET_STATUS:
		return

	frappe.db.set_single_value("ERPNext CRM Settings", "deal_status", TARGET_STATUS)
