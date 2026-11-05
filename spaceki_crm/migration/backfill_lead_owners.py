"""Remap CRM Lead ownership from Zoho 'Lead Managed By' for current sales users.

Rules (agreed with client):
1. Lead Managed By = Upagna / Hariharan / Rahul → that User as lead_owner
2. Everything else (ex-employees, empty Managed By, etc.) → Spaceki (info@spaceki.com)
3. Leads with empty Managed By that are already on Spaceki stay as-is (same result)

Only rows present in the Zoho Leads CSV are touched (matched by zoho_record_id).
Extra leads created on dev for testing (no Zoho id / not in export) are left alone.
Production should not have those extras.

Visibility in Frappe CRM is driven by lead_owner (Sales User sees only their own).
"""

from __future__ import annotations

import os
from collections import Counter

import frappe
from frappe.desk.form.assign_to import add as assign

from crm.migration.importer import COMPANY_OWNER, CURRENT_MANAGED_BY_USERS
from crm.migration.utils import clean, data_path, get_frappe_name, read_csv

# Re-export names used by resolve helpers below (imported from importer)


def resolve_managed_by_user(managed_by_text: str | None) -> str | None:
	"""Return Frappe user email if Managed By maps to a current salesperson."""
	text = clean(managed_by_text)
	if not text:
		return None
	# Prefer first name when Zoho has "Upagna,Rahul"
	primary = text.split(",")[0].strip().lower()
	email = CURRENT_MANAGED_BY_USERS.get(primary)
	if email and frappe.db.exists("User", email):
		return email
	return None


def resolve_lead_owner_from_zoho_row(row: dict, company_owner: str = COMPANY_OWNER) -> str:
	"""Current sales from Managed By; everyone else → company Spaceki account."""
	managed = resolve_managed_by_user(row.get("Lead Managed By"))
	if managed:
		return managed
	if frappe.db.exists("User", company_owner):
		return company_owner
	return "Administrator"


def _ensure_assignment(lead_name: str, user: str) -> bool:
	"""Create open ToDo assignment if missing (helps Assigned To UI)."""
	exists = frappe.db.exists(
		"ToDo",
		{
			"reference_type": "CRM Lead",
			"reference_name": lead_name,
			"allocated_to": user,
			"status": ("!=", "Cancelled"),
		},
	)
	if exists:
		return False
	assign(
		{"assign_to": [user], "doctype": "CRM Lead", "name": lead_name},
		ignore_permissions=True,
	)
	return True


def backfill_lead_owners(
	dry_run: bool = True,
	company_owner: str = COMPANY_OWNER,
	limit: int | None = None,
	leads_csv: str | None = None,
	create_assignments: bool = False,
) -> dict:
	"""Apply ownership remap from Zoho Leads CSV onto CRM Lead by zoho_record_id.

	create_assignments: optional ToDo creation (slow). lead_owner alone is enough
	for Sales User list visibility.
	"""
	if leads_csv:
		os.environ["ZOHO_INPUT_DIR"] = os.path.dirname(os.path.dirname(leads_csv))

	csv_path = leads_csv or data_path("Leads_001.csv")
	if not os.path.exists(csv_path):
		frappe.throw(f"Zoho leads CSV not found: {csv_path}")

	stats = Counter()
	by_owner = Counter()
	samples = []

	rows = read_csv("Leads_001.csv") if not leads_csv else None
	if leads_csv:
		import csv

		with open(leads_csv, newline="", encoding="utf-8") as handle:
			rows = list(csv.DictReader(handle))

	if limit:
		rows = rows[:limit]

	for row in rows:
		stats["csv_rows"] += 1
		zoho_id = clean(row.get("Record Id"))
		if not zoho_id:
			stats["skipped_no_zoho_id"] += 1
			continue

		lead_name = get_frappe_name("CRM Lead", zoho_id)
		if not lead_name:
			stats["skipped_not_in_frappe"] += 1
			continue

		managed_text = clean(row.get("Lead Managed By")) or None
		target_owner = resolve_lead_owner_from_zoho_row(row, company_owner=company_owner)
		by_owner[target_owner] += 1

		current = frappe.db.get_value(
			"CRM Lead",
			lead_name,
			["lead_owner", "lead_managed_by"],
			as_dict=True,
		)
		owner_changed = (current.lead_owner or "") != target_owner
		managed_changed = (current.lead_managed_by or None) != managed_text

		if not owner_changed and not managed_changed:
			stats["unchanged"] += 1
			continue

		if owner_changed:
			stats["owner_updates"] += 1
		if managed_changed:
			stats["managed_by_updates"] += 1

		if len(samples) < 15:
			samples.append(
				f"{lead_name}: owner {current.lead_owner!r} -> {target_owner!r}; "
				f"managed_by {current.lead_managed_by!r} -> {managed_text!r}"
			)

		if dry_run:
			stats["would_update"] += 1
			continue

		# lead_owner alone drives Sales User visibility; avoid full doc.save() for speed
		updates = {}
		if owner_changed:
			updates["lead_owner"] = target_owner
		if managed_changed:
			updates["lead_managed_by"] = managed_text
		frappe.db.set_value("CRM Lead", lead_name, updates, update_modified=False)

		if owner_changed and target_owner and create_assignments:
			try:
				if _ensure_assignment(lead_name, target_owner):
					stats["assignments_created"] += 1
			except Exception:
				stats["assignment_failed"] += 1
				frappe.log_error(
					title=f"Lead assign failed {lead_name}",
					message=frappe.get_traceback(),
				)

		stats["updated"] += 1
		if stats["updated"] % 200 == 0:
			frappe.db.commit()

	if not dry_run:
		frappe.db.commit()

	return {
		"dry_run": dry_run,
		"csv": csv_path,
		"stats": dict(stats),
		"by_target_owner": dict(by_owner.most_common()),
		"samples": samples,
	}


def execute(dry_run: bool = True, limit: int | None = None):
	"""bench execute entrypoint."""
	return backfill_lead_owners(dry_run=dry_run, limit=limit)
