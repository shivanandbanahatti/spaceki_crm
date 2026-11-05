"""Sync Sales User Custom DocPerms from a source site snapshot onto current site.

Also ensures durable CRM import permissions for Sales User.
"""

from __future__ import annotations

import frappe

# Permissions Sales Users need for Frappe CRM day-to-day (esp. Excel import).
# Kept in code so prod/dev don't drift again.
SALES_USER_CUSTOM_PERMS = [
	{
		"parent": "Data Import",
		"read": 1,
		"write": 1,
		"create": 1,
		"delete": 0,
		"import": 1,
		"export": 1,
		"share": 0,
		"print": 0,
		"email": 0,
		"report": 0,
		"select": 0,
	},
	{
		"parent": "CRM Lead",
		"read": 1,
		"write": 1,
		"create": 1,
		"delete": 1,
		"import": 1,
		"export": 1,
		"share": 1,
		"print": 1,
		"email": 1,
		"report": 1,
		"select": 0,
	},
	{
		"parent": "Contact",
		"read": 1,
		"write": 1,
		"create": 1,
		"delete": 0,
		"import": 0,
		"export": 0,
		"share": 0,
		"print": 0,
		"email": 0,
		"report": 0,
		"select": 0,
	},
]


def _ensure_custom_docperm(parent: str, role: str = "Sales User", **rights):
	right_keys = (
		"read",
		"write",
		"create",
		"delete",
		"submit",
		"cancel",
		"amend",
		"report",
		"export",
		"import",
		"share",
		"print",
		"email",
		"select",
		"if_owner",
	)
	existing = frappe.db.exists("Custom DocPerm", {"parent": parent, "role": role, "permlevel": 0})

	if existing:
		doc = frappe.get_doc("Custom DocPerm", existing)
		changed = False
		for key in right_keys:
			value = rights.get(key, 0)
			if doc.get(key) != value:
				doc.set(key, value)
				changed = True
		if changed:
			doc.save(ignore_permissions=True)
			print(f"  updated Custom DocPerm: {parent} / {role}")
		else:
			print(f"  ok (unchanged): {parent} / {role}")
		return

	doc = frappe.get_doc(
		{
			"doctype": "Custom DocPerm",
			"parent": parent,
			"role": role,
			"permlevel": 0,
			**{k: rights.get(k, 0) for k in right_keys},
		}
	)
	doc.insert(ignore_permissions=True)
	print(f"  created Custom DocPerm: {parent} / {role}")


def apply_sales_user_crm_perms(clear_cache: bool = True):
	"""bench execute spaceki_crm.migration.sync_sales_user_perms.apply_sales_user_crm_perms"""
	print("Applying Sales User CRM Custom DocPerms...")
	for row in SALES_USER_CUSTOM_PERMS:
		parent = row["parent"]
		rights = {k: v for k, v in row.items() if k != "parent"}
		_ensure_custom_docperm(parent, **rights)

	frappe.db.commit()
	if clear_cache:
		frappe.clear_cache()
	print("Done.")


def verify_user(user: str = "upagna@nrgroupindia.com"):
	"""bench execute spaceki_crm.migration.sync_sales_user_perms.verify_user"""
	if not frappe.db.exists("User", user):
		print(f"User missing: {user}")
		return

	frappe.set_user(user)
	checks = ["Data Import", "CRM Lead", "CRM Lead Source", "Contact", "File"]
	print(f"Permissions for {user}:")
	for dt in checks:
		print(
			f"  {dt}: read={frappe.has_permission(dt, 'read')} "
			f"create={frappe.has_permission(dt, 'create')} "
			f"import={frappe.has_permission(dt, 'import')}"
		)
	frappe.set_user("Administrator")


def execute():
	apply_sales_user_crm_perms()
	verify_user()
