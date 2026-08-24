import os

import frappe
from crm.migration.utils import clean, data_path, get_frappe_name, read_csv


def backfill_deal_links():
	"""Repair deal ↔ contact ↔ organization links from Zoho export."""
	stats = {
		"contacts_linked": 0,
		"contact_rows_added": 0,
		"organizations_linked": 0,
		"org_names_synced": 0,
		"expected_values_filled": 0,
	}

	deals_csv = data_path("Deals_001.csv")
	if not os.path.exists(deals_csv):
		frappe.logger("spaceki_crm").info(
			"Skipping deal link backfill; Zoho export not found at %s", deals_csv
		)
		return stats

	for row in read_csv("Deals_001.csv"):
		zoho_id = clean(row["Record Id"])
		deal_name = get_frappe_name("CRM Deal", zoho_id)
		if not deal_name:
			continue

		deal = frappe.get_doc("CRM Deal", deal_name)
		changed = False

		contact_zoho = clean(row.get("Contact Name.id"))
		if contact_zoho:
			contact = get_frappe_name("Contact", contact_zoho)
			if contact and deal.contact != contact:
				deal.contact = contact
				changed = True
				stats["contacts_linked"] += 1
			if contact and contact not in [c.contact for c in deal.contacts]:
				deal.append("contacts", {"contact": contact, "is_primary": 1})
				changed = True
				stats["contact_rows_added"] += 1
			elif contact:
				for child in deal.contacts:
					if child.contact == contact:
						child.is_primary = 1

		account_zoho = clean(row.get("Account Name.id"))
		if account_zoho:
			organization = get_frappe_name("CRM Organization", account_zoho)
			if organization and deal.organization != organization:
				deal.organization = organization
				changed = True
				stats["organizations_linked"] += 1

		if deal.organization:
			org_label = frappe.db.get_value("CRM Organization", deal.organization, "organization_name")
			if org_label and deal.organization_name != org_label:
				deal.organization_name = org_label
				changed = True
				stats["org_names_synced"] += 1

		deal_value = deal.deal_value or 0
		if deal_value and not deal.expected_deal_value:
			deal.expected_deal_value = deal_value
			changed = True
			stats["expected_values_filled"] += 1

		if changed:
			deal.flags.ignore_mandatory = True
			deal.save(ignore_permissions=True)

	roles_csv = data_path("Deal Contact Role_001.csv")
	if os.path.exists(roles_csv):
		for row in read_csv("Deal Contact Role_001.csv"):
			deal = get_frappe_name("CRM Deal", clean(row.get("Potential Name.id")))
			contact = get_frappe_name("Contact", clean(row.get("Contact Name.id")))
			if not deal or not contact:
				continue
			deal_doc = frappe.get_doc("CRM Deal", deal)
			existing = [c.contact for c in deal_doc.contacts]
			if contact in existing:
				for child in deal_doc.contacts:
					if child.contact == contact:
						child.role = clean(row.get("Role")) or child.role
			else:
				deal_doc.append(
					"contacts",
					{"contact": contact, "is_primary": 0, "role": clean(row.get("Role")) or None},
				)
				stats["contact_rows_added"] += 1
			if not deal_doc.contact:
				deal_doc.contact = contact
				for child in deal_doc.contacts:
					child.is_primary = 1 if child.contact == contact else 0
				stats["contacts_linked"] += 1
			deal_doc.flags.ignore_mandatory = True
			deal_doc.save(ignore_permissions=True)

	frappe.db.commit()
	return stats
