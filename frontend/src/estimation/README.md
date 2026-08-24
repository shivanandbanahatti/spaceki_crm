# Estimate Builder (Vue)

A guided UI over the `Estimate` DocType. The engine stays on the server; this layer only
collects input and renders server-computed pricing.

## Files
- `api/estimate.js` — wrappers over the backend whitelisted methods.
- `stores/estimate.js` — Pinia store: working draft, debounced live-pricing, save/hydrate,
  load-existing, template application, revise, send-for-approval.
- `pages/EstimateList.vue` — landing list (opens a row in the Builder).
- `pages/EstimateNew.vue` — system picker (step 1).
- `pages/EstimateBuilder.vue` — 3-zone builder; deep-links `/estimate/:name`.
- `components/PricingRow.vue` — pricing panel row.
- `components/TakeoffGrid.vue` — measurement take-off (Nos×L×B×depth → line qty).
- `components/WorkoutChain.vue` — read-only view of the Overhead Profile chain.
- `routes.js` — route group to merge into the app router.

## Backend contract (already shipped in `spaceki_erp`)
- `…estimate.system_defaults(system)` → `{ scope_category, overhead_profile, uom, gst_rate, price_list, terms, templates[] }`
- `…estimate.preview_pricing(doc)` → `{ totals…, lines[], costing[] }` — **dry-run, no DB write**
- Document methods via `frappe.client.run_doc_method`: `apply_template`, `add_product_bundle`,
  `refresh_item_prices`, `make_revision`, `make_quotation`.

## Wiring (already done)
This app has **no `@spaceki` vite alias** — the stock crm `vite.config.js` only aliases
`@ → crm/frontend/src`. Overrides work by `frontend_sync.py` **copying** files into crm/src
before build, then restoring. So:
1. `frontend_sync.py` now syncs this whole `estimation/` dir into `crm/frontend/src/estimation`
   (added via `FRONTEND_DIRS`) and removes it on restore.
2. The spaceki `router.js` override registers the routes: `import { estimationRoutes } from
   '@/estimation/routes'` + `...estimationRoutes` (valid once synced, since `@ → crm/src`).
3. All files here use only **relative** (`../stores/…`) and **bare** (`frappe-ui`, `vue`,
   `pinia`) imports — no `@/` or `@spaceki` — so they resolve after the copy.
`pinia` is installed on the crm app (`app.use(pinia)` in `main.js`); `frappe-ui` provides
`call`, `createDocumentResource`, and the components used.

## Build / dev
- **Build:** `cd apps/spaceki_crm/frontend && ./build.sh` (sync → `yarn build` in crm → restore),
  then `bench restart && bench --site <site> clear-cache`.
- **Dev (hot-reload):**
  ```bash
  cd /apps/frappe-bench/apps
  sudo -u frappe python3 spaceki_crm/spaceki_crm/frontend_sync.py sync
  cd crm/frontend && yarn dev
  # when done: python3 spaceki_crm/spaceki_crm/frontend_sync.py restore
  ```
  Note: vite watches the **copy** in `crm/src/estimation`, so edits to the source here don't
  hot-reload — either edit the copy and port back, or `ln -s` the source over the copy during dev.

## Live-pricing model
Every cost-affecting edit calls `store.price()` (debounced ~250 ms) → `preview_pricing(draft)`.
The result populates `store.pricing`; the panel and per-line chips read from it. Because the
backend runs the exact `validate()` cascade on an in-memory doc, on-screen numbers equal
saved numbers to the paisa.

## Save / template flow (implemented in the store)
- `save()` → `frappe.client.insert` (new) or `frappe.client.save` (update) from `toServerDoc()`,
  keeps `savedName`, then `hydrate()` + re-price.
- `applyTemplateToActive()` → saves if needed, calls `apply_template(name, lineIdx, template)`
  (server persists the formula-driven build-up), re-fetches the doc, hydrates, re-prices.
- `loadExisting(name)` hydrates the draft from a saved Estimate for `/estimate/:name`.
- Take-off rows set `qty_source = 'Takeoff'`; the server rolls them into `line.qty`, which the
  store reflects back after each price.

## Role gating
Render the Cost build-up tab + margin only when the loaded doc exposes the permlevel-1
fields (Estimator/Approver). Sales users see Geometry/Take-off, client rate, and the quote —
not the build-up or margin. The backend already enforces this at permlevel 1; the UI just
mirrors it.

## Build next / polish
- **Verify against a running frontend** — these files are syntax-checked but not built; run
  `yarn dev` in `spaceki_crm/frontend`, exercise create → template → price → save → approve.
- **Per-project workout override** — `WorkoutChain.vue` is read-only; editable per-estimate
  overhead % needs a small backend feature (per-line `overhead_profile` or an overrides table).
- **Extra-over lines & options** (backend gaps G2/G4) — vision/spandrel/openable grouping and
  Option 1/2 alternatives, once those land server-side.
- **Print/quotation preview**, list filters/search, and role-based hiding of the Cost build-up
  tab (mirror the permlevel-1 gate the backend already enforces).
