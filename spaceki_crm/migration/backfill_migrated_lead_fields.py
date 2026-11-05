"""Backfill incomplete fields on Upagna leads migrated DEV -> PROD.

Matches by normalized phone. Updates zoho_company, description, city
(and lead_managed_by / source if empty on prod but filled on dev).
Does NOT create new leads or change lead names.
"""

from __future__ import annotations

import re

import frappe

UPAGNA = "upagna@nrgroupindia.com"
PROD_SINCE = "2026-09-22 20:00:00"
PROD_UNTIL = "2026-09-23"
DEV_SINCE = "2026-09-02"

COPY_FIELDS = (
	"zoho_company",
	"description",
	"city",
	"lead_managed_by",
	"source",
	"industry",
	"territory",
	"job_title",
	"website",
	"email",
	"organization",
)


def normalize_phone(phone: str | None) -> str | None:
	if not phone:
		return None
	digits = re.sub(r"\D", "", str(phone))
	return digits or None


def _dev_city(row) -> str | None:
	return row.get("city") or row.get("custom_lead_city") or None


def backfill_from_dev(dry_run: bool = True):
	"""
	Must be invoked carefully:
	1) Load DEV leads into memory
	2) Switch to PROD and update matched leads
	"""
	# --- Load DEV ---
	frappe.init(site="dev.spaceki.com")
	frappe.connect()
	dev_meta = frappe.get_meta("CRM Lead")
	dev_has_custom_city = dev_meta.has_field("custom_lead_city")
	dev_fields = [
		"name",
		"phone",
		"mobile_no",
		"zoho_company",
		"description",
		"city",
		"lead_managed_by",
		"source",
		"industry",
		"territory",
		"job_title",
		"website",
		"email",
		"organization",
		"lead_name",
	]
	if dev_has_custom_city:
		dev_fields.append("custom_lead_city")

	dev_rows = frappe.db.sql(
		f"""
		SELECT {", ".join(f"`{f}`" for f in dev_fields)}
		FROM `tabCRM Lead`
		WHERE (lead_owner=%s OR owner=%s) AND creation >= %s
		""",
		(UPAGNA, UPAGNA, DEV_SINCE),
		as_dict=True,
	)
	dev_by_phone: dict[str, dict] = {}
	for row in dev_rows:
		pk = normalize_phone(row.mobile_no) or normalize_phone(row.phone)
		if not pk:
			continue
		# prefer row that has more filled important fields
		existing = dev_by_phone.get(pk)
		if not existing:
			dev_by_phone[pk] = row
		else:
			score = sum(1 for f in ("zoho_company", "description", "city") if row.get(f) or (f == "city" and row.get("custom_lead_city")))
			old = sum(1 for f in ("zoho_company", "description", "city") if existing.get(f) or (f == "city" and existing.get("custom_lead_city")))
			if score >= old:
				dev_by_phone[pk] = row
	print(f"DEV indexed phones: {len(dev_by_phone)} (from {len(dev_rows)} leads)")
	frappe.destroy()

	# --- Update PROD ---
	frappe.init(site="erp.spaceki.com")
	frappe.connect()
	prod_meta = frappe.get_meta("CRM Lead")
	prod_fields = [f for f in COPY_FIELDS if prod_meta.has_field(f)]

	prod_rows = frappe.db.sql(
		"""
		SELECT name, phone, mobile_no, zoho_company, description, city, lead_managed_by,
		       source, industry, territory, job_title, website, email, organization, lead_name
		FROM `tabCRM Lead`
		WHERE lead_owner=%s AND creation >= %s AND creation < %s
		ORDER BY creation
		""",
		(UPAGNA, PROD_SINCE, PROD_UNTIL),
		as_dict=True,
	)
	print(f"PROD migration batch: {len(prod_rows)}")

	updated = 0
	skipped_no_match = 0
	skipped_nothing = 0
	field_updates = {f: 0 for f in prod_fields}
	examples = []

	for prod in prod_rows:
		pk = normalize_phone(prod.mobile_no) or normalize_phone(prod.phone)
		if not pk or pk not in dev_by_phone:
			skipped_no_match += 1
			continue

		dev = dev_by_phone[pk]
		updates = {}
		for f in prod_fields:
			if f == "city":
				dev_val = _dev_city(dev)
			else:
				dev_val = dev.get(f)
			prod_val = prod.get(f)
			if dev_val and not prod_val:
				updates[f] = dev_val
				field_updates[f] += 1

		if not updates:
			skipped_nothing += 1
			continue

		if dry_run:
			if len(examples) < 8:
				examples.append((prod.name, dev.name, pk, updates))
		else:
			frappe.db.set_value("CRM Lead", prod.name, updates, update_modified=False)

		updated += 1
		if not dry_run and updated % 50 == 0:
			frappe.db.commit()
			print(f"  updated {updated}...")

	if not dry_run:
		frappe.db.commit()
		frappe.clear_cache()

	print(f"\n{'Would update' if dry_run else 'Updated'}: {updated}")
	print(f"No phone match: {skipped_no_match}")
	print(f"Already complete / nothing to copy: {skipped_nothing}")
	print("Field update counts:")
	for f, c in field_updates.items():
		if c:
			print(f"  {f}: {c}")

	print("\nExamples:")
	for prod_name, dev_name, pk, updates in examples:
		print(f"  PROD {prod_name} <- DEV {dev_name} phone={pk}")
		for k, v in updates.items():
			vv = (str(v)[:80] + "…") if v and len(str(v)) > 80 else v
			print(f"    set {k}={vv!r}")

	# Specific user example
	target = "CRM-LEAD-2026-21782"
	if frappe.db.exists("CRM Lead", target):
		row = frappe.db.get_value(
			"CRM Lead",
			target,
			["zoho_company", "description", "city", "phone", "mobile_no"],
			as_dict=True,
		)
		print(f"\nCheck {target} NOW: {row}")

	frappe.destroy()
	return {
		"updated": updated,
		"skipped_no_match": skipped_no_match,
		"skipped_nothing": skipped_nothing,
		"field_updates": field_updates,
		"dry_run": dry_run,
	}


def execute():
	"""bench-style entry: dry_run first via kwargs in callers."""
	return backfill_from_dev(dry_run=True)
