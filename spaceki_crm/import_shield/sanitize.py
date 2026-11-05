"""Safe Excel import sanitizers for CRM Lead (whitespace links, phones, names)."""

from __future__ import annotations

import re

import frappe
from frappe.utils import cstr, validate_email_address

# Link doctypes used on CRM Lead that we auto-resolve by whitespace + case
CRM_LEAD_LINK_DOCTYPES = frozenset(
	{
		"CRM Lead Source",
		"CRM Lead Status",
		"CRM Territory",
		"CRM Industry",
		"Salutation",
		"Gender",
		"Campaign",
		"CRM Lost Reason",
		"CRM Communication Status",
		"User",
	}
)

# Frappe Phone options allow these chars only (see PHONE_NUMBER_PATTERN)
_PHONE_ALLOWED = set("0123456789 +_-,.*#()")
_WS_RE = re.compile(r"\s+")


def normalize_whitespace(value: str | None) -> str:
	if value is None:
		return ""
	return _WS_RE.sub(" ", cstr(value)).strip()


def _link_map(doctype: str) -> dict[str, str]:
	"""Map normalized_key -> canonical name (unique keys only)."""
	local = getattr(frappe.local, "spaceki_link_maps", None)
	if local is None:
		local = {}
		frappe.local.spaceki_link_maps = local
	if doctype in local:
		return local[doctype]

	mapping: dict[str, str] = {}
	collisions: set[str] = set()
	for name in frappe.get_all(doctype, pluck="name"):
		key = normalize_whitespace(name).lower()
		if key in mapping and mapping[key] != name:
			collisions.add(key)
		else:
			mapping[key] = name
	for key in collisions:
		mapping.pop(key, None)

	local[doctype] = mapping
	return mapping


def resolve_link_value(doctype: str | None, value) -> str | None:
	"""Return canonical Link name if exact or whitespace/case-insensitive unique match."""
	if value is None or value == "":
		return value
	if not doctype or doctype not in CRM_LEAD_LINK_DOCTYPES:
		return value

	raw = cstr(value)
	normalized = normalize_whitespace(raw)
	if not normalized:
		return value

	# Prefer map (canonical casing) — MariaDB exists() is case-insensitive and would
	# otherwise return the Excel casing instead of the master name.
	match = _link_map(doctype).get(normalized.lower())
	if match:
		return match

	if frappe.db.exists(doctype, raw, cache=True):
		return frappe.db.get_value(doctype, {"name": raw}, "name") or raw

	if normalized != raw and frappe.db.exists(doctype, normalized, cache=True):
		return frappe.db.get_value(doctype, {"name": normalized}, "name") or normalized

	return value


def normalize_phone_digits(phone) -> str | None:
	"""Digits-only phone key for duplicate matching."""
	if phone is None or phone == "":
		return None
	digits = re.sub(r"\D", "", cstr(phone))
	return digits or None


def sanitize_phone(phone) -> str | None:
	"""Strip unicode/junk so Frappe Phone validation accepts common Excel pastes."""
	if phone is None or phone == "":
		return None

	s = cstr(phone).strip()
	# Drop invisible / weird unicode (e.g. ˉ U+02D9 from Excel)
	cleaned = "".join(ch for ch in s if ch in _PHONE_ALLOWED)
	cleaned = _WS_RE.sub(" ", cleaned).strip()

	if not cleaned or not any(ch.isdigit() for ch in cleaned):
		# last resort: digits only
		digits = re.sub(r"\D", "", s)
		return digits or None

	# Phone pattern max length 20
	if len(cleaned) > 20:
		digits = re.sub(r"\D", "", cleaned)
		cleaned = digits[-15:] if len(digits) > 15 else digits

	return cleaned or None


def sanitize_email(email, blank_if_invalid: bool = False) -> str | None:
	if email is None or email == "":
		return None
	email = normalize_whitespace(cstr(email))
	if not email:
		return None
	try:
		validate_email_address(email, throw=True)
		return email
	except Exception:
		if blank_if_invalid:
			return None
		return email


def ensure_lead_name_fields(doc) -> None:
	"""Avoid 'requires person's name or organization' on import when Excel left name blank."""
	if doc.get("first_name"):
		return
	if doc.get("organization") or doc.get("zoho_company") or doc.get("lead_name") or doc.get("email"):
		# set_lead_name in core can derive from org/email; first_name is required in meta
		if doc.get("lead_name"):
			doc.first_name = cstr(doc.lead_name).split()[0][:140]
		elif doc.get("zoho_company"):
			doc.first_name = cstr(doc.zoho_company)[:140]
		elif doc.get("organization"):
			doc.first_name = cstr(doc.organization)[:140]
		elif doc.get("email"):
			doc.first_name = cstr(doc.email).split("@")[0][:140]


def sync_company_fields(doc) -> None:
	"""Keep Company (zoho_company) and organization in sync when one side is filled."""
	org = normalize_whitespace(doc.get("organization")) or None
	company = normalize_whitespace(doc.get("zoho_company")) or None
	if org:
		doc.organization = org
	if company:
		doc.zoho_company = company
	if company and not org:
		# leave organization empty — UI uses zoho_company as Company
		pass
	elif org and not company and hasattr(doc, "zoho_company"):
		doc.zoho_company = org


def sanitize_crm_lead_doc(doc, for_import: bool = False) -> None:
	"""Apply safe cleanups on a CRM Lead document."""
	# Links
	for field, doctype in (
		("source", "CRM Lead Source"),
		("status", "CRM Lead Status"),
		("territory", "CRM Territory"),
		("industry", "CRM Industry"),
		("salutation", "Salutation"),
		("gender", "Gender"),
		("campaign", "Campaign"),
		("lost_reason", "CRM Lost Reason"),
		("communication_status", "CRM Communication Status"),
		("lead_owner", "User"),
	):
		if doc.get(field):
			doc.set(field, resolve_link_value(doctype, doc.get(field)))

	# Phones
	for field in ("mobile_no", "phone", "whatsapp"):
		if doc.meta.has_field(field) and doc.get(field):
			doc.set(field, sanitize_phone(doc.get(field)))

	# Email
	if doc.get("email"):
		doc.email = sanitize_email(doc.email, blank_if_invalid=for_import)

	# Text / company
	if doc.meta.has_field("zoho_company"):
		sync_company_fields(doc)
	if for_import:
		ensure_lead_name_fields(doc)

	# Trim description
	if doc.get("description"):
		doc.description = cstr(doc.description).strip()
	if doc.meta.has_field("city") and doc.get("city"):
		doc.city = normalize_whitespace(doc.city)
