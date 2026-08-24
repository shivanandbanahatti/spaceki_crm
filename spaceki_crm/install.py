import subprocess
from pathlib import Path

import frappe
from frappe import _

from spaceki_crm.customizations.custom_fields import ensure_custom_fields
from spaceki_crm.customizations.phase_a import apply_phase_a
from spaceki_crm.frontend_sync import sync_frontend
from spaceki_crm.migration.deal_pipeline import apply_deal_pipeline
from spaceki_crm.overrides.crm_view_settings import set_deals_kanban_as_default

# Frappe CRM version the frontend overrides (router.js, KanbanView.vue, …) were
# authored against. The build copies override files into the `crm` app and runs
# `yarn build`; against a different FCRM version those files may not match, so we
# skip the build (leaving stock FCRM UI intact) and warn loudly rather than
# corrupt the shared crm frontend. Bump this when the overrides are re-based.
EXPECTED_FCRM_VERSION = "2.0.0-dev"


def before_install():
	"""Fail fast when hard prerequisites are missing."""
	installed = frappe.get_installed_apps()
	if "crm" not in installed:
		frappe.throw(
			_(
				"spaceki_crm requires the Frappe CRM app (`crm`) on this site. "
				"Install crm first (Frappe v16–17 + crm 2.x), then retry. "
				"Node.js and Yarn are also needed for the optional frontend build."
			),
			title=_("Missing prerequisite: crm"),
		)

	try:
		import crm
	except Exception as exc:
		frappe.throw(
			_("Could not import the crm app: {0}").format(exc),
			title=_("Missing prerequisite: crm"),
		)

	version = getattr(crm, "__version__", "") or ""
	major = version.split(".", 1)[0]
	if major != "2":
		frappe.throw(
			_(
				"spaceki_crm requires Frappe CRM 2.x (found {0}). "
				"Upgrade or install crm >= 2.0.0, then retry."
			).format(version or "unknown"),
			title=_("Incompatible crm version"),
		)


def after_install():
	# Provision the custom fields the app depends on (esp. `deal_name`) BEFORE
	# layouts/pipeline reference them.
	ensure_custom_fields()
	apply_phase_a()
	# Patches listed in patches.txt are marked as already-run (without executing)
	# on a fresh install, so run the pipeline + kanban-default setup directly to
	# guarantee every new site comes up configured identically.
	apply_deal_pipeline()
	set_deals_kanban_as_default()
	frappe.db.commit()
	build_frontend()


def _fcrm_version():
	try:
		import crm

		return getattr(crm, "__version__", None)
	except Exception:
		return None


def build_frontend():
	"""Sync Spaceki UI overrides into FCRM and build CRM assets."""
	build_script = frappe.get_app_path("spaceki_crm", "..", "frontend", "build.sh")

	found = _fcrm_version()
	if found != EXPECTED_FCRM_VERSION:
		msg = (
			f"Spaceki CRM: Frappe CRM version mismatch (found {found!r}, expected "
			f"{EXPECTED_FCRM_VERSION!r}). Skipping frontend build to avoid breaking "
			"the shared FCRM UI. Verify the overrides match this FCRM version, then "
			f"build manually:\n  bash {build_script}\n"
			"  bench restart && bench --site <site> clear-cache"
		)
		frappe.log_error(title="Spaceki CRM frontend build skipped", message=msg)
		print(msg)
		return

	try:
		sync_frontend()
	except FileNotFoundError as exc:
		frappe.log_error(title="Spaceki CRM frontend sync failed", message=str(exc))
		print(f"Spaceki CRM: frontend sync skipped — {exc}")
		return

	crm_frontend = Path(frappe.get_app_path("crm")).parent / "frontend"
	if not (crm_frontend / "package.json").exists():
		print("Spaceki CRM: crm app frontend not found; run frontend/build.sh manually.")
		return

	try:
		subprocess.run(
			["bash", build_script],
			cwd=Path(frappe.get_app_path("spaceki_crm", "..")),
			check=True,
			timeout=600,
		)
		print("Spaceki CRM: frontend built successfully.")
	except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
		frappe.log_error(title="Spaceki CRM frontend build failed", message=str(exc))
		print(
			"Spaceki CRM: frontend build failed. After install, run:\n"
			f"  bash {build_script}\n"
			"  bench restart && bench --site <site> clear-cache"
		)


def link_frontend():
	"""Backward-compatible alias for bench execute."""
	sync_frontend()
