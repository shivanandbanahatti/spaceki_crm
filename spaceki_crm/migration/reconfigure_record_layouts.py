"""Move deal/lead details from sidebar into the Overview tab."""

import frappe

from spaceki_crm.customizations.phase_a import (
	DEAL_DATA_TABS,
	LEAD_DATA_TABS,
	_configure_data_fields_layout,
	_configure_record_side_panel,
)


def apply():
	_configure_data_fields_layout("CRM Deal", DEAL_DATA_TABS)
	_configure_data_fields_layout("CRM Lead", LEAD_DATA_TABS)
	_configure_record_side_panel("CRM Deal")
	_configure_record_side_panel("CRM Lead")
	frappe.db.commit()
	frappe.clear_cache()
	return "Deal and Lead layouts reconfigured"
