#!/usr/bin/env bash
set -euo pipefail

# CRM frontend files are owned by the frappe user; re-exec when needed.
if [ "$(id -un)" != "frappe" ]; then
	exec sudo -u frappe "$0" "$@"
fi

BENCH_PATH="$(cd "$(dirname "$0")/../../.." && pwd)"
PYTHON="${BENCH_PATH}/env/bin/python"
SYNC="${BENCH_PATH}/apps/spaceki_crm/spaceki_crm/frontend_sync.py"

echo "Syncing Spaceki CRM frontend overrides into FCRM..."
"$PYTHON" "$SYNC" sync

cd "$BENCH_PATH/apps/crm/frontend"
echo "Building FCRM frontend..."
yarn build

echo "Restoring stock FCRM frontend files..."
"$PYTHON" "$SYNC" restore

echo "Done. Run: bench restart && bench --site ${SITE:-erp.spaceki.com} clear-cache"
