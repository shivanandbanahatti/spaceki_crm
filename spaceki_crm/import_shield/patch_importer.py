"""Monkeypatch Frappe Data Import so CRM Lead Link values resolve before exact-match checks."""

from __future__ import annotations

import frappe


def apply_import_shield_patch() -> None:
	"""Idempotent patch of Data Import Row/Column for CRM Lead."""
	from frappe.core.doctype.data_import import importer as importer_mod

	if getattr(importer_mod, "_spaceki_import_shield", False):
		return

	from spaceki_crm.import_shield.sanitize import resolve_link_value, sanitize_phone

	# Per-cell Link / Phone cleanup lives on Row
	_orig_validate_value = importer_mod.Row.validate_value

	def validate_value(self, value, col):
		df = getattr(col, "df", None)
		if getattr(self, "doctype", None) == "CRM Lead" and value is not None and df is not None:
			if df.fieldtype == "Link":
				value = resolve_link_value(df.options, value)
			elif getattr(df, "options", None) == "Phone" or df.fieldname in ("mobile_no", "phone", "whatsapp"):
				value = sanitize_phone(value)
		return _orig_validate_value(self, value, col)

	importer_mod.Row.validate_value = validate_value

	# Column preview / bulk "values do not exist" check
	_orig_validate_values = importer_mod.Column.validate_values

	def validate_values(self):
		df = getattr(self, "df", None)
		if (
			getattr(self, "doctype", None) == "CRM Lead"
			and df is not None
			and df.fieldtype == "Link"
			and getattr(self, "column_values", None)
		):
			self.column_values = [
				resolve_link_value(df.options, v) if v not in (None, "") else v for v in self.column_values
			]
		return _orig_validate_values(self)

	importer_mod.Column.validate_values = validate_values
	importer_mod._spaceki_import_shield = True


def ensure_import_shield(*args, **kwargs) -> None:
	"""Safe entry for hooks / document path.

	boot_session passes bootinfo; before_job may pass job args — ignore them.
	"""
	try:
		apply_import_shield_patch()
	except Exception:
		frappe.log_error(title="Spaceki CRM Import Shield patch failed")
