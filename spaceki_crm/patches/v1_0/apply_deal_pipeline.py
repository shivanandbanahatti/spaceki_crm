import frappe

from spaceki_crm.migration.deal_pipeline import apply_deal_pipeline


def execute():
	apply_deal_pipeline()
