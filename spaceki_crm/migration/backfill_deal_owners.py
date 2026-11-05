"""Remap CRM Deal ownership from Zoho 'Lead managed By' for current sales users."""

from __future__ import annotations

import os
from collections import Counter

import frappe

from crm.migration.importer import COMPANY_OWNER
from crm.migration.utils import clean, data_path, get_frappe_name, read_csv
from spaceki_crm.migration.backfill_lead_owners import resolve_managed_by_user


def resolve_deal_owner_from_zoho_row(row: dict, company_owner: str = COMPANY_OWNER) -> str:
	managed = (
		clean(row.get("Lead managed By"))
		or clean(row.get("Lead Managed By"))
		or None
	)
	managed_user = resolve_managed_by_user(managed)
	if managed_user:
		return managed_user
	if frappe.db.exists("User", company_owner):
		return company_owner
	return "Administrator"


def backfill_deal_owners(
	dry_run: bool = True,
	company_owner: str = COMPANY_OWNER,
	limit: int | None = None,
) -> dict:
	stats = Counter()
	by_owner = Counter()
	samples = []

	rows = read_csv("Deals_001.csv", required=False)
	if limit:
		rows = rows[:limit]

	for row in rows:
		stats["csv_rows"] += 1
		zoho_id = clean(row.get("Record Id"))
		if not zoho_id:
			continue

		deal_name = get_frappe_name("CRM Deal", zoho_id)
		if not deal_name:
			stats["skipped_not_in_frappe"] += 1
			continue

		managed_text = clean(row.get("Lead managed By")) or clean(row.get("Lead Managed By")) or None
		target_owner = resolve_deal_owner_from_zoho_row(row, company_owner=company_owner)
		by_owner[target_owner] += 1

		current_owner = frappe.db.get_value("CRM Deal", deal_name, "deal_owner")
		if current_owner == target_owner:
			stats["unchanged"] += 1
			continue

		stats["owner_updates"] += 1
		if len(samples) < 15:
			samples.append(
				f"{deal_name} ({row.get('Deal Name')}): {current_owner!r} -> {target_owner!r} "
				f"(managed_by={managed_text!r})"
			)

		if dry_run:
			stats["would_update"] += 1
			continue

		frappe.db.set_value(
			"CRM Deal",
			deal_name,
			"deal_owner",
			target_owner,
			update_modified=False,
		)
		stats["updated"] += 1

	if not dry_run:
		frappe.db.commit()

	return {
		"dry_run": dry_run,
		"csv": data_path("Deals_001.csv"),
		"stats": dict(stats),
		"by_target_owner": dict(by_owner.most_common()),
		"samples": samples,
	}


def execute(dry_run: bool = True, limit: int | None = None):
	return backfill_deal_owners(dry_run=dry_run, limit=limit)
