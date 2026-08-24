import json

import frappe
from crm.fcrm.doctype.crm_view_settings.crm_view_settings import create, get_route_name


def _section(label, name, fields, opened=True):
	return {
		"label": label,
		"name": name,
		"opened": opened,
		"columns": [{"name": f"{name}_col", "fields": fields}],
	}


def _two_col_section(label, name, left_fields, right_fields, opened=True):
	columns = []
	if left_fields:
		columns.append({"name": f"{name}_left", "fields": left_fields})
	if right_fields:
		columns.append({"name": f"{name}_right", "fields": right_fields})
	return {
		"label": label,
		"name": name,
		"opened": opened,
		"columns": columns or [{"name": f"{name}_col", "fields": []}],
	}


ZOHO_MIGRATION_SECTION = _section(
	"Zoho Migration",
	"spaceki_zoho",
	["zoho_record_id", "zoho_created_time", "zoho_modified_time", "campaign"],
	opened=False,
)

DEAL_ZOHO_MIGRATION_SECTION = _section(
	"Zoho Migration",
	"spaceki_zoho",
	["zoho_record_id", "zoho_created_time", "zoho_modified_time"],
	opened=False,
)

DEAL_DATA_TABS = [
	{
		"name": "overview_tab",
		"label": "",
		"sections": [
			_two_col_section(
				"Deal Information",
				"deal_information",
				[
					"deal_name",
					"deal_owner",
					"status",
					"deal_type",
					"next_step",
					"source",
					"lead",
					"contact",
				],
				[
					"deal_value",
					"organization",
					"organization_name",
					"expected_closure_date",
					"closed_date",
					"probability",
					"expected_deal_value",
					"campaign",
				],
			),
			_section("Description", "description_section", ["description"]),
			_two_col_section(
				"Follow-up",
				"follow_up_section",
				["last_follow_up", "next_follow_up"],
				[],
			),
			_two_col_section(
				"Organization Profile",
				"organization_profile",
				["website", "territory", "annual_revenue", "industry"],
				["no_of_employees", "currency", "exchange_rate"],
				opened=False,
			),
			_section("Products", "products_section", ["products"], opened=False),
			_two_col_section("Totals", "totals_section", ["total"], ["net_total"], opened=False),
			DEAL_ZOHO_MIGRATION_SECTION,
		],
	}
]

LEAD_DATA_TABS = [
	{
		"name": "overview_tab",
		"label": "",
		"sections": [
			_two_col_section(
				"Lead Information",
				"lead_information",
				[
					"lead_name",
					"status",
					"lead_owner",
					"lead_managed_by",
					"source",
					"industry",
					"organization",
				],
				[
					"email",
					"mobile_no",
					"phone",
					"whatsapp",
					"job_title",
					"territory",
					"campaign",
				],
			),
			_two_col_section(
				"Client & Project",
				"client_project",
				[
					"zoho_company",
					"hrf",
					"building_type",
					"quote_value",
					"date_of_quote_sent",
				],
				["requirement", "google_maps_location"],
			),
			_section("Description", "description_section", ["description"]),
			_two_col_section(
				"Address",
				"address_section",
				["address_line1", "city", "state"],
				["country", "pincode"],
				opened=False,
			),
			ZOHO_MIGRATION_SECTION,
		],
	}
]

# Legacy names kept for migrations that referenced side-panel sections.
LEAD_PRIORITY_SECTIONS = [
	_section(
		"Business Card",
		"spaceki_business_card",
		[
			"lead_name",
			"organization",
			"email",
			"mobile_no",
			"phone",
			"status",
			"lead_owner",
			"lead_managed_by",
			"source",
			"industry",
		],
	),
	_section(
		"Client & Project",
		"spaceki_client_project",
		[
			"zoho_company",
			"hrf",
			"description",
			"building_type",
			"quote_value",
			"date_of_quote_sent",
			"requirement",
			"google_maps_location",
		],
	),
	_section(
		"Address",
		"spaceki_address",
		["city", "state", "country", "territory", "pincode"],
		opened=False,
	),
	_section(
		"Zoho Migration",
		"spaceki_zoho",
		["zoho_record_id", "zoho_created_time", "zoho_modified_time", "campaign"],
		opened=False,
	),
]

