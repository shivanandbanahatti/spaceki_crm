app_name = "spaceki_crm"
app_title = "Spaceki CRM"
app_publisher = "shivanandbanahatti"
app_description = "Enterprise customizations for Frappe CRM"
app_email = "shivanandbanahatti@gmail.com"
app_license = "MIT"

required_apps = ["crm"]

before_install = "spaceki_crm.install.before_install"
after_install = "spaceki_crm.install.after_install"

extend_doctype_class = {
	"CRM Lead": ["spaceki_crm.overrides.crm_lead.SpacekiCRMLead"],
}

doc_events = {
	"CRM Deal": {
		"validate": "spaceki_crm.overrides.crm_deal.sync_zoho_forecast",
	},
	"CRM View Settings": {
		"validate": "spaceki_crm.overrides.crm_view_settings.enforce_deals_kanban_default",
	},
	# Requires frappe_whatsapp (WhatsApp Message). No-op until that app is installed.
	"WhatsApp Message": {
		"after_insert": "spaceki_crm.integrations.whatsapp_lead.create_lead_from_whatsapp_message",
	},
}

override_whitelisted_methods = {
	"crm.api.doc.get_data": "spaceki_crm.overrides.doc.get_data",
}

# Lead Import Shield (Excel typo tolerance) — patch Data Import on boot / workers
boot_session = "spaceki_crm.import_shield.patch_importer.ensure_import_shield"
before_job = "spaceki_crm.import_shield.patch_importer.ensure_import_shield"
