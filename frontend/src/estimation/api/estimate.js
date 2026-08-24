// API layer for the Estimate Builder — thin wrappers over the backend whitelisted
// methods. All calculation stays on the server; the frontend only renders results.
import { call, createDocumentResource } from 'frappe-ui'

const M = 'spaceki_erp.spaceki_estimation.doctype.estimate.estimate'

// System picker → defaults (overhead profile, UOM, scope, templates, terms).
export function getSystemDefaults(system) {
  return call(`${M}.system_defaults`, { system })
}

// Live pricing — dry-run compute of an unsaved draft. Returns totals + per-line
// pricing + costing, writes nothing. Same code path as save, so it never drifts.
export function previewPricing(draft) {
  return call(`${M}.preview_pricing`, { doc: JSON.stringify(draft) })
}

// Templates for a scope (used by the "Add line from template" gallery).
export function listTemplates(scope) {
  return call('frappe.client.get_list', {
    doctype: 'Estimation Template',
    filters: { scope_category: scope, is_active: 1 },
    fields: ['name', 'description', 'default_uom', 'default_pricing_mode'],
    limit_page_length: 0,
  })
}

// A saved Estimate document (load / setValue / submit via frappe-ui).
export function estimateDoc(name) {
  return createDocumentResource({ doctype: 'Estimate', name, auto: true })
}

// Whitelisted document methods (run against a *saved* Estimate).
function docMethod(name, method, args = {}) {
  return call('frappe.client.run_doc_method', {
    dt: 'Estimate',
    dn: name,
    method,
    args: JSON.stringify(args),
  }).then((r) => r.message)
}

export const applyTemplate = (name, lineIdx, templateName) =>
  docMethod(name, 'apply_template', { line_idx: lineIdx, template_name: templateName })

export const addFromBundle = (name, bundle, qty = 1) =>
  docMethod(name, 'add_product_bundle', { product_bundle: bundle, qty })

export const refreshItemPrices = (name) => docMethod(name, 'refresh_item_prices')
export const makeRevision = (name) => docMethod(name, 'make_revision')
export const makeQuotation = (name) => docMethod(name, 'make_quotation')