DEAL_PRIORITY_SECTIONS = [
	_section(
		"Deal Summary",
		"spaceki_deal_summary",
		[
			"deal_name",
			"deal_owner",
			"status",
			"organization",
			"lead",
			"contact",
			"expected_deal_value",
			"probability",
			"expected_closure_date",
		],
	),
	_section(
		"Follow-up & Details",
		"spaceki_follow_up",
		[
			"description",
			"deal_type",
			"last_follow_up",
			"next_follow_up",
			"lead_name",
			"organization_name",
			"campaign",
		],
	),
	_section(
		"Zoho Migration",
		"spaceki_zoho",
		["zoho_record_id", "zoho_created_time", "zoho_modified_time"],
		opened=False,
	),
]

LEAD_FORM_SCRIPT = """const SPACEKI_NAV_PREFIX = 'spaceki_nav_'

function spacekiRemoveQuickNavActions(actions) {
	if (!actions?.length) return actions || []
	return actions.filter((action) => !action?.name?.startsWith(SPACEKI_NAV_PREFIX))
}

function spacekiUpsertQuickNavActions(ctx, router, tabs) {
	const actions = spacekiRemoveQuickNavActions(ctx.actions)
	if (!tabs.length) {
		ctx.actions = actions
		return
	}
	actions.push({
		name: `${SPACEKI_NAV_PREFIX}menu`,
		buttonLabel: __('Jump to'),
		group: __('Related'),
		items: tabs.map(({ label, hash }) => ({
			label,
			onClick: () => router.push({ hash }),
		})),
	})
	ctx.actions = actions
}

function spacekiBuildNavTabs(counts) {
	const tabs = [
		{ label: __('Notes ({0})', [counts.notes || 0]), hash: '#notes' },
		{ label: __('Tasks ({0})', [counts.tasks || 0]), hash: '#tasks' },
		{ label: __('Calls ({0})', [counts.calls || 0]), hash: '#calls' },
		{ label: __('Files ({0})', [counts.attachments || 0]), hash: '#attachments' },
	]
	if (counts.erpnext_enabled) {
		tabs.push({ label: __('ERPNext'), hash: '#erpnext' })
	}
	return tabs
}

class CRMLead {
	_addQuickNavActions() {
		if (!this.doc?.name) return
		if (this._spacekiQuickNavLoading) return
		this._spacekiQuickNavLoading = true

		call('spaceki_crm.api.record.get_related_counts', {
			doctype: 'CRM Lead',
			name: this.doc.name,
		})
			.then((counts) => {
				if (!counts) return
				spacekiUpsertQuickNavActions(
					this._originalDocumentContext,
					this.router,
					spacekiBuildNavTabs(counts),
				)
			})
			.finally(() => {
				this._spacekiQuickNavLoading = false
			})
	}

	onLoad() {
		this._addQuickNavActions()
	}
}
"""

