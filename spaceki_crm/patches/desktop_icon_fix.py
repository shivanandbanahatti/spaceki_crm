"""Avoid duplicate Desktop Icon errors during app install (e.g. India Compliance)."""


def apply():
	import frappe
	from frappe.desk.doctype.desktop_icon import desktop_icon as module

	if getattr(module.create_desktop_icons_from_installed_apps, "_spaceki_patched", False):
		return

	def create_desktop_icons_from_installed_apps():
		apps = frappe.get_installed_apps()
		index = 0
		for app in apps:
			app_title = frappe.get_hooks("app_title", app_name=app)[0]
			app_details = frappe.get_hooks("add_to_apps_screen", app_name=app)
			if not app_details:
				continue

			# India Compliance ships a Folder icon with the same label as the App icon.
			if frappe.db.exists("Desktop Icon", app_title):
				continue
			if frappe.db.exists("Desktop Icon", {"icon_type": "App", "app": app}):
				continue

			icon = frappe.new_doc("Desktop Icon")
			icon.label = app_title
			icon.link_type = "External"
			icon.idx = index
			icon.icon_type = "App"
			icon.app = app
			icon.link = app_details[0]["route"]
			icon.logo_url = app_details[0]["logo"]
			icon.insert(ignore_if_duplicate=True)
			index += 1

	create_desktop_icons_from_installed_apps._spaceki_patched = True
	module.create_desktop_icons_from_installed_apps = create_desktop_icons_from_installed_apps


apply()
