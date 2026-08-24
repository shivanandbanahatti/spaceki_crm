# Spaceki CRM

Enterprise customizations for Frappe CRM — layouts, views, APIs, and UI overrides without forking FCRM core.

## Prerequisites

**Required (install fails if missing):**

- Frappe **v16 / v17**, Python **≥ 3.10**
- **crm** app installed on the site (`crm` 2.x)

**Optional (warned, install continues):**

- Node.js + Yarn and `apps/crm/frontend` (for Spaceki UI overrides build)
- ERPNext / India Compliance (optional related tabs)

## Install

```bash
cd /path/to/frappe-bench

bench get-app https://github.com/shivanandbanahatti/spaceki_crm.git
# or: ./env/bin/pip install -e apps/spaceki_crm

bench --site <your-site> install-app spaceki_crm

bench restart
bench --site <your-site> clear-cache
```

`install-app` applies:

- Deal/Lead layouts (Overview tab, side panel, pipeline)
- CRM views (Kanban default, list columns, deal title field)
- Patches in `spaceki_crm/patches.txt` (idempotent on migrate)
- Frontend sync + `yarn build` via `frontend/build.sh`

If the frontend build fails during install (e.g. no yarn), run manually:

```bash
bash apps/spaceki_crm/frontend/build.sh
bench restart && bench --site <your-site> clear-cache
```

## Upgrade

```bash
cd /path/to/frappe-bench
git -C apps/spaceki_crm pull
./env/bin/pip install -e apps/spaceki_crm
bench --site <your-site> migrate
bash apps/spaceki_crm/frontend/build.sh
bench restart && bench --site <your-site> clear-cache
```

## Frontend overrides

UI files live in `frontend/src/` and are copied into FCRM at build time by `spaceki_crm/frontend_sync.py`.

```bash
# Sync overrides → build → restore stock FCRM sources
bash apps/spaceki_crm/frontend/build.sh

# Refresh upstream snapshots after upgrading the crm app
python apps/spaceki_crm/spaceki_crm/frontend_sync.py capture
```

## Optional data migrations

Zoho CSV backfills are skipped automatically when export files are not present.

```bash
bench --site <site> execute spaceki_crm.migration.backfill_deal_links.backfill_deal_links
bench --site <site> execute spaceki_crm.migration.deal_pipeline.apply_deal_pipeline
```

## Structure

| Path | Purpose |
|------|---------|
| `spaceki_crm/hooks.py` | Install hook, doc events, API overrides |
| `spaceki_crm/customizations/` | CRM Fields Layout, views, pipeline |
| `spaceki_crm/overrides/` | `get_data`, deal forecast, view settings |
| `spaceki_crm/migration/` | Backfills and one-off scripts |
| `spaceki_crm/patches/` | Post-migrate patches (idempotent) |
| `frontend/src/` | FCRM UI overrides |
| `frontend/upstream/` | Stock FCRM snapshots for build restore |
