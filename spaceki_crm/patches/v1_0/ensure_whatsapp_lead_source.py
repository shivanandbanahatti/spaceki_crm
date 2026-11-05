"""Ensure CRM Lead Source 'WhatsApp' exists for inbound lead capture."""

from spaceki_crm.integrations.whatsapp_lead import ensure_whatsapp_lead_source


def execute():
	ensure_whatsapp_lead_source()
