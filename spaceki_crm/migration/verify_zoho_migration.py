"""End-to-end verification of Zoho CRM migration against Frappe CRM on a site."""

from __future__ import annotations

import os
from collections import Counter

import frappe

from crm.migration.importer import COMPANY_OWNER, CURRENT_MANAGED_BY_USERS
from crm.migration.utils import (
	ZOHO_MODULE_TO_DOCTYPE,
	attachments_dir,
	clean,
	data_path,
	find_attachment_file,
	get_frappe_name,
	read_csv,
)

CURRENT_MANAGED_BY = {k.title(): v for k, v in CURRENT_MANAGED_BY_USERS.items()}
CURRENT_MANAGED_BY.update({"Upagna": "upagna@nrgroupindia.com", "Rohit Jangir": "rohit@nrgroupindia.com"})


def _count_csv(filename: str, required: bool = True) -> int:
	try:
		return len(read_csv(filename, required=required))
	except Exception:
		return 0


def _count_frappe(doctype: str, zoho_filter: bool = True) -> int:
	if not frappe.db.exists("DocType", doctype):
		return 0
	if zoho_filter and frappe.db.has_column(doctype, "zoho_record_id"):
		return frappe.db.count(doctype, {"zoho_record_id": ["is", "set"]})
	return frappe.db.count(doctype)


def _missing_zoho_ids(csv_file: str, doctype: str, limit: int = 20) -> list[str]:
	missing = []
	for row in read_csv(csv_file, required=False):
		zoho_id = clean(row.get("Record Id"))
		if zoho_id and not get_frappe_name(doctype, zoho_id):
			missing.append(zoho_id)
	return missing[:limit], len(missing)


def verify_leads() -> dict:
	csv_count = _count_csv("Leads_001.csv")
	frappe_count = frappe.db.count("CRM Lead", {"zoho_record_id": ["is", "set"]})
	missing_sample, missing_total = _missing_zoho_ids("Leads_001.csv", "CRM Lead")

	owner_counts = dict(
		frappe.db.sql(
			"""
			SELECT ifnull(lead_owner, '') owner, COUNT(*) c
			FROM `tabCRM Lead` WHERE zoho_record_id IS NOT NULL AND zoho_record_id != ''
			GROUP BY lead_owner ORDER BY c DESC
			""",
			as_dict=False,
		)
	)

	# Expected owner from CSV rules
	expected = Counter()
	wrong_owner = []
	for row in read_csv("Leads_001.csv", required=False):
		zoho_id = clean(row["Record Id"])
		lead = get_frappe_name("CRM Lead", zoho_id)
		if not lead:
			continue
		managed = clean(row.get("Lead Managed By"))
		if managed:
			primary = managed.split(",")[0].strip()
			exp = CURRENT_MANAGED_BY.get(primary) or CURRENT_MANAGED_BY.get(primary.title())
			if not exp:
				exp = COMPANY_OWNER
		else:
			exp = COMPANY_OWNER
		expected[exp] += 1
		actual = frappe.db.get_value("CRM Lead", lead, "lead_owner")
		if actual != exp:
			wrong_owner.append(
				{"zoho_id": zoho_id, "lead": lead, "expected": exp, "actual": actual, "managed_by": managed}
			)

	extras = frappe.db.count(
		"CRM Lead",
		[["zoho_record_id", "in", ["", None]]],
	)

	return {
		"csv_rows": csv_count,
		"frappe_zoho_leads": frappe_count,
		"missing_in_frappe": missing_total,
		"missing_sample": missing_sample,
		"test_extras_no_zoho_id": extras,
		"owner_counts": owner_counts,
		"expected_owner_from_csv": dict(expected.most_common()),
		"wrong_owner_count": len(wrong_owner),
		"wrong_owner_sample": wrong_owner[:10],
		"managed_by_filled": frappe.db.sql(
			"SELECT COUNT(*) FROM `tabCRM Lead` WHERE zoho_record_id IS NOT NULL AND ifnull(lead_managed_by,'') != ''"
		)[0][0],
	}