DEAL_FORM_SCRIPT = """const SPACEKI_NAV_PREFIX = 'spaceki_nav_'

function spacekiRemoveQuickNavActions(actions) {
	if (!actions?.length) return actions || []
	return actions.filter((action) => !action?.name?.startsWith(SPACEKI_NAV_PREFIX))
}

function spacekiUpsertQuickNavActions(ctx, router, tabs) {
	const actions = spacekiRemoveQuickNavActions(ctx.actions)
	if (!tabs.length) {
		ctx.actions = actions
		return
	}
	actions.push({
		name: `${SPACEKI_NAV_PREFIX}menu`,
		buttonLabel: __('Jump to'),
		group: __('Related'),
		items: tabs.map(({ label, hash }) => ({
			label,
			onClick: () => router.push({ hash }),
		})),
	})
	ctx.actions = actions
}

function spacekiBuildNavTabs(counts) {
	const tabs = [
		{ label: __('Notes ({0})', [counts.notes || 0]), hash: '#notes' },
		{ label: __('Tasks ({0})', [counts.tasks || 0]), hash: '#tasks' },
		{ label: __('Calls ({0})', [counts.calls || 0]), hash: '#calls' },
		{ label: __('Files ({0})', [counts.attachments || 0]), hash: '#attachments' },
	]
	if (counts.erpnext_enabled) {
		tabs.push({ label: __('ERPNext'), hash: '#erpnext' })
	}
	return tabs
}

class CRMDeal {
	_addQuickNavActions() {
		if (!this.doc?.name) return
		if (this._spacekiQuickNavLoading) return
		this._spacekiQuickNavLoading = true

		call('spaceki_crm.api.record.get_related_counts', {
			doctype: 'CRM Deal',
			name: this.doc.name,
		})
			.then((counts) => {
				if (!counts) return
				spacekiUpsertQuickNavActions(
					this._originalDocumentContext,
					this.router,
					spacekiBuildNavTabs(counts),
				)
			})
			.finally(() => {
				this._spacekiQuickNavLoading = false
			})
	}

	onLoad() {
		this._addQuickNavActions()
	}
}
"""



def _disable_quick_nav_scripts():
	"""Tab labels show counts directly; header quick-nav is redundant."""
	for name in ("Spaceki Lead Quick Nav", "Spaceki Deal Quick Nav"):
		if frappe.db.exists("CRM Form Script", name):
			frappe.db.set_value("CRM Form Script", name, "enabled", 0)


def _load_side_panel_sections(doctype):
	layout_name = f"{doctype}-Side Panel"
	if not frappe.db.exists("CRM Fields Layout", layout_name):
		return []
	raw = frappe.db.get_value("CRM Fields Layout", layout_name, "layout")
	if not raw:
		return []
	sections = json.loads(raw)
	if sections and isinstance(sections[0], dict) and sections[0].get("sections"):
		sections = sections[0]["sections"]
	return sections


def _merge_side_panel(doctype, priority_sections):
	existing = _load_side_panel_sections(doctype)
	priority_names = {section.get("name") for section in priority_sections}
	kept = [section for section in existing if section.get("name") not in priority_names]

	contacts = [section for section in kept if section.get("name") == "contacts_section"]
	rest = [section for section in kept if section.get("name") != "contacts_section"]
	merged = contacts + priority_sections + rest

	layout_name = f"{doctype}-Side Panel"
	frappe.db.set_value("CRM Fields Layout", layout_name, "layout", json.dumps(merged))


