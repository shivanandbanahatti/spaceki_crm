import json

import frappe


def enforce_deals_kanban_default(doc, method=None):
	"""Validate hook on CRM View Settings.

	Two responsibilities, both scoped to CRM Deal views:
	1. Keep the standard kanban as the default view type (and standard list/group_by
	   as non-default) so the Deals page opens in kanban for every user.
	2. Make sure any Deal kanban view is configured with the SpaceKi pipeline
	   columns/fields. FCRM creates a user's standard kanban lazily the first time
	   they open it — without this it lands unconfigured (empty kanban_fields) and
	   renders blank cards. We only fill blanks, so user customisations are kept.
	"""
	if doc.dt != "CRM Deal":
		return

	if doc.is_standard:
		doc.is_default = 1 if doc.type == "kanban" else 0

	if doc.type == "kanban":
		_ensure_kanban_config(doc)


def _ensure_kanban_config(doc):
	"""Populate empty kanban config on a Deal kanban view (non-destructive)."""
	# Imported lazily to avoid an import cycle at hook-registration time.
	from spaceki_crm.migration.deal_pipeline import KANBAN_FIELDS, deal_kanban_columns

	doc.column_field = doc.column_field or "status"
	doc.title_field = doc.title_field or "deal_name"
	if not frappe.parse_json(doc.kanban_fields or "[]"):
		doc.kanban_fields = json.dumps(KANBAN_FIELDS)
	if not frappe.parse_json(doc.kanban_columns or "[]"):
		doc.kanban_columns = json.dumps(deal_kanban_columns())


def set_deals_kanban_as_default():
	"""One-shot: mark kanban standard views as default for CRM Deal."""
	frappe.db.sql(
		"""
		UPDATE `tabCRM View Settings`
		SET is_default = IF(type = 'kanban', 1, 0)
		WHERE dt = 'CRM Deal' AND is_standard = 1
		"""
	)