def verify_deals() -> dict:
	csv_count = _count_csv("Deals_001.csv")
	frappe_count = _count_frappe("CRM Deal")
	missing_sample, missing_total = _missing_zoho_ids("Deals_001.csv", "CRM Deal")

	no_contact = frappe.db.count("CRM Deal", {"contact": ["in", ["", None]]})
	no_org = frappe.db.count("CRM Deal", {"organization": ["in", ["", None]]})

	stages = frappe.db.sql(
		"SELECT ifnull(status,'') s, COUNT(*) c FROM `tabCRM Deal` GROUP BY status ORDER BY c DESC",
		as_dict=True,
	)

	return {
		"csv_rows": csv_count,
		"frappe_deals": frappe_count,
		"missing_in_frappe": missing_total,
		"missing_sample": missing_sample,
		"deals_without_contact": no_contact,
		"deals_without_organization": no_org,
		"stages": {r.s: r.c for r in stages},
	}


def verify_notes() -> dict:
	csv_count = _count_csv("Notes_001.csv", required=False)
	frappe_count = _count_frappe("FCRM Note")
	missing_sample, missing_total = _missing_zoho_ids("Notes_001.csv", "FCRM Note")

	skipped_no_parent = 0
	orphan_refs = 0
	for row in read_csv("Notes_001.csv", required=False):
		zoho_id = clean(row["Record Id"])
		if get_frappe_name("FCRM Note", zoho_id):
			continue
		parent_module = clean(row.get("Parent Id.Module"))
		parent_zoho = clean(row.get("Parent.id"))
		ref_doctype = ZOHO_MODULE_TO_DOCTYPE.get(parent_module)
		ref_docname = get_frappe_name(ref_doctype, parent_zoho) if ref_doctype else None
		if not ref_docname:
			skipped_no_parent += 1

	for note in frappe.get_all(
		"FCRM Note",
		filters={"zoho_record_id": ["is", "set"]},
		fields=["name", "reference_doctype", "reference_docname"],
		limit=5000,
	):
		if note.reference_doctype and note.reference_docname:
			if not frappe.db.exists(note.reference_doctype, note.reference_docname):
				orphan_refs += 1

	return {
		"csv_rows": csv_count,
		"frappe_notes": frappe_count,
		"missing_in_frappe": missing_total,
		"missing_sample": missing_sample,
		"expected_skipped_no_parent": skipped_no_parent,
		"orphan_reference_links": orphan_refs,
	}


def verify_tasks() -> dict:
	csv_count = _count_csv("Tasks_001.csv", required=False)
	if not frappe.db.exists("DocType", "CRM Task"):
		return {"error": "CRM Task doctype missing"}
	frappe_count = _count_frappe("CRM Task")
	missing_sample, missing_total = _missing_zoho_ids("Tasks_001.csv", "CRM Task")

	no_ref = frappe.db.count(
		"CRM Task",
		{"zoho_record_id": ["is", "set"], "reference_docname": ["in", ["", None]]},
	)

	return {
		"csv_rows": csv_count,
		"frappe_tasks": frappe_count,
		"missing_in_frappe": missing_total,
		"missing_sample": missing_sample,
		"tasks_without_reference": no_ref,
	}


def verify_calls() -> dict:
	csv_count = _count_csv("Calls_001.csv", required=False)
	if not frappe.db.exists("DocType", "CRM Call Log"):
		return {"error": "CRM Call Log doctype missing"}
	frappe_count = _count_frappe("CRM Call Log")
	missing_sample, missing_total = _missing_zoho_ids("Calls_001.csv", "CRM Call Log")
	return {
		"csv_rows": csv_count,
		"frappe_calls": frappe_count,
		"missing_in_frappe": missing_total,
		"missing_sample": missing_sample,
	}


def verify_meetings() -> dict:
	csv_count = _count_csv("Meetings_001.csv", required=False)
	frappe_count = _count_frappe("Event")
	missing_sample, missing_total = _missing_zoho_ids("Meetings_001.csv", "Event")
	return {
		"csv_rows": csv_count,
		"frappe_events": frappe_count,
		"missing_in_frappe": missing_total,
		"missing_sample": missing_sample,
	}


def verify_contacts_accounts() -> dict:
	contacts_csv = _count_csv("Contacts_001.csv", required=False)
	accounts_csv = _count_csv("Accounts_001.csv", required=False)
	contacts_fr = _count_frappe("Contact")
	orgs_fr = _count_frappe("CRM Organization")
	c_missing_sample, c_missing = _missing_zoho_ids("Contacts_001.csv", "Contact")
	a_missing_sample, a_missing = _missing_zoho_ids("Accounts_001.csv", "CRM Organization")
	return {
		"contacts_csv": contacts_csv,
		"contacts_frappe": contacts_fr,
		"contacts_missing": c_missing,
		"accounts_csv": accounts_csv,
		"organizations_frappe": orgs_fr,
		"accounts_missing": a_missing,
	}


