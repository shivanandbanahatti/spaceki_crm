import inspect
import json

import frappe
from crm.api import doc as crm_doc

ZOHO_DEAL_KANBAN_FIELDS = [
	"organization",
	"organization_name",
	"contact",
	"deal_value",
	"expected_deal_value",
]

_GET_DATA_PARAMS = set(inspect.signature(crm_doc.get_data).parameters.keys())


@frappe.whitelist()
def get_data(*args, **kwargs):
	view = kwargs.get("view")
	if isinstance(view, str):
		try:
			view = json.loads(view) if view else {}
		except json.JSONDecodeError:
			view = {}

	view_type = (view or {}).get("view_type")
	doctype = kwargs.get("doctype")

	if doctype == "CRM Deal":
		rows = kwargs.get("rows")
		if isinstance(rows, str):
			try:
				rows = json.loads(rows) if rows else []
			except json.JSONDecodeError:
				rows = []
		elif not rows:
			rows = []
		# `name` MUST be present: the kanban/list card builds its Deal route as
		# {name: 'Deal', params: {dealId: row.name}} and the frontend only exposes
		# fields listed in the returned `rows`. Without it every card fails to
		# resolve its route ("Missing required param dealId").
		for field in ("name", "deal_name", "organization_name"):
			if field not in rows:
				rows.append(field)
		kwargs["rows"] = json.dumps(rows)

		if view_type == "kanban":
			kwargs["title_field"] = "deal_name"
			kwargs["kanban_fields"] = json.dumps(ZOHO_DEAL_KANBAN_FIELDS)

	filtered_kwargs = {k: v for k, v in kwargs.items() if k in _GET_DATA_PARAMS}
	result = crm_doc.get_data(*args, **filtered_kwargs)

	if isinstance(result, dict) and result.get("view_type") == "kanban" and result.get("data"):
		_enrich_kanban_columns(result)

	return result


def _enrich_kanban_columns(result):
	for column in result.get("data") or []:
		kc = column.get("column") or {}
		stage = kc.get("name")
		if not stage:
			continue

		kc["stage_probability"] = frappe.db.get_value("CRM Deal Status", stage, "probability") or 0
		totals = frappe.db.sql(
			"""
			select
				count(*) as deal_count,
				sum(
					coalesce(
						nullif(expected_deal_value, 0),
						nullif(deal_value, 0) * coalesce(probability, 0) / 100,
						0
					)
				) as stage_total
			from `tabCRM Deal`
			where status = %s
			""",
			stage,
			as_dict=True,
		)[0]
		kc["stage_total"] = totals.stage_total or 0
		kc["deal_count"] = totals.deal_count or kc.get("count") or 0
