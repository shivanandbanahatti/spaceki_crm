# Copyright (c) 2026, Spaceki and contributors
# For license information, please see license.txt

from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from spaceki_crm.integrations.whatsapp_lead import (
	WHATSAPP_SOURCE,
	_create_whatsapp_lead,
	create_lead_from_whatsapp_message,
	ensure_whatsapp_lead_source,
)


class TestWhatsAppLeadCapture(FrappeTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def test_ensure_whatsapp_lead_source_creates_once(self):
		ensure_whatsapp_lead_source()
		self.assertTrue(frappe.db.exists("CRM Lead Source", WHATSAPP_SOURCE))
		ensure_whatsapp_lead_source()
		self.assertEqual(
			frappe.db.count("CRM Lead Source", {"name": WHATSAPP_SOURCE}),
			1,
		)

	def test_skips_outgoing_messages(self):
		doc = MagicMock()
		doc.type = "Outgoing"
		doc.get = lambda k, d=None: getattr(doc, k, d)
		with patch(
			"spaceki_crm.integrations.whatsapp_lead.get_contact_lead_or_deal_from_number"
		) as lookup:
			create_lead_from_whatsapp_message(doc)
		lookup.assert_not_called()

	def test_skips_when_already_linked(self):
		doc = MagicMock()
		doc.type = "Incoming"
		doc.reference_doctype = "CRM Lead"
		doc.reference_name = "CRM-LEAD-0001"
		doc.profile_name = None
		doc.get = lambda k, d=None: getattr(doc, k, d)
		with patch(
			"spaceki_crm.integrations.whatsapp_lead.get_contact_lead_or_deal_from_number"
		) as lookup:
			create_lead_from_whatsapp_message(doc)
		lookup.assert_not_called()

	def test_creates_lead_for_unknown_number_uses_phone_as_fallback(self):
		doc = MagicMock()
		doc.name = "WA-MSG-TEST"
		doc.type = "Incoming"
		doc.reference_doctype = None
		doc.reference_name = None
		doc.profile_name = None
		doc.get = lambda k, d=None: {
			"from": "+919876543210",
			"type": "Incoming",
			"profile_name": None,
		}.get(k, d)

		with (
			patch(
				"spaceki_crm.integrations.whatsapp_lead.get_contact_lead_or_deal_from_number",
				return_value=(None, None),
			),
			patch("frappe.db.set_value") as set_value,
		):
			create_lead_from_whatsapp_message(doc)

		lead = frappe.get_all(
			"CRM Lead",
			filters={"mobile_no": "+919876543210", "source": WHATSAPP_SOURCE},
			fields=["name", "first_name"],
			limit=1,
		)
		self.assertEqual(len(lead), 1)
		self.assertEqual(lead[0].first_name, "+919876543210")
		set_value.assert_called_once()
		args = set_value.call_args
		self.assertEqual(args[0][0], "WhatsApp Message")
		self.assertEqual(args[0][1], "WA-MSG-TEST")
		self.assertEqual(args[0][2]["reference_doctype"], "CRM Lead")
		self.assertEqual(args[0][2]["reference_name"], lead[0].name)

	def test_creates_lead_with_whatsapp_profile_name(self):
		lead_name = _create_whatsapp_lead("919900112233", "Manikanta Dm")
		lead = frappe.get_doc("CRM Lead", lead_name)
		self.assertEqual(lead.first_name, "Manikanta")
		self.assertEqual(lead.last_name, "Dm")
		self.assertEqual(lead.mobile_no, "919900112233")
		self.assertEqual(lead.source, WHATSAPP_SOURCE)
		self.assertIn("Manikanta", lead.lead_name)

	def test_links_existing_match_without_new_lead(self):
		doc = MagicMock()
		doc.name = "WA-MSG-EXISTING"
		doc.type = "Incoming"
		doc.reference_doctype = None
		doc.reference_name = None
		doc.profile_name = None
		doc.get = lambda k, d=None: {
			"from": "+911111111111",
			"type": "Incoming",
			"profile_name": None,
		}.get(k, d)

		before = frappe.db.count("CRM Lead")
		with (
			patch(
				"spaceki_crm.integrations.whatsapp_lead.get_contact_lead_or_deal_from_number",
				return_value=("CRM-LEAD-EXIST", "CRM Lead"),
			),
			patch("frappe.db.set_value") as set_value,
			patch(
				"spaceki_crm.integrations.whatsapp_lead._upgrade_lead_name_from_profile"
			) as upgrade,
		):
			create_lead_from_whatsapp_message(doc)

		self.assertEqual(frappe.db.count("CRM Lead"), before)
		set_value.assert_called_once_with(
			"WhatsApp Message",
			"WA-MSG-EXISTING",
			{"reference_doctype": "CRM Lead", "reference_name": "CRM-LEAD-EXIST"},
			update_modified=False,
		)
		upgrade.assert_not_called()
