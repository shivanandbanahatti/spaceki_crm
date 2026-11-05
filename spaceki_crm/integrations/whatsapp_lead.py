"""Auto-create CRM Lead from inbound WhatsApp messages with unknown numbers.

Stock Frappe CRM links WhatsApp Message → existing Contact/Lead/Deal on validate,
but does not create a Lead for unknown numbers (see frappe/crm#1931). This hook
fills that gap for Spaceki.

Lead display name prefers Meta WhatsApp profile_name when present; falls back to
the sender phone number.
"""

from __future__ import annotations

import frappe

from crm.integrations.api import get_contact_lead_or_deal_from_number

WHATSAPP_SOURCE = "WhatsApp"


def ensure_whatsapp_lead_source() -> None:
	"""Idempotently create the CRM Lead Source used for inbound WhatsApp leads."""
	if frappe.db.exists("CRM Lead Source", WHATSAPP_SOURCE):
		return
	frappe.get_doc({"doctype": "CRM Lead Source", "source_name": WHATSAPP_SOURCE}).insert(
		ignore_permissions=True
	)


def create_lead_from_whatsapp_message(doc, method=None):
	"""After Insert on WhatsApp Message: unknown inbound number → new CRM Lead.

	Known numbers are already linked by crm.api.whatsapp.validate; we do nothing
	in that case so the WhatsApp tab continues to thread on the existing record
	(except upgrading a phone-as-name Lead when profile_name arrives).
	"""
	if doc.get("type") != "Incoming":
		return

	phone_number = (doc.get("from") or "").strip()
	profile_name = (doc.get("profile_name") or "").strip() or None

	# Already linked (by CRM validate, or manually).
	if doc.get("reference_doctype") and doc.get("reference_name"):
		if doc.reference_doctype == "CRM Lead" and profile_name:
			_upgrade_lead_name_from_profile(doc.reference_name, phone_number, profile_name)
		return

	if not phone_number:
		return

	try:
		name, doctype = get_contact_lead_or_deal_from_number(phone_number)
	except Exception:
		frappe.log_error(
			frappe.get_traceback(),
			"Spaceki CRM WhatsApp: failed to resolve number before lead create",
		)
		return

	if doctype and name:
		# Race: another process linked it, or validate missed setting refs.
		frappe.db.set_value(
			"WhatsApp Message",
			doc.name,
			{"reference_doctype": doctype, "reference_name": name},
			update_modified=False,
		)
		if doctype == "CRM Lead" and profile_name:
			_upgrade_lead_name_from_profile(name, phone_number, profile_name)
		return

	try:
		lead_name = _create_whatsapp_lead(phone_number, profile_name)
	except Exception:
		frappe.log_error(
			frappe.get_traceback(),
			f"Spaceki CRM WhatsApp: failed to create lead for {phone_number}",
		)
		return

	frappe.db.set_value(
		"WhatsApp Message",
		doc.name,
		{"reference_doctype": "CRM Lead", "reference_name": lead_name},
		update_modified=False,
	)


def _display_name_parts(profile_name: str | None, phone_number: str) -> tuple[str, str]:
	"""Return (first_name, last_name). Prefer WhatsApp profile name over phone."""
	display = (profile_name or "").strip() or phone_number
	parts = display.split(None, 1)
	first_name = parts[0]
	last_name = parts[1] if len(parts) > 1 else ""
	return first_name, last_name


def _normalized_digits(value: str | None) -> str:
	if not value:
		return ""
	return "".join(ch for ch in value if ch.isdigit())


def _upgrade_lead_name_from_profile(lead_name: str, phone_number: str, profile_name: str) -> None:
	"""If Lead was titled with the phone number, replace with WhatsApp profile name."""
	if not frappe.db.exists("CRM Lead", lead_name):
		return
	lead = frappe.db.get_value(
		"CRM Lead", lead_name, ["first_name", "mobile_no", "source"], as_dict=True
	)
	if not lead:
		return
	if lead.source and lead.source != WHATSAPP_SOURCE:
		return
	if not _lead_name_is_phone(lead.first_name, lead.mobile_no, phone_number):
		return

	first_name, last_name = _display_name_parts(profile_name, phone_number)
	lead_name_full = " ".join(p for p in (first_name, last_name) if p)
	frappe.db.set_value(
		"CRM Lead",
		lead_name,
		{"first_name": first_name, "last_name": last_name, "lead_name": lead_name_full},
		update_modified=False,
	)