def _upsert_form_script(doctype, script_name, script):
	existing = frappe.db.get_value("CRM Form Script", {"dt": doctype, "name": script_name}, "name")
	if existing:
		frappe.db.set_value("CRM Form Script", existing, {"script": script, "enabled": 1, "view": "Form"})
		return existing

	doc = frappe.get_doc(
		{
			"doctype": "CRM Form Script",
			"dt": doctype,
			"name": script_name,
			"enabled": 1,
			"view": "Form",
			"script": script,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _ensure_view(doctype, label, view_type, filters=None, group_by=None, order_by="modified desc"):
	if frappe.db.exists("CRM View Settings", {"dt": doctype, "label": label}):
		return

	view = {
		"doctype": doctype,
		"label": label,
		"type": view_type,
		"filters": filters or {},
		"order_by": order_by,
		"group_by_field": group_by or "owner",
		"route_name": get_route_name(doctype),
	}
	doc = create(view)
	frappe.db.set_value("CRM View Settings", doc.name, {"public": 1, "pinned": 1, "user": ""})


def _extend_lead_quick_filters():
	settings_name = frappe.db.get_value(
		"CRM Global Settings",
		{"dt": "CRM Lead", "type": "Quick Filters"},
		"name",
	)
	if not settings_name:
		settings_name = frappe.db.get_value("CRM Global Settings", {"dt": "CRM Lead"}, "name")
	if not settings_name:
		return

	current = frappe.db.get_value("CRM Global Settings", settings_name, "json") or "[]"
	try:
		filters = json.loads(current) if isinstance(current, str) else (current or [])
	except json.JSONDecodeError:
		filters = []

	extra = ["lead_managed_by", "zoho_company", "hrf", "city", "organization"]
	changed = False
	for field in extra:
		if field not in filters:
			filters.append(field)
			changed = True

	if changed:
		frappe.db.set_value("CRM Global Settings", settings_name, "json", json.dumps(filters))



DEALS_LIST_COLUMNS = [
	{"label": "Deal Name", "type": "Data", "key": "deal_name", "width": "14rem"},
	{"label": "Organization", "type": "Link", "key": "organization", "options": "CRM Organization", "width": "11rem"},
	{"label": "Annual Revenue", "type": "Currency", "key": "annual_revenue", "align": "right", "width": "9rem"},
	{"label": "Status", "type": "Link", "options": "CRM Deal Status", "key": "status", "width": "10rem"},
	{"label": "Email", "type": "Data", "key": "email", "width": "12rem"},
	{"label": "Mobile No.", "type": "Data", "key": "mobile_no", "width": "11rem"},
	{"label": "Assigned To", "type": "Text", "key": "_assign", "width": "10rem"},
	{"label": "Last Modified", "type": "Datetime", "key": "modified", "width": "8rem"},
]

DEALS_LIST_ROWS = [
	"name",
	"deal_name",
	"organization",
	"organization_name",
	"annual_revenue",
	"status",
	"email",
	"currency",
	"mobile_no",
	"deal_owner",
	"sla_status",
	"response_by",
	"first_response_time",
	"first_responded_on",
	"modified",
	"_assign",
]


def _set_deal_title_field():
	"""Use Zoho deal name as the document title in CRM."""
	existing = frappe.db.exists(
		"Property Setter",
		{"doc_type": "CRM Deal", "doctype_or_field": "DocType", "property": "title_field"},
	)
	if existing:
		frappe.db.set_value("Property Setter", existing, "value", "deal_name")
	else:
		frappe.make_property_setter(
			{
				"doctype": "CRM Deal",
				"doctype_or_field": "DocType",
				"property": "title_field",
				"value": "deal_name",
				"property_type": "Data",
			}
		)


def _configure_deals_list_view():
	"""Show deal name in list views and load fallback name fields."""
	columns = json.dumps(DEALS_LIST_COLUMNS)
	rows = json.dumps(DEALS_LIST_ROWS)
	for view_name in frappe.get_all(
		"CRM View Settings",
		filters={"dt": "CRM Deal", "type": "list"},
		pluck="name",
	):
		frappe.db.set_value("CRM View Settings", view_name, {"columns": columns, "rows": rows})


def _backfill_missing_deal_names():
	"""Copy organization_name into deal_name when Zoho name was not stored."""
	frappe.db.sql(
		"""
		UPDATE `tabCRM Deal`
		SET deal_name = organization_name
		WHERE (deal_name IS NULL OR deal_name = '')
			AND organization_name IS NOT NULL AND organization_name != ''
		"""
	)


def _configure_deals_kanban_view():
	"""Pinned Zoho-style stage kanban as default deals board."""
	from crm.fcrm.doctype.crm_view_settings.crm_view_settings import create, get_route_name

	label = "Stage View"
	if frappe.db.exists("CRM View Settings", {"dt": "CRM Deal", "label": label}):
		view_name = frappe.db.get_value("CRM View Settings", {"dt": "CRM Deal", "label": label}, "name")
	else:
		view = {
			"doctype": "CRM Deal",
			"label": label,
			"type": "kanban",
			"filters": {},
			"column_field": "status",
			"title_field": "deal_name",
			"kanban_fields": ["organization", "organization_name", "contact", "deal_value", "expected_deal_value"],
			"route_name": get_route_name("CRM Deal"),
		}
		doc = create(view)
		view_name = doc.name

	frappe.db.set_value(
		"CRM View Settings",
		view_name,
		{
			"title_field": "deal_name",
			"kanban_fields": '["organization", "organization_name", "contact", "deal_value", "expected_deal_value"]',
			"column_field": "status",
			"public": 1,
			"pinned": 1,
			"user": "",
		},
	)

	for std in frappe.get_all(
		"CRM View Settings",
		filters={"dt": "CRM Deal", "type": "kanban", "is_standard": 1},
		pluck="name",
	):
		frappe.db.set_value(
			"CRM View Settings",
			std,
			{"title_field": "deal_name", "kanban_fields": '["organization", "organization_name", "contact", "deal_value", "expected_deal_value"]', "label": "Kanban"},
		)


def _configure_deals_kanban():
	"""Match Zoho stage view: deal name title, org, contact, amount on cards."""
	kanban_fields = json.dumps(["organization", "organization_name", "contact", "deal_value", "expected_deal_value"])
	for view in frappe.get_all(
		"CRM View Settings",
		filters={"dt": "CRM Deal", "type": "kanban"},
		fields=["name"],
	):
		frappe.db.set_value(
			"CRM View Settings",
			view.name,
			{
				"title_field": "deal_name",
				"kanban_fields": kanban_fields,
				"column_field": "status",
			},
		)



def _save_fields_layout(doctype, layout_type, layout):
	layout_name = f"{doctype}-{layout_type}"
	layout_json = json.dumps(layout)
	if frappe.db.exists("CRM Fields Layout", layout_name):
		frappe.db.set_value("CRM Fields Layout", layout_name, "layout", layout_json)
		return
	doc = frappe.get_doc(
		{
			"doctype": "CRM Fields Layout",
			"dt": doctype,
			"type": layout_type,
			"layout": layout_json,
		}
	)
	doc.insert(ignore_permissions=True)


def _configure_data_fields_layout(doctype, tabs):
	"""Zoho-style overview in the main record tab."""
	_save_fields_layout(doctype, "Data Fields", tabs)


def _configure_record_side_panel(doctype):
	"""Keep sidebar focused on linked contacts; details live in Overview."""
	existing = _load_side_panel_sections(doctype)
	contacts = [section for section in existing if section.get("name") == "contacts_section"]
	_save_fields_layout(doctype, "Side Panel", contacts)


def apply_phase_a():
	"""Metadata-only Phase A: layouts, scripts, views — no FCRM frontend fork."""
	_configure_data_fields_layout("CRM Deal", DEAL_DATA_TABS)
	_configure_data_fields_layout("CRM Lead", LEAD_DATA_TABS)
	_configure_record_side_panel("CRM Deal")
	_configure_record_side_panel("CRM Lead")

	_disable_quick_nav_scripts()

	_ensure_view("CRM Lead", "By Lead Owner", "group_by", group_by="lead_owner")
	_ensure_view("CRM Lead", "By Status", "group_by", group_by="status")
	_ensure_view("CRM Lead", "By Managed By", "group_by", group_by="lead_managed_by")
	_ensure_view(
		"CRM Deal",
		"Open Deals",
		"list",
		filters={"status": ["not in", ["Closed Won", "Closed Lost", "Closed Lost to Competition"]]},
		order_by="expected_closure_date asc",
	)
	_ensure_view("CRM Deal", "By Deal Owner", "group_by", group_by="deal_owner")
	_set_deal_title_field()
	_configure_deals_list_view()
	_backfill_missing_deal_names()
	_configure_deals_kanban_view()
	_ensure_view(
		"CRM Deal",
		"My Deals",
		"kanban",
		filters={"deal_owner": ["=", frappe.session.user]},
	)

	_configure_deals_kanban()
	from spaceki_crm.overrides.crm_view_settings import set_deals_kanban_as_default

	set_deals_kanban_as_default()
	from spaceki_crm.migration.deal_pipeline import apply_deal_pipeline
	apply_deal_pipeline()
	from spaceki_crm.migration.backfill_deal_links import backfill_deal_links
	backfill_deal_links()
	_extend_lead_quick_filters()
	frappe.db.commit()
	frappe.clear_cache()
