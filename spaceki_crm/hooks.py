app_name = "spaceki_crm"
app_title = "Spaceki CRM"
app_publisher = "shivanandbanahatti"
app_description = "Enterprise customizations for Frappe CRM"
app_email = "shivanandbanahatti@gmail.com"
app_license = "MIT"

required_apps = ["crm"]

before_install = "spaceki_crm.install.before_install"
after_install = "spaceki_crm.install.after_install"

doc_events = {
	"CRM Deal": {
		"validate": "spaceki_crm.overrides.crm_deal.sync_zoho_forecast",
	},
	"CRM View Settings": {
		"validate": "spaceki_crm.overrides.crm_view_settings.enforce_deals_kanban_default",
	},
}

override_whitelisted_methods = {
	"crm.api.doc.get_data": "spaceki_crm.overrides.doc.get_data",
}
