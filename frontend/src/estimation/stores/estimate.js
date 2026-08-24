// Pinia store: owns the working draft and the live-pricing loop for the Builder.
// The draft mirrors the Estimate DocType shape; it is priced server-side on every
// edit (previewPricing) and persisted on Save via frappe.client.insert/save.
import { defineStore } from 'pinia'
import { reactive, ref, computed } from 'vue'
import { call } from 'frappe-ui'
import { getSystemDefaults, previewPricing, applyTemplate, makeQuotation, makeRevision } from '../api/estimate'

let _uid = 0
const newLineId = () => `l${Date.now().toString(36)}${_uid++}`

// Header fields we send to the server (draft.system is UI-only and excluded).
const HEADER = [
  'project_name', 'customer', 'estimate_date', 'valid_till', 'overhead_profile',
  'price_list', 'company', 'currency', 'gst_rate', 'rounding_method',
  'aluminium_rate', 'steel_rate', 'ss_rate', 'metal_rate_basis',
]

const emptyDraft = () => ({
  project_name: '', customer: '', estimate_date: new Date().toISOString().slice(0, 10),
  system: '', scope_category: '', overhead_profile: '', price_list: '', company: '', currency: '',
  gst_rate: 18, rounding_method: 'Round to 10',
  aluminium_rate: 0, steel_rate: 0, ss_rate: 0, metal_rate_basis: '',
  lines: [], costing_lines: [], measurements: [],
})

export const useEstimateStore = defineStore('estimate', () => {
  const draft = reactive(emptyDraft())
  const pricing = ref(null)
  const activeLineId = ref(null)
  const savedName = ref(null)
  const busy = ref(false)
  const pricingPending = ref(false)
  let debounce

  const activeLine = computed(() => draft.lines.find((l) => l.line_id === activeLineId.value) || null)
  const linePricing = (id) => (pricing.value?.lines || []).find((l) => l.line_id === id) || {}
  const lineCosting = (id) => (pricing.value?.costing || []).filter((c) => c.line_id === id)
  const lineMeasurements = (id) => draft.measurements.filter((m) => m.line_id === id)

  function reset() {
    Object.assign(draft, emptyDraft())
    pricing.value = null
    activeLineId.value = null
    savedName.value = null
  }

  // ---- system picker -------------------------------------------------------
  async function chooseSystem(system) {
    const d = await getSystemDefaults(system)
    Object.assign(draft, {
      system, scope_category: d.scope_category, overhead_profile: d.overhead_profile,
      price_list: d.price_list, gst_rate: d.gst_rate, rounding_method: d.rounding_method || draft.rounding_method,
    })
    return d.templates || []
  }

  // ---- lines / take-off ----------------------------------------------------
  function addLine({ description = 'New line', uom, template } = {}) {
    const line = {
      line_id: newLineId(), line_type: 'Item', scope_category: draft.scope_category,
      description, uom: uom || 'Square Meter', qty_source: 'Manual', qty: 0, pricing_mode: 'Costed',
      width: 0, height: 0, grids_wide: 0, grids_high: 0, labour_rate: 0, labour_qty: 0,
      client_rate: 0, template: template || null,
    }
    draft.lines.push(line)
    activeLineId.value = line.line_id
    return line
  }

  function removeLine(id) {
    draft.lines = draft.lines.filter((l) => l.line_id !== id)
    draft.costing_lines = draft.costing_lines.filter((c) => c.line_id !== id)
    draft.measurements = draft.measurements.filter((m) => m.line_id !== id)
    if (activeLineId.value === id) activeLineId.value = draft.lines[0]?.line_id || null
  }

  function addMeasurement(lineId) {
    draft.measurements.push({ line_id: lineId, description: '', nos: 1, length: 0, breadth: 0, depth: 1, include_in_rollup: 1 })
    const line = draft.lines.find((l) => l.line_id === lineId)
    if (line) line.qty_source = 'Takeoff' // rollup now drives qty
  }
  function removeMeasurement(row) {
    const i = draft.measurements.indexOf(row)
    if (i > -1) draft.measurements.splice(i, 1)
  }

  // ---- live pricing --------------------------------------------------------
  function price() {
    clearTimeout(debounce)
    debounce = setTimeout(runPrice, 250)
  }
  async function runPrice() {
    pricingPending.value = true
    try {
      pricing.value = await previewPricing(toServerDoc())
      // reflect server-rolled qty (take-off) back onto the lines for display
      for (const lp of pricing.value.lines || []) {
        const l = draft.lines.find((x) => x.line_id === lp.line_id)
        if (l && l.qty_source === 'Takeoff') l.qty = lp.qty
      }
    } finally {
      pricingPending.value = false
    }
  }

  // ---- persistence ---------------------------------------------------------
  function toServerDoc() {
    const doc = { doctype: 'Estimate', naming_series: 'EST-.YYYY.-.####' }
    for (const f of HEADER) if (draft[f] !== undefined && draft[f] !== '') doc[f] = draft[f]
    doc.lines = draft.lines
    doc.costing_lines = draft.costing_lines
    doc.measurements = draft.measurements
    if (savedName.value) doc.name = savedName.value
    return doc
  }

  function hydrate(doc) {
    draft.lines = doc.lines || []
    draft.costing_lines = doc.costing_lines || []
    draft.measurements = doc.measurements || []
    for (const f of HEADER) if (doc[f] !== undefined) draft[f] = doc[f]
    if (!draft.lines.find((l) => l.line_id === activeLineId.value)) {
      activeLineId.value = draft.lines.find((l) => l.line_type === 'Item')?.line_id || null
    }
  }

  async function save() {
    busy.value = true
    try {
      const doc = savedName.value
        ? await call('frappe.client.save', { doc: toServerDoc() })
        : await call('frappe.client.insert', { doc: toServerDoc() })
      savedName.value = doc.name
      hydrate(doc)
      await runPrice()
      return doc.name
    } finally {
      busy.value = false
    }
  }

  async function loadExisting(name) {
    reset()
    const doc = await call('frappe.client.get', { doctype: 'Estimate', name })
    savedName.value = doc.name
    draft.scope_category = doc.lines?.find((l) => l.scope_category)?.scope_category || ''
    hydrate(doc)
    await runPrice()
  }

  // ---- template application (runs against a saved Estimate) ----------------
  async function applyTemplateToActive(templateName) {
    if (!savedName.value) await save()
    const idx = draft.lines.findIndex((l) => l.line_id === activeLineId.value) + 1
    if (idx < 1) return
    await applyTemplate(savedName.value, idx, templateName)
    const doc = await call('frappe.client.get', { doctype: 'Estimate', name: savedName.value })
    hydrate(doc)
    await runPrice()
  }

  async function sendForApproval() {
    if (!savedName.value) await save()
    return makeQuotation(savedName.value)
  }
  async function revise() {
    if (!savedName.value) return
    const newName = await makeRevision(savedName.value)
    await loadExisting(newName)
    return newName
  }

  return {
    draft, pricing, activeLineId, activeLine, savedName, busy, pricingPending,
    linePricing, lineCosting, lineMeasurements,
    reset, chooseSystem, addLine, removeLine, addMeasurement, removeMeasurement,
    price, runPrice, save, loadExisting, applyTemplateToActive, sendForApproval, revise,
  }
})
