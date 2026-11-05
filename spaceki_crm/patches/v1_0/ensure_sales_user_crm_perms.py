from spaceki_crm.migration.sync_sales_user_perms import apply_sales_user_crm_perms


def execute():
	apply_sales_user_crm_perms(clear_cache=True)
