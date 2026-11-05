"""Quick self-check for Lead Import Shield (run on dev)."""

from spaceki_crm.import_shield.sanitize import (
	resolve_link_value,
	sanitize_phone,
	sanitize_email,
	normalize_whitespace,
)


def execute():
	"""bench execute spaceki_crm.import_shield.selftest.execute"""
	import frappe

	print("=== Import Shield selftest ===")

	# whitespace source
	bad = "Architects and Builders  Database"
	got = resolve_link_value("CRM Lead Source", bad)
	print(f"Source {bad!r} -> {got!r}")
	assert got == "Architects and Builders Database", got

	# case
	got2 = resolve_link_value("CRM Lead Source", "architects and builders database")
	print(f"Source lowercase -> {got2!r}")
	assert got2 == "Architects and Builders Database"

	# must NOT collapse Architect vs Architects
	a = resolve_link_value("CRM Lead Source", "Architect and Builders Database")
	print(f"Singular Architect -> {a!r}")
	assert a == "Architect and Builders Database"

	# phone unicode junk
	phone = sanitize_phone("\u02d98121414848")
	print(f"Phone unicode -> {phone!r}")
	assert phone and phone.startswith("812"), phone

	phone2 = sanitize_phone("080 2657-3635")
	print(f"Phone spaced -> {phone2!r}")
	assert "080" in phone2 or "2657" in phone2

	# bad email blanked
	em = sanitize_email("barch@hegde&hegde.com", blank_if_invalid=True)
	print(f"Bad email blanked -> {em!r}")
	assert em is None

	print("normalize:", normalize_whitespace("  a   b  "))
	print("OK")
	return "OK"
