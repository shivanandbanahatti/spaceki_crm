"""Expose deal names in CRM list/detail views."""

import frappe

from spaceki_crm.customizations.phase_a import (
	_backfill_missing_deal_names,
	_configure_deals_list_view,
	_set_deal_title_field,
)


def apply():
	_backfill_missing_deal_names()
	_set_deal_title_field()
	_configure_deals_list_view()
	frappe.db.commit()
	frappe.clear_cache()
	return "Deal display settings updated"
