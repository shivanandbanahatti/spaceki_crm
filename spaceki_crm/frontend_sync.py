"""Copy Spaceki CRM frontend overrides to/from FCRM (no database required)."""

import shutil
import subprocess
import sys
from pathlib import Path

FRONTEND_FILES = (
	"App.vue",
	"router.js",
	"pages/Deals.vue",
	"pages/Lead.vue",
	"pages/Deal.vue",
	"pages/MobileLead.vue",
	"pages/MobileDeal.vue",
	"components/Kanban/KanbanView.vue",
	"components/Activities/Activities.vue",
	"components/Activities/DataFields.vue",
	"components/FieldLayout/FieldLayout.vue",
	"components/FieldLayout/Section.vue",
	"components/Record/RecordHero.vue",
	"components/Record/RecordTabItem.vue",
	"components/Record/DealContactsSection.vue",
	"components/Record/DocumentNavButtons.vue",
	"composables/useRelatedCounts.js",
	"composables/useDocumentNav.js",
	"composables/recordPageTabs.js",
	"composables/useRecordTabManager.js",
)

UPSTREAM_STUB_MARKER = "Stock FCRM has no useRelatedCounts composable."
UPSTREAM_STUB_MARKERS = (
	UPSTREAM_STUB_MARKER,
	"Stock FCRM has no useDocumentNav composable.",
	"Stock FCRM has no DocumentNavButtons.",
)

# Additive Spaceki-only directories (no stock FCRM counterpart). Copied in whole
# before build and removed on restore. Imported as `@/estimation/...` once synced.
FRONTEND_DIRS = ("estimation",)


def _paths():
	bench_path = Path(__file__).resolve().parent.parent.parent.parent
	spaceki_root = bench_path / "apps" / "spaceki_crm" / "frontend"
	return {
		"spaceki_src": spaceki_root / "src",
		"upstream": spaceki_root / "upstream",
		"crm_src": bench_path / "apps" / "crm" / "frontend" / "src",
	}


def sync_frontend():
	"""Copy Spaceki CRM UI overrides into FCRM before build."""
	paths = _paths()
	for rel in FRONTEND_FILES:
		source = paths["spaceki_src"] / rel
		target = paths["crm_src"] / rel
		if not source.exists():
			raise FileNotFoundError(f"Missing Spaceki CRM frontend file: {source}")
		target.parent.mkdir(parents=True, exist_ok=True)
		if target.exists() or target.is_symlink():
			target.unlink()
		shutil.copy2(source, target)

	for rel in FRONTEND_DIRS:
		source = paths["spaceki_src"] / rel
		target = paths["crm_src"] / rel
		if not source.exists():
			raise FileNotFoundError(f"Missing Spaceki CRM frontend dir: {source}")
		if target.exists():
			shutil.rmtree(target)
		shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__", "node_modules"))


def restore_frontend():
	"""Restore stock FCRM frontend files after build."""
	paths = _paths()
	for rel in FRONTEND_FILES:
		upstream = paths["upstream"] / Path(rel).name
		target = paths["crm_src"] / rel
		if not upstream.exists():
			continue
		text = upstream.read_text(errors="ignore")
		if upstream.suffix in (".js", ".vue") and any(m in text for m in UPSTREAM_STUB_MARKERS):
			if target.exists():
				target.unlink()
			continue
		target.parent.mkdir(parents=True, exist_ok=True)
		shutil.copy2(upstream, target)

	# Additive dirs have no stock counterpart — just remove them from FCRM.
	for rel in FRONTEND_DIRS:
		target = paths["crm_src"] / rel
		if target.exists():
			shutil.rmtree(target)


def capture_upstream():
	"""Snapshot stock FCRM frontend files into upstream/ for restore after build."""
	paths = _paths()
	crm_git = paths["crm_src"].parent.parent  # apps/crm
	paths["upstream"].mkdir(parents=True, exist_ok=True)
	for rel in FRONTEND_FILES:
		target = paths["upstream"] / Path(rel).name
		try:
			result = subprocess.run(
				["git", "-C", str(crm_git), "show", f"HEAD:frontend/src/{rel}"],
				check=True,
				capture_output=True,
			)
			target.write_bytes(result.stdout)
		except subprocess.CalledProcessError:
			stock = paths["crm_src"] / rel
			if stock.exists():
				shutil.copy2(stock, target)


def main():
	command = sys.argv[1] if len(sys.argv) > 1 else ""
	if command == "sync":
		sync_frontend()
	elif command == "capture":
		capture_upstream()
	elif command == "restore":
		restore_frontend()
	else:
		print(f"Usage: {sys.argv[0]} sync|capture|restore", file=sys.stderr)
		sys.exit(1)


if __name__ == "__main__":
	main()
