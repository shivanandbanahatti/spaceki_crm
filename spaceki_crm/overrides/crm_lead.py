"""CRM Lead customizations: default owner, import upsert, Import Shield sanitizers."""

import frappe

from spaceki_crm.import_shield.patch_importer import ensure_import_shield
from spaceki_crm.import_shield.sanitize import normalize_phone_digits, sanitize_crm_lead_doc

IMPORT_MERGE_FIELDS = (
	"first_name",
	"last_name",
	"middle_name",
	"salutation",
	"organization",
	"email",
	"phone",
	"mobile_no",
	"source",
	"status",
	"territory",
	"industry",
	"job_title",
	"lead_managed_by",
	"website",
	"zoho_company",
	"description",
	"city",
)


def normalize_phone(phone: str | None) -> str | None:
	return normalize_phone_digits(phone)


def find_existing_lead_by_phone(phone: str | None, mobile_no: str | None = None) -> str | None:
	norm = normalize_phone_digits(phone) or normalize_phone_digits(mobile_no)
	if not norm or len(norm) < 6:
		return None

	rows = frappe.db.sql(
		"""
		SELECT name, phone, mobile_no
		FROM `tabCRM Lead`
		WHERE (phone IS NOT NULL AND phone != '') OR (mobile_no IS NOT NULL AND mobile_no != '')
		""",
		as_dict=True,
	)
	for row in rows:
		for value in (row.phone, row.mobile_no):
			if value and normalize_phone_digits(value) == norm:
				return row.name
	return None


class SpacekiCRMLead:
	def validate(self):
		ensure_import_shield()
		sanitize_crm_lead_doc(self, for_import=bool(frappe.flags.in_import))
		self._set_default_lead_owner()
		super().validate()

	def insert(self, *args, **kwargs):
		ensure_import_shield()
		if frappe.flags.in_import and self.is_new():
			existing = find_existing_lead_by_phone(self.phone, self.mobile_no)
			if existing:
				return self._update_existing_on_import(existing)
		return super().insert(*args, **kwargs)

	def _set_default_lead_owner(self):
		if self.lead_owner:
			return

		user = frappe.session.user
		if not user or user == "Guest":
			return

		if not frappe.db.exists("User", user):
			return

		self.lead_owner = user

	def _update_existing_on_import(self, existing_name: str):
		existing = frappe.get_doc("CRM Lead", existing_name)
		sanitize_crm_lead_doc(self, for_import=True)
		changed = False

		for field in IMPORT_MERGE_FIELDS:
			if not existing.meta.has_field(field) and field not in ("lead_managed_by",):
				# still try set if attribute exists on meta
				if not hasattr(existing, field) and field not in existing.meta.get_valid_columns():
					continue
			if not existing.meta.has_field(field):
				continue
			value = self.get(field)
			if value and existing.get(field) != value:
				existing.set(field, value)
				changed = True

		if not existing.lead_owner:
			existing.lead_owner = frappe.session.user or self.owner
			changed = True

		if changed:
			existing.flags.ignore_permissions = True
			existing.save()
		elif not existing.lead_owner:
			frappe.db.set_value("CRM Lead", existing_name, "lead_owner", frappe.session.user)

		if existing.lead_owner:
			existing.assign_agent(existing.lead_owner)

		return existing
