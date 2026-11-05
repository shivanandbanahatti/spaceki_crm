"""Verify a sales user's migrated data vs what they see as Sales User in Frappe CRM."""

from __future__ import annotations

import os
from collections import Counter

import frappe

from crm.migration.importer import CURRENT_MANAGED_BY_USERS
from crm.migration.utils import ZOHO_MODULE_TO_DOCTYPE, clean, get_frappe_name, read_csv
from crm.permissions.org_hierarchy import get_lead_permission_query_conditions, has_lead_permission

# Zoho "Lead Managed By" display name → Frappe user email
MANAGED_BY_TO_USER = {
	"Upagna": "upagna@nrgroupindia.com",
	"Rohit Jangir": "rohit@nrgroupindia.com",
	"Hariharan": "hariharan@nrgroupindia.com",
	"Rahul": "rahul@nrgroupindia.com",
}


def _zoho_leads_for_managed_by(name: str) -> list[dict]:
	rows = []
	for row in read_csv("Leads_001.csv", required=False):
		managed = clean(row.get("Lead Managed By"))
		if not managed:
			continue
		primary = managed.split(",")[0].strip()
		if primary.lower() == name.lower() or managed.lower().startswith(name.lower()):
			rows.append(row)
	return rows


def _zoho_deals_for_managed_by(name: str) -> list[dict]:
	rows = []
	for row in read_csv("Deals_001.csv", required=False):
		managed = clean(row.get("Lead managed By")) or clean(row.get("Lead Managed By"))
		if managed and managed.lower().startswith(name.lower()):
			rows.append(row)
	return rows


def _notes_on_zoho_leads(lead_zoho_ids: set[str]) -> list[dict]:
	found = []
	for row in read_csv("Notes_001.csv", required=False):
		parent = clean(row.get("Parent.id"))
		module = clean(row.get("Parent Id.Module"))
		if module == "Leads" and parent in lead_zoho_ids:
			found.append(row)
	return found


def _tasks_on_zoho_leads(lead_zoho_ids: set[str]) -> list[dict]:
	found = []
	for row in read_csv("Tasks_001.csv", required=False):
		related = clean(row.get("Related To.id"))
		if related in lead_zoho_ids:
			found.append(row)
	return found


def _attachments_on_zoho_leads(lead_zoho_ids: set[str]) -> list[dict]:
	found = []
	for row in read_csv("Attachments_001.csv", required=False):
		parent = clean(row.get("Parent.id"))
		module = clean(row.get("Parent Id.Module"))
		if parent in lead_zoho_ids and (module == "Leads" or not module):
			found.append(row)
	return found


def _calls_on_zoho_leads(lead_zoho_ids: set[str]) -> list[dict]:
	found = []
	for row in read_csv("Calls_001.csv", required=False):
		related = clean(row.get("Related To.id"))
		if related in lead_zoho_ids:
			found.append(row)
	return found


def _count_visible_leads(user: str) -> int:
	cond = get_lead_permission_query_conditions(user)
	if not cond:
		return frappe.db.count("CRM Lead")
	return frappe.db.sql(f"SELECT COUNT(*) FROM `tabCRM Lead` WHERE {cond}")[0][0]


def _user_can_see_lead(user: str, lead_name: str) -> bool:
	doc = frappe.get_doc("CRM Lead", lead_name)
	return bool(has_lead_permission(doc, "read", user))


