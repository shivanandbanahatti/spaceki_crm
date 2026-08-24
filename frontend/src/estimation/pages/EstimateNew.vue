<!-- Step 1 — declare intent. Picking a system sets the overhead profile, sale UOM,
     scope and templates, so the Builder opens already scoped to the job. -->
<template>
  <div class="mx-auto max-w-4xl p-6">
    <h1 class="text-xl font-semibold">New estimate</h1>

    <div class="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-3">
      <FormControl label="Project" v-model="store.draft.project_name" placeholder="GR Construction — Head Office" />
      <FormControl type="link" label="Customer" doctype="Customer" v-model="store.draft.customer" />
      <FormControl type="date" label="Estimate date" v-model="store.draft.estimate_date" />
    </div>

    <p class="mt-8 text-base font-medium">What are we estimating?</p>
    <p class="text-sm text-gray-500">Pick the system — it sets the pricing defaults so you don't have to.</p>

    <div class="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
      <button
        v-for="s in systems"
        :key="s.name"
        class="rounded-lg border p-4 text-left transition hover:border-gray-900"
        :class="selected === s.name ? 'border-2 border-gray-900 bg-gray-50' : 'border-gray-200'"
        @click="choose(s.name)"
      >
        <div class="font-mono text-xs text-gray-400">{{ s.uom }}</div>
        <div class="mt-1 text-sm font-medium">{{ s.name }}</div>
        <div class="mt-1 text-xs text-gray-500">{{ s.hint }}</div>
      </button>
    </div>

    <div v-if="applied" class="mt-6 rounded-lg border border-dashed border-gray-300 bg-gray-50 p-3 text-sm">
      <span class="font-mono text-xs uppercase tracking-wide text-gray-500">Auto-applied</span>
      · Overhead profile <b>{{ store.draft.overhead_profile }}</b>
      · UOM <b>{{ applied.uom }}</b>
      · {{ applied.templates?.length || 0 }} templates
    </div>

    <div class="mt-6 flex justify-end">
      <Button variant="solid" :disabled="!selected" @click="start">Start builder</Button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Button, FormControl } from 'frappe-ui'
import { useEstimateStore } from '../stores/estimate'

const router = useRouter()
const store = useEstimateStore()
const selected = ref('')
const applied = ref(null)

// Mirrors _SYSTEM_CATALOG on the backend.
const systems = [
  { name: 'Semi-unitised', uom: 'SQM', hint: 'Open / closed groove, glass extra-over' },
  { name: 'Unitised', uom: 'SQM', hint: 'Framework + gaskets, glass extra-over' },
  { name: 'Stick', uom: 'SQM', hint: 'Mullion / transom, site-glazed' },
  { name: 'Aluminium Windows', uom: 'NOS', hint: 'Per-typology (SD, casement, vent)' },
  { name: 'Cladding', uom: 'SQM', hint: 'ACP / HPL / WPC, tender sections' },
  { name: 'Railing', uom: 'RMT', hint: 'U-channel / top-rail, per running metre' },
  { name: 'MS Fabrication', uom: 'RMT', hint: 'Grills, handrails, SS railing' },
]

async function choose(name) {
  selected.value = name
  const templates = await store.chooseSystem(name)
  applied.value = { uom: systems.find((s) => s.name === name)?.uom, templates }
}

function start() {
  router.push({ name: 'EstimateBuilder', params: { name: 'new' } })
}
</script>
