"""Zoho-style weighted forecast: expected revenue = deal value x stage probability."""

import frappe
from frappe.utils import flt


def sync_zoho_forecast(doc, method=None):
	"""Keep probability in sync with stage and derive expected deal value."""
	if doc.status:
		stage_probability = frappe.db.get_value("CRM Deal Status", doc.status, "probability")
		if stage_probability is not None:
			doc.probability = flt(stage_probability)

	deal_value = flt(doc.deal_value)
	if deal_value:
		doc.expected_deal_value = deal_value * flt(doc.probability) / 100