def verify_sales_user(managed_by_name: str, user_email: str | None = None) -> dict:
	"""Compare Zoho records for a salesperson vs Frappe visibility as Sales User."""
	user_email = user_email or MANAGED_BY_TO_USER.get(managed_by_name)
	if not user_email:
		frappe.throw(f"Unknown salesperson: {managed_by_name}")

	if not frappe.db.exists("User", user_email):
		return {"error": f"User {user_email} not found on site"}

	roles = frappe.get_roles(user_email)
	zoho_leads = _zoho_leads_for_managed_by(managed_by_name)
	zoho_lead_ids = {clean(r["Record Id"]) for r in zoho_leads}

	# --- Leads ---
	in_frappe = 0
	correct_owner = 0
	can_see = 0
	wrong_owner = []
	not_in_frappe = []
	not_visible = []

	for row in zoho_leads:
		zoho_id = clean(row["Record Id"])
		lead_name = get_frappe_name("CRM Lead", zoho_id)
		if not lead_name:
			not_in_frappe.append({"zoho_id": zoho_id, "name": row.get("Full Name")})
			continue
		in_frappe += 1
		owner = frappe.db.get_value("CRM Lead", lead_name, "lead_owner")
		if owner == user_email:
			correct_owner += 1
		else:
			wrong_owner.append(
				{
					"zoho_id": zoho_id,
					"lead": lead_name,
					"name": row.get("Full Name"),
					"owner": owner,
				}
			)
		if _user_can_see_lead(user_email, lead_name):
			can_see += 1
		else:
			not_visible.append({"zoho_id": zoho_id, "lead": lead_name, "owner": owner})

	visible_total = _count_visible_leads(user_email)

	# --- Related records on her Zoho leads ---
	zoho_notes = _notes_on_zoho_leads(zoho_lead_ids)
	zoho_tasks = _tasks_on_zoho_leads(zoho_lead_ids)
	zoho_attachments = _attachments_on_zoho_leads(zoho_lead_ids)
	zoho_calls = _calls_on_zoho_leads(zoho_lead_ids)
	zoho_deals = _zoho_deals_for_managed_by(managed_by_name)

	notes_in_frappe = 0
	notes_missing = 0
	for row in zoho_notes:
		if get_frappe_name("FCRM Note", clean(row["Record Id"])):
			notes_in_frappe += 1
		else:
			notes_missing += 1

	tasks_in_frappe = 0
	tasks_missing = 0
	for row in zoho_tasks:
		zid = clean(row["Record Id"])
		if get_frappe_name("CRM Task", zid):
			tasks_in_frappe += 1
		else:
			tasks_missing += 1

	attachments_in_frappe = 0
	attachments_missing = 0
	for row in zoho_attachments:
		parent_zoho = clean(row.get("Parent.id"))
		file_name = clean(row.get("File Name"))
		lead_name = get_frappe_name("CRM Lead", parent_zoho)
		if not lead_name:
			attachments_missing += 1
			continue
		if file_name and frappe.db.exists(
			"File",
			{
				"file_name": file_name,
				"attached_to_doctype": "CRM Lead",
				"attached_to_name": lead_name,
			},
		):
			attachments_in_frappe += 1
		else:
			attachments_missing += 1

	calls_in_frappe = 0
	calls_missing = 0
	for row in zoho_calls:
		if get_frappe_name("CRM Call Log", clean(row["Record Id"])):
			calls_in_frappe += 1
		else:
			calls_missing += 1

	deals_in_frappe = 0
	deals_wrong_owner = 0
	deals_missing = 0
	for row in zoho_deals:
		zid = clean(row["Record Id"])
		deal = get_frappe_name("CRM Deal", zid)
		if not deal:
			deals_missing += 1
			continue
		deals_in_frappe += 1
		if frappe.db.get_value("CRM Deal", deal, "deal_owner") != user_email:
			deals_wrong_owner += 1

	# Files on her visible leads (what she sees when opening a lead)
	lead_names = [
		get_frappe_name("CRM Lead", clean(r["Record Id"]))
		for r in zoho_leads
		if get_frappe_name("CRM Lead", clean(r["Record Id"]))
	]
	file_count = 0
	if lead_names:
		file_count = frappe.db.count("File", {"attached_to_doctype": "CRM Lead", "attached_to_name": ["in", lead_names[:5000]]})

	note_count_on_leads = 0
	if lead_names:
		note_count_on_leads = frappe.db.count(
			"FCRM Note",
			{"reference_doctype": "CRM Lead", "reference_docname": ["in", lead_names[:5000]]},
		)

	task_count_on_leads = 0
	if lead_names:
		task_count_on_leads = frappe.db.count(
			"CRM Task",
			{"reference_doctype": "CRM Lead", "reference_docname": ["in", lead_names[:5000]]},
		)

	return {
		"user": user_email,
		"roles": roles,
		"is_sales_user_only": "Sales User" in roles and "Sales Manager" not in roles and "System Manager" not in roles,
		"leads": {
			"zoho_managed_by_count": len(zoho_leads),
			"in_frappe": in_frappe,
			"correct_lead_owner": correct_owner,
			"can_see_as_sales_user": can_see,
			"visible_leads_total_in_list": visible_total,
			"not_in_frappe": len(not_in_frappe),
			"wrong_owner": len(wrong_owner),
			"not_visible": len(not_visible),
			"wrong_owner_sample": wrong_owner[:5],
			"not_in_frappe_sample": not_in_frappe[:5],
			"not_visible_sample": not_visible[:5],
		},
		"notes_on_her_leads": {
			"zoho_count": len(zoho_notes),
			"in_frappe": notes_in_frappe,
			"missing": notes_missing,
			"linked_in_frappe_on_her_leads": note_count_on_leads,
		},
		"tasks_on_her_leads": {
			"zoho_count": len(zoho_tasks),
			"in_frappe": tasks_in_frappe,
			"missing": tasks_missing,
			"linked_in_frappe_on_her_leads": task_count_on_leads,
		},
		"attachments_on_her_leads": {
			"zoho_count": len(zoho_attachments),
			"in_frappe": attachments_in_frappe,
			"missing": attachments_missing,
			"files_on_her_leads_in_frappe": file_count,
		},
		"calls_on_her_leads": {
			"zoho_count": len(zoho_calls),
			"in_frappe": calls_in_frappe,
			"missing": calls_missing,
		},
		"deals_managed_by_her_in_zoho": {
			"zoho_count": len(zoho_deals),
			"in_frappe": deals_in_frappe,
			"missing": deals_missing,
			"wrong_deal_owner": deals_wrong_owner,
		},
		"spot_checks": _spot_checks(zoho_leads[:3], user_email),
	}


