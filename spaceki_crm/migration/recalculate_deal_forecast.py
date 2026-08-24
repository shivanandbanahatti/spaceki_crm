"""Recalculate expected_deal_value for all deals from deal_value x stage probability."""

import frappe
from frappe.utils import flt

from spaceki_crm.overrides.crm_deal import sync_zoho_forecast


def recalculate_deal_forecast():
	updated = 0
	for deal in frappe.get_all("CRM Deal", pluck="name"):
		doc = frappe.get_doc("CRM Deal", deal)
		before = flt(doc.expected_deal_value)
		old_probability = flt(doc.probability)
		sync_zoho_forecast(doc)
		if (
			flt(doc.expected_deal_value) != before
			or flt(doc.probability) != old_probability
		):
			doc.db_update()
			updated += 1
	frappe.db.commit()
	frappe.clear_cache()
	return {"updated": updated}
