"""Sync WhatsApp Settings defaults and backfill WhatsApp Lead display names."""

from spaceki_crm.integrations.whatsapp_lead import (
	backfill_whatsapp_lead_names,
	sync_whatsapp_settings_defaults,
)


def execute():
	sync_whatsapp_settings_defaults()
	backfill_whatsapp_lead_names()
