<!-- The Builder — three zones: BOQ lines (spine) · selected-line detail · live pricing.
     All numbers come from previewPricing(); the client never computes a rate. -->
<template>
  <div class="flex h-full flex-col">
    <!-- top bar -->
    <div class="flex flex-wrap items-center gap-3 border-b bg-gray-50 px-4 py-2.5">
      <span class="font-mono text-sm font-medium">{{ store.savedName || 'SPACEKI/BOQ/new' }}</span>
      <Badge v-if="store.draft.system" :label="store.draft.system" theme="blue" />
      <span class="text-sm text-gray-500">{{ store.draft.project_name }} · {{ store.draft.customer }}</span>
      <div class="ml-auto flex gap-2">
        <Button :loading="store.busy" @click="store.save()">Save</Button>
        <Button v-if="store.savedName" @click="store.revise()">Revise</Button>
        <Button variant="solid" @click="store.sendForApproval()">Send for approval</Button>
      </div>
    </div>

    <div class="grid flex-1 grid-cols-1 lg:grid-cols-[1.05fr_1.5fr_1fr]">
      <!-- LEFT — BOQ lines -->
      <section class="border-r p-3">
        <div class="mb-2 flex items-center">
          <span class="font-mono text-xs uppercase tracking-wide text-gray-400">BOQ lines</span>
          <button class="ml-auto text-sm font-medium text-blue-600" @click="store.addLine()">+ Add line</button>
        </div>
        <button
          v-for="(l, i) in store.draft.lines"
          :key="l.line_id"
          class="mb-2 w-full rounded-lg border p-2.5 text-left"
          :class="l.line_id === store.activeLineId ? 'border-gray-900 bg-gray-50' : 'border-gray-200'"
          @click="store.activeLineId = l.line_id"
        >
          <div class="flex items-baseline gap-2">
            <span class="font-mono text-xs text-gray-400">{{ i + 1 }}</span>
            <span class="flex-1 truncate text-sm font-medium">{{ l.description }}</span>
          </div>
          <div class="mt-1 flex gap-2 font-mono text-xs text-gray-500">
            <span>{{ l.qty }} {{ l.uom }}</span>
            <span>· ₹{{ fmt(store.linePricing(l.line_id).client_rate) }}</span>
            <span class="ml-auto font-medium text-gray-900">₹{{ fmt(store.linePricing(l.line_id).amount) }}</span>
          </div>
        </button>
      </section>

      <!-- MIDDLE — line detail -->
      <section class="border-r p-3">
        <div v-if="!store.activeLine" class="p-8 text-center text-sm text-gray-400">Select or add a BOQ line.</div>
        <template v-else>
          <div class="mb-3 flex items-center gap-2">
            <span class="flex-1 font-mono text-xs uppercase tracking-wide text-gray-400">
              Line · {{ store.activeLine.description }}
            </span>
            <button class="text-gray-300 hover:text-red-500" @click="store.removeLine(store.activeLine.line_id)">Remove</button>
          </div>

          <TabButtons v-model="tab" :buttons="['Geometry & Take-off', 'Cost build-up', 'Pricing']" class="mb-4" />

          <!-- Geometry & take-off -->
          <div v-show="tab === 0">
            <FormControl label="Description" v-model="store.activeLine.description" class="mb-3" />
            <div class="grid grid-cols-2 gap-3">
              <FormControl label="Width (m)" type="number" v-model.number="store.activeLine.width" @input="store.price()" />
              <FormControl label="Height (m)" type="number" v-model.number="store.activeLine.height" @input="store.price()" />
              <FormControl label="Grids wide" type="number" v-model.number="store.activeLine.grids_wide" @input="store.price()" />
              <FormControl label="Grids high" type="number" v-model.number="store.activeLine.grids_high" @input="store.price()" />
              <FormControl label="Labour rate / uom" type="number" v-model.number="store.activeLine.labour_rate" @input="store.price()" />
              <FormControl label="Total qty" type="number" v-model.number="store.activeLine.qty"
                           :disabled="store.activeLine.qty_source === 'Takeoff'" @input="store.price()" />
            </div>
            <div class="mt-4 border-t pt-3">
              <TakeoffGrid :line-id="store.activeLine.line_id" />
            </div>
          </div>

          <!-- Cost build-up -->
          <div v-show="tab === 1">
            <div class="mb-2">
              <Autocomplete :options="templateOptions" placeholder="Add from template…" @update:modelValue="applyTemplate" />
              <p class="mt-1 text-xs text-gray-400">Applying a template saves the estimate and loads the formula-driven build-up.</p>
            </div>
            <table class="w-full text-xs">
              <thead>
                <tr class="border-b text-left font-mono uppercase text-gray-400">
                  <th class="py-1">Component</th><th class="text-right">Qty</th><th class="text-right">Rate</th><th class="text-right">Amount</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="c in store.lineCosting(store.activeLine.line_id)" :key="c.component_name" class="border-b">
                  <td class="py-1.5">{{ c.component_name }}</td>
                  <td class="text-right font-mono">{{ fmt(c.total_qty) }}</td>
                  <td class="text-right font-mono">{{ fmt(c.rate) }}</td>
                  <td class="text-right font-mono">{{ fmt(c.amount) }}</td>
                </tr>
                <tr v-if="!store.lineCosting(store.activeLine.line_id).length">
                  <td colspan="4" class="py-3 text-center text-gray-400">No components — add from a template.</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Pricing -->
          <div v-show="tab === 2" class="space-y-2">
            <Row label="Derived rate" :value="store.linePricing(store.activeLine.line_id).derived_rate" />
            <FormControl label="Client rate" type="number" v-model.number="store.activeLine.client_rate" @input="store.price()" />
            <Row label="Margin %" :value="store.linePricing(store.activeLine.line_id).margin_percent" pct />
          </div>
        </template>
      </section>

      <!-- RIGHT — pricing -->
      <section class="p-3">
        <div class="mb-3 flex items-center gap-2">
          <span class="font-mono text-xs uppercase tracking-wide text-gray-400">Pricing · estimate</span>
          <LoadingIndicator v-if="store.pricingPending" class="h-3 w-3" />
        </div>
        <Row label="Fabrication cost" :value="p.total_fabrication_cost" />
        <WorkoutChain :profile="store.draft.overhead_profile" class="my-2" />
        <Row label="Derived total" :value="p.total_derived_amount" />
        <Row label="Client total" :value="p.total_client_amount" />
        <div class="my-3 flex items-center justify-between rounded-lg border border-green-200 bg-green-50 px-3 py-2.5">
          <span class="font-mono text-xs uppercase tracking-wide text-green-700">Blended margin</span>
          <span class="text-lg font-semibold text-green-700">{{ fmt(p.blended_margin_percent) }}%</span>
        </div>
        <Row label="GST" :value="p.total_gst_amount" />
        <Row label="Grand total" :value="p.grand_total" big />
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Button, Badge, FormControl, TabButtons, Autocomplete, LoadingIndicator } from 'frappe-ui'
import { useEstimateStore } from '../stores/estimate'
import { listTemplates } from '../api/estimate'
import Row from '../components/PricingRow.vue'
import TakeoffGrid from '../components/TakeoffGrid.vue'
import WorkoutChain from '../components/WorkoutChain.vue'

const props = defineProps({ name: { type: String, default: 'new' } })
const store = useEstimateStore()
const tab = ref(0)
const templates = ref([])

const p = computed(() => store.pricing || {})
const templateOptions = computed(() => templates.value.map((t) => ({ label: t.name, value: t.name })))
const fmt = (n) => Number(n || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 })

async function applyTemplate(opt) {
  if (opt?.value) await store.applyTemplateToActive(opt.value)
}

onMounted(async () => {
  // Deep-link to an existing estimate; otherwise continue the draft from the picker.
  if (props.name && props.name !== 'new' && store.savedName !== props.name) {
    await store.loadExisting(props.name)
  } else if (!store.draft.lines.length) {
    store.addLine()
  }
  if (store.draft.scope_category) templates.value = (await listTemplates(store.draft.scope_category)) || []
  store.price()
})
</script>