def _spot_checks(zoho_rows: list[dict], user: str) -> list[dict]:
	checks = []
	for row in zoho_rows:
		zoho_id = clean(row["Record Id"])
		lead = get_frappe_name("CRM Lead", zoho_id)
		if not lead:
			continue
		checks.append(
			{
				"zoho_id": zoho_id,
				"name": row.get("Full Name"),
				"lead": lead,
				"lead_owner": frappe.db.get_value("CRM Lead", lead, "lead_owner"),
				"lead_managed_by": frappe.db.get_value("CRM Lead", lead, "lead_managed_by"),
				"source": frappe.db.get_value("CRM Lead", lead, "source"),
				"can_see": _user_can_see_lead(user, lead),
				"notes": frappe.db.count(
					"FCRM Note", {"reference_doctype": "CRM Lead", "reference_docname": lead}
				),
				"tasks": frappe.db.count(
					"CRM Task", {"reference_doctype": "CRM Lead", "reference_docname": lead}
				),
				"files": frappe.db.count(
					"File", {"attached_to_doctype": "CRM Lead", "attached_to_name": lead}
				),
			}
		)
	# Prathap Reddy example
	prathap = get_frappe_name("CRM Lead", "zcrm_73429000006644118")
	if prathap:
		checks.append(
			{
				"example": "Mr. Prathap Reddy",
				"lead": prathap,
				"lead_owner": frappe.db.get_value("CRM Lead", prathap, "lead_owner"),
				"lead_managed_by": frappe.db.get_value("CRM Lead", prathap, "lead_managed_by"),
				"source": frappe.db.get_value("CRM Lead", prathap, "source"),
				"can_see": _user_can_see_lead(user, prathap),
			}
		)
	return checks


def verify_all_current_sales_users() -> dict:
	users = ["Upagna", "Hariharan", "Rahul"]
	return {name: verify_sales_user(name) for name in users}


def execute():
	import json

	report = verify_all_current_sales_users()
	print(json.dumps(report, indent=2, default=str))
	return report
