"""Backfill lead_owner from document owner for leads created without an owner."""

import frappe

from spaceki_crm.overrides.crm_lead import normalize_phone


def backfill_lead_owner_from_document_owner(
	owner: str | None = None,
	since: str | None = None,
	dry_run: bool = True,
):
	"""Set lead_owner = owner when lead_owner is empty (e.g. Excel imports)."""
	conditions = ["(lead_owner IS NULL OR lead_owner = '')", "owner NOT IN ('Administrator', 'Guest')"]
	values: list = []

	if owner:
		conditions.append("owner = %s")
		values.append(owner)
	if since:
		conditions.append("creation >= %s")
		values.append(since)

	leads = frappe.db.sql(
		f"""
		SELECT name, owner, lead_name, phone, mobile_no
		FROM `tabCRM Lead`
		WHERE {" AND ".join(conditions)}
		ORDER BY creation
		""",
		tuple(values),
		as_dict=True,
	)

	updated = 0
	skipped = 0
	for lead in leads:
		if not frappe.db.exists("User", lead.owner):
			skipped += 1
			continue

		if dry_run:
			print(f"Would set lead_owner={lead.owner} on {lead.name} ({lead.lead_name})")
		else:
			frappe.db.set_value("CRM Lead", lead.name, "lead_owner", lead.owner, update_modified=False)
			doc = frappe.get_doc("CRM Lead", lead.name)
			doc.assign_agent(lead.owner)
		updated += 1

	if not dry_run and updated:
		frappe.db.commit()

	print(f"{'Would update' if dry_run else 'Updated'}: {updated}, skipped: {skipped}")
	return {"updated": updated, "skipped": skipped, "dry_run": dry_run}


def cleanup_duplicate_imports(
	owner: str | None = None,
	since: str | None = None,
	dry_run: bool = True,
):
	"""Remove duplicate leads from re-imports, keeping the earliest record per phone."""
	conditions = ["(phone IS NOT NULL OR mobile_no IS NOT NULL)"]
	values: list = []

	if owner:
		conditions.append("owner = %s")
		values.append(owner)
	if since:
		conditions.append("creation >= %s")
		values.append(since)

	leads = frappe.db.sql(
		f"""
		SELECT name, owner, lead_name, phone, mobile_no, creation
		FROM `tabCRM Lead`
		WHERE {" AND ".join(conditions)}
		ORDER BY creation ASC
		""",
		tuple(values),
		as_dict=True,
	)

	seen: dict[str, str] = {}
	to_delete: list[str] = []

	for lead in leads:
		norm = normalize_phone(lead.phone) or normalize_phone(lead.mobile_no)
		if not norm:
			continue

		if norm in seen:
			to_delete.append(lead.name)
			if dry_run:
				print(f"Would delete duplicate {lead.name} ({lead.lead_name}) — keeps {seen[norm]}")
		else:
			seen[norm] = lead.name

	if dry_run:
		print(f"Would delete {len(to_delete)} duplicate leads")
	else:
		for name in to_delete:
			frappe.delete_doc("CRM Lead", name, ignore_permissions=True, force=True)
		frappe.db.commit()
		print(f"Deleted {len(to_delete)} duplicate leads")

	return {"deleted": len(to_delete), "kept": len(seen), "dry_run": dry_run}


def execute():
	"""bench execute spaceki_crm.migration.fix_imported_lead_owners.execute"""
	backfill_lead_owner_from_document_owner(since="2026-09-02", dry_run=False)
	cleanup_duplicate_imports(since="2026-09-02", owner="upagna@nrgroupindia.com", dry_run=False)