def _lead_name_is_phone(first_name: str | None, mobile_no: str | None, phone_number: str) -> bool:
	"""True when first_name is essentially the phone number (no real person name yet)."""
	if not first_name:
		return True
	fn = first_name.strip()
	fn_digits = _normalized_digits(fn)
	phone_digits = _normalized_digits(phone_number) or _normalized_digits(mobile_no)
	if not fn_digits or not phone_digits:
		return fn in {phone_number, mobile_no}
	# Same digits as phone, or first_name equals stored mobile / sender
	return fn_digits == phone_digits or fn in {phone_number, mobile_no}


def _create_whatsapp_lead(phone_number: str, profile_name: str | None = None) -> str:
	ensure_whatsapp_lead_source()

	first_name, last_name = _display_name_parts(profile_name, phone_number)

	lead = frappe.new_doc("CRM Lead")
	lead.first_name = first_name
	lead.last_name = last_name
	lead.mobile_no = phone_number
	lead.source = WHATSAPP_SOURCE
	lead.insert(ignore_permissions=True)
	return lead.name


def sync_whatsapp_settings_defaults() -> str | None:
	"""Point WhatsApp Settings at the Active default account so CRM enables the WhatsApp tab."""
	if not frappe.db.exists("DocType", "WhatsApp Settings"):
		return None
	if not frappe.db.exists("DocType", "WhatsApp Account"):
		return None

	account = frappe.db.get_value(
		"WhatsApp Account",
		{"status": "Active", "is_default_outgoing": 1},
		"name",
	) or frappe.db.get_value(
		"WhatsApp Account",
		{"status": "Active", "is_default_incoming": 1},
		"name",
	) or frappe.db.get_value("WhatsApp Account", {"status": "Active"}, "name")

	if not account:
		return None

	settings = frappe.get_single("WhatsApp Settings")
	changed = False
	if settings.default_outgoing_account != account:
		settings.default_outgoing_account = account
		changed = True
	if settings.default_incoming_account != account:
		settings.default_incoming_account = account
		changed = True
	if changed:
		settings.save(ignore_permissions=True)
	return account


def backfill_whatsapp_lead_names() -> int:
	"""Rename WhatsApp Leads whose title is still the phone number using profile_name / Profiles."""
	updated = 0
	leads = frappe.get_all(
		"CRM Lead",
		filters={"source": WHATSAPP_SOURCE},
		fields=["name", "first_name", "mobile_no"],
	)
	for lead in leads:
		if not _lead_name_is_phone(lead.first_name, lead.mobile_no, lead.mobile_no or ""):
			continue

		profile_name = None
		msgs = frappe.get_all(
			"WhatsApp Message",
			filters={
				"reference_doctype": "CRM Lead",
				"reference_name": lead.name,
				"type": "Incoming",
			},
			fields=["profile_name"],
			order_by="creation desc",
			limit=20,
		)
		for msg in msgs:
			if msg.profile_name and msg.profile_name.strip():
				profile_name = msg.profile_name.strip()
				break
		if not profile_name and lead.mobile_no:
			profile_name = frappe.db.get_value(
				"WhatsApp Profiles", {"number": lead.mobile_no}, "profile_name"
			)
		if not profile_name:
			continue

		first_name, last_name = _display_name_parts(profile_name, lead.mobile_no or "")
		lead_name_full = " ".join(p for p in (first_name, last_name) if p)
		frappe.db.set_value(
			"CRM Lead",
			lead.name,
			{"first_name": first_name, "last_name": last_name, "lead_name": lead_name_full},
			update_modified=False,
		)
		updated += 1
	return updated