def verify_attachments() -> dict:
	rows = read_csv("Attachments_001.csv", required=False)
	att_dir = attachments_dir()
	att_dir_exists = os.path.isdir(att_dir)

	importable = 0
	missing_file = 0
	missing_parent = 0
	already_imported = 0

	module_map = {}
	for filename, module in [
		("Leads_001.csv", "Leads"),
		("Contacts_001.csv", "Contacts"),
		("Deals_001.csv", "Potentials"),
		("Accounts_001.csv", "Accounts"),
		("Notes_001.csv", "Notes"),
		("Meetings_001.csv", "Events"),
	]:
		for row in read_csv(filename, required=False):
			module_map[clean(row["Record Id"])] = module

	for row in rows:
		record_id = clean(row["Record Id"])
		file_name = clean(row.get("File Name"))
		parent_zoho = clean(row.get("Parent.id"))
		parent_module = clean(row.get("Parent Id.Module")) or module_map.get(parent_zoho)
		ref_doctype = ZOHO_MODULE_TO_DOCTYPE.get(parent_module)
		ref_docname = get_frappe_name(ref_doctype, parent_zoho) if ref_doctype else None
		if parent_module == "Notes":
			ref_docname = get_frappe_name("FCRM Note", parent_zoho)
			ref_doctype = "FCRM Note"
		if not ref_docname:
			missing_parent += 1
			continue
		path = find_attachment_file(record_id, file_name)
		if not path:
			missing_file += 1
			continue
		importable += 1
		if file_name and frappe.db.exists(
			"File",
			{
				"file_name": file_name,
				"attached_to_doctype": ref_doctype,
				"attached_to_name": ref_docname,
			},
		):
			already_imported += 1

	files_on_leads = frappe.db.count("File", {"attached_to_doctype": "CRM Lead"})
	files_on_deals = frappe.db.count("File", {"attached_to_doctype": "CRM Deal"})
	files_on_notes = frappe.db.count("File", {"attached_to_doctype": "FCRM Note"})
	total_files = frappe.db.count("File")

	return {
		"csv_rows": len(rows),
		"attachments_dir": att_dir,
		"attachments_dir_exists": att_dir_exists,
		"missing_parent_in_frappe": missing_parent,
		"missing_file_on_disk": missing_file,
		"importable_with_parent_and_file": importable,
		"already_imported_by_filename_match": already_imported,
		"not_yet_imported": max(0, importable - already_imported),
		"files_in_frappe_total": total_files,
		"files_on_leads": files_on_leads,
		"files_on_deals": files_on_deals,
		"files_on_notes": files_on_notes,
	}


def verify_invoices_campaigns() -> dict:
	out = {}
	if frappe.db.exists("DocType", "Sales Invoice"):
		out["invoices_csv"] = _count_csv("Invoices_001.csv", required=False)
		out["invoices_frappe"] = frappe.db.count(
			"Sales Invoice", {"zoho_record_id": ["is", "set"]}
		)
	if frappe.db.exists("DocType", "Campaign"):
		out["campaigns_csv"] = _count_csv("Campaigns_001.csv", required=False)
		out["campaigns_frappe"] = frappe.db.count("Campaign", {"zoho_record_id": ["is", "set"]})
	return out


def run_verification() -> dict:
	"""Full migration verification report."""
	return {
		"input_dir": os.environ.get("ZOHO_INPUT_DIR") or data_path("Leads_001.csv").rsplit("/Data/", 1)[0],
		"site": frappe.local.site,
		"leads": verify_leads(),
		"deals": verify_deals(),
		"notes": verify_notes(),
		"tasks": verify_tasks(),
		"calls": verify_calls(),
		"meetings": verify_meetings(),
		"contacts_accounts": verify_contacts_accounts(),
		"attachments": verify_attachments(),
		"invoices_campaigns": verify_invoices_campaigns(),
	}


def execute():
	"""bench execute spaceki_crm.migration.verify_zoho_migration.execute"""
	import json

	report = run_verification()
	print(json.dumps(report, indent=2, default=str))
	return report
