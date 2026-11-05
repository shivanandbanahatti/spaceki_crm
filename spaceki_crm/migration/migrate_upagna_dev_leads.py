"""Migrate Upagna leads that exist only on a source site into the current site.

Designed to run ON production while reading lead payloads prepared from DEV.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import frappe

UPAGNA = "upagna@nrgroupindia.com"


def normalize_phone(phone: str | None) -> str | None:
	if not phone:
		return None
	digits = re.sub(r"\D", "", phone)
	return digits or None


def lead_fingerprint(row: dict) -> tuple[str | None, str | None]:
	phone = normalize_phone(row.get("mobile_no")) or normalize_phone(row.get("phone"))
	parts = []
	for key in ("lead_name", "organization", "email"):
		val = (row.get(key) or "").strip().lower()
		if val:
			parts.append(val)
	name_key = "|".join(parts) if parts else None
	return phone, name_key


def export_dev_only_leads(
	since: str = "2026-09-02",
	owner_user: str = UPAGNA,
	out_path: str = "/tmp/upagna_dev_only_leads.json",
):
	"""Run on DEV: export leads owned/created by Upagna since date that we will push to prod.

	bench execute spaceki_crm.migration.migrate_upagna_dev_leads.export_dev_only_leads
	"""
	fields = [
		"name",
		"first_name",
		"middle_name",
		"last_name",
		"lead_name",
		"organization",
		"email",
		"phone",
		"mobile_no",
		"source",
		"status",
		"territory",
		"industry",
		"job_title",
		"website",
		"lead_owner",
		"owner",
		"creation",
		"lead_managed_by",
		"salutation",
		"gender",
		"no_of_employees",
		"annual_revenue",
	]
	# only fields that exist
	meta = frappe.get_meta("CRM Lead")
	fields = [f for f in fields if f in ("name", "owner", "creation") or meta.has_field(f)]

	leads = frappe.get_all(
		"CRM Lead",
		filters={
			"creation": [">=", since],
			"owner": owner_user,
		},
		fields=fields,
		order_by="creation asc",
		limit_page_length=0,
	)
	# also include lead_owner=upagna created by others after since? prefer owner=upagna for "she created"
	extra = frappe.get_all(
		"CRM Lead",
		filters={
			"creation": [">=", since],
			"lead_owner": owner_user,
			"owner": ["!=", owner_user],
		},
		fields=fields,
		order_by="creation asc",
		limit_page_length=0,
	)
	seen = {l.name for l in leads}
	for l in extra:
		if l.name not in seen:
			leads.append(l)

	payload = [dict(l) for l in leads]
	Path(out_path).write_text(json.dumps(payload, default=str, indent=2))
	print(f"Exported {len(payload)} leads to {out_path}")
	return {"count": len(payload), "path": out_path}


def import_leads_from_json(
	json_path: str = "/tmp/upagna_dev_only_leads.json",
	owner_user: str = UPAGNA,
	dry_run: bool = True,
):
	"""Run on PROD: insert leads missing by phone/name fingerprint.

	bench execute spaceki_crm.migration.migrate_upagna_dev_leads.import_leads_from_json
	"""
	path = Path(json_path)
	if not path.exists():
		raise FileNotFoundError(json_path)

	rows = json.loads(path.read_text())
	print(f"Loaded {len(rows)} leads from {json_path}")

	# Build existing fingerprints on this site
	existing = frappe.db.sql(
		"""
		SELECT name, lead_name, organization, email, phone, mobile_no
		FROM `tabCRM Lead`
		""",
		as_dict=True,
	)
	phones = set()
	names = set()
	for e in existing:
		pk, nk = lead_fingerprint(e)
		if pk:
			phones.add(pk)
		if nk:
			names.add(nk)

	# Valid link values
	valid_sources = set(frappe.get_all("CRM Lead Source", pluck="name"))
	valid_statuses = set(frappe.get_all("CRM Lead Status", pluck="name"))
	valid_territories = set(frappe.get_all("CRM Territory", pluck="name")) if frappe.db.exists("DocType", "CRM Territory") else set()
	valid_industries = set(frappe.get_all("CRM Industry", pluck="name")) if frappe.db.exists("DocType", "CRM Industry") else set()

	to_create = []
	skipped = 0
	for row in rows:
		pk, nk = lead_fingerprint(row)
		if pk and pk in phones:
			skipped += 1
			continue
		if (not pk) and nk and nk in names:
			skipped += 1
			continue
		to_create.append(row)

	print(f"Would create: {len(to_create)} | skip existing: {skipped} | dry_run={dry_run}")

	created = 0
	errors = []
	for row in to_create:
		doc_data = {
			"doctype": "CRM Lead",
			"first_name": row.get("first_name") or (row.get("lead_name") or "Lead").split()[0],
			"middle_name": row.get("middle_name"),
			"last_name": row.get("last_name"),
			"organization": row.get("organization"),
			"email": row.get("email"),
			"phone": row.get("phone"),
			"mobile_no": row.get("mobile_no"),
			"job_title": row.get("job_title"),
			"website": row.get("website"),
			"salutation": row.get("salutation"),
			"gender": row.get("gender"),
			"lead_owner": row.get("lead_owner") or owner_user,
		}
		if row.get("source") in valid_sources:
			doc_data["source"] = row["source"]
		if row.get("status") in valid_statuses:
			doc_data["status"] = row["status"]
		elif "New" in valid_statuses:
			doc_data["status"] = "New"
		if row.get("territory") in valid_territories:
			doc_data["territory"] = row["territory"]
		if row.get("industry") in valid_industries:
			doc_data["industry"] = row["industry"]
		if frappe.get_meta("CRM Lead").has_field("lead_managed_by") and row.get("lead_managed_by"):
			doc_data["lead_managed_by"] = row["lead_managed_by"]

		# clean Nones
		doc_data = {k: v for k, v in doc_data.items() if v not in (None, "")}

		if dry_run:
			print(f"  would create: {doc_data.get('first_name')} {doc_data.get('last_name') or ''} | {doc_data.get('phone') or doc_data.get('mobile_no')}")
			created += 1
			continue

		try:
			doc = frappe.get_doc(doc_data)
			doc.flags.ignore_permissions = True
			doc.insert(ignore_permissions=True)
			# force ownership fields
			frappe.db.set_value(
				"CRM Lead",
				doc.name,
				{
					"owner": owner_user,
					"lead_owner": owner_user,
				},
				update_modified=False,
			)
			created += 1
			if created % 50 == 0:
				frappe.db.commit()
				print(f"  created {created}...")
		except Exception as e:
			errors.append({"dev_name": row.get("name"), "error": str(e)})
			print(f"  ERROR {row.get('name')}: {e}")

	if not dry_run:
		frappe.db.commit()

	print(f"Created: {created} | Skipped: {skipped} | Errors: {len(errors)} | dry_run={dry_run}")
	return {"created": created, "skipped": skipped, "errors": errors, "dry_run": dry_run}
