"""SpaceKi deal pipeline: statuses, probabilities, and kanban stage order."""

import json

import frappe

DEAL_PIPELINE = [
	{
		"deal_status": "Qualification",
		"probability": 10,
		"position": 1,
		"type": "Open",
		"color": "gray",
	},
	{
		"deal_status": "Need Analysis / Meeting Done",
		"probability": 20,
		"position": 2,
		"type": "Open",
		"color": "blue",
	},
	{
		"deal_status": "Identify Decision Makers / Decision Discussion",
		"probability": 30,
		"position": 3,
		"type": "Ongoing",
		"color": "cyan",
	},
	{
		"deal_status": "Proposal or Price Quote Submitted",
		"probability": 50,
		"position": 4,
		"type": "Ongoing",
		"color": "teal",
	},
	{
		"deal_status": "Negotiation / Review",
		"probability": 70,
		"position": 5,
		"type": "Ongoing",
		"color": "orange",
	},
	{
		"deal_status": "Closed Won",
		"probability": 100,
		"position": 6,
		"type": "Won",
		"color": "green",
	},
	{
		"deal_status": "Closed Lost",
		"probability": 0,
		"position": 7,
		"type": "Lost",
		"color": "red",
	},
	{
		"deal_status": "Closed Lost to Competition",
		"probability": 0,
		"position": 8,
		"type": "Lost",
		"color": "pink",
	},
]

STATUS_ALIASES = {
	"Needs Analysis / Meeting Done": "Need Analysis / Meeting Done",
	"Proposal/Price Quote Submitted": "Proposal or Price Quote Submitted",
	"Negotiation/Review": "Negotiation / Review",
	"Demo/Making": "Need Analysis / Meeting Done",
	"Proposal/Quotation": "Proposal or Price Quote Submitted",
	"Negotiation": "Negotiation / Review",
	"Ready to Close": "Negotiation / Review",
	"Won": "Closed Won",
	"Lost": "Closed Lost",
}

KANBAN_FIELDS = [
	"organization",
	"organization_name",
	"contact",
	"deal_value",
	"expected_deal_value",
]


def apply_deal_pipeline():
	"""Upsert pipeline statuses, migrate deals, and configure kanban views."""
	_upsert_pipeline_statuses()
	_migrate_deal_records()
	_retire_legacy_statuses()
	_configure_kanban_views()
	frappe.db.commit()
	frappe.clear_cache()


def _upsert_pipeline_statuses():
	for stage in DEAL_PIPELINE:
		name = stage["deal_status"]
		if frappe.db.exists("CRM Deal Status", name):
			frappe.db.set_value(
				"CRM Deal Status",
				name,
				{
					"probability": stage["probability"],
					"position": stage["position"],
					"type": stage["type"],
					"color": stage["color"],
				},
			)
			continue

		doc = frappe.new_doc("CRM Deal Status")
		doc.deal_status = name
		doc.probability = stage["probability"]
		doc.position = stage["position"]
		doc.type = stage["type"]
		doc.color = stage["color"]
		doc.insert(ignore_permissions=True)


def _migrate_deal_records():
	for old, new in STATUS_ALIASES.items():
		if old == new:
			continue
		if not frappe.db.count("CRM Deal", {"status": old}):
			continue
		if not frappe.db.exists("CRM Deal Status", new):
			continue
		frappe.db.sql(
			"update `tabCRM Deal` set status = %s where status = %s",
			(new, old),
		)


def _retire_legacy_statuses():
	canonical = {stage["deal_status"] for stage in DEAL_PIPELINE}
	legacy = set(STATUS_ALIASES.keys()) | {
		"Demo/Making",
		"Proposal/Quotation",
		"Negotiation",
		"Ready to Close",
		"Won",
		"Lost",
	}
	for status in legacy:
		if status in canonical or not frappe.db.exists("CRM Deal Status", status):
			continue
		if frappe.db.count("CRM Deal", {"status": status}):
			continue
		frappe.delete_doc("CRM Deal Status", status, force=True)


def deal_kanban_columns():
	return [
		{"name": stage["deal_status"], "color": stage["color"]}
		for stage in DEAL_PIPELINE
	]


def _configure_kanban_views():
	updates = {
		"column_field": "status",
		"title_field": "deal_name",
		"kanban_columns": json.dumps(deal_kanban_columns()),
		"kanban_fields": json.dumps(KANBAN_FIELDS),
	}

	# Configure every kanban view that already exists (standard + saved views).
	for view in frappe.get_all(
		"CRM View Settings",
		filters={"dt": "CRM Deal", "type": "kanban"},
		pluck="name",
	):
		frappe.db.set_value("CRM View Settings", view, updates)

	# `set_value` above only touches views that already exist. FCRM creates a
	# user's standard kanban lazily (first time they open it), so on a fresh site
	# no standard kanban exists at patch time and it would never get configured.
	# Guarantee at least one configured, default standard kanban view (owned by
	# Administrator) so the Deals page has a working kanban out of the box.
	if not frappe.db.exists(
		"CRM View Settings",
		{"dt": "CRM Deal", "type": "kanban", "is_standard": 1},
	):
		doc = frappe.new_doc("CRM View Settings")
		doc.update(
			{
				"label": "Kanban",
				"dt": "CRM Deal",
				"type": "kanban",
				"is_standard": 1,
				"is_default": 1,
				"route_name": "Deals",
				"user": "Administrator",
				**updates,
			}
		)
		doc.insert(ignore_permissions=True)
