<!-- Measurement take-off for the active line. Rows roll up into line.qty (Nos x L x B x depth)
     when qty_source = Takeoff; editing any cell re-prices. -->
<template>
  <div>
    <div class="mb-2 flex items-center">
      <span class="font-mono text-xs uppercase tracking-wide text-gray-400">Take-off</span>
      <button class="ml-auto text-sm font-medium text-blue-600" @click="add">+ Add row</button>
    </div>

    <table class="w-full text-xs">
      <thead>
        <tr class="border-b text-left font-mono uppercase text-gray-400">
          <th class="py-1">Location</th>
          <th class="w-14 text-right">Nos</th>
          <th class="w-16 text-right">L</th>
          <th class="w-16 text-right">B</th>
          <th class="w-16 text-right">Depth</th>
          <th class="w-16 text-right">Qty</th>
          <th class="w-6"></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(m, i) in rows" :key="i" class="border-b">
          <td class="py-1"><input v-model="m.description" class="w-full bg-transparent" @input="price" /></td>
          <td><input v-model.number="m.nos" type="number" class="w-full bg-transparent text-right font-mono" @input="price" /></td>
          <td><input v-model.number="m.length" type="number" class="w-full bg-transparent text-right font-mono" @input="price" /></td>
          <td><input v-model.number="m.breadth" type="number" class="w-full bg-transparent text-right font-mono" @input="price" /></td>
          <td><input v-model.number="m.depth" type="number" class="w-full bg-transparent text-right font-mono" @input="price" /></td>
          <td class="text-right font-mono text-gray-500">{{ qty(m) }}</td>
          <td class="text-center">
            <button class="text-gray-300 hover:text-red-500" @click="store.removeMeasurement(m)" aria-label="Remove row">×</button>
          </td>
        </tr>
        <tr v-if="!rows.length"><td colspan="7" class="py-3 text-center text-gray-400">No take-off rows — line qty is entered manually.</td></tr>
      </tbody>
      <tfoot v-if="rows.length">
        <tr class="font-medium">
          <td class="py-1.5" colspan="5">Total → line qty</td>
          <td class="text-right font-mono">{{ total }}</td>
          <td></td>
        </tr>
      </tfoot>
    </table>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useEstimateStore } from '../stores/estimate'

const props = defineProps({ lineId: String })
const store = useEstimateStore()

const rows = computed(() => store.lineMeasurements(props.lineId))
const qty = (m) => Number((m.nos || 1) * (m.length || 0) * (m.breadth || 1) * (m.depth || 1)).toFixed(3)
const total = computed(() => rows.value.reduce((s, m) => s + Number(qty(m)), 0).toFixed(3))

function add() {
  store.addMeasurement(props.lineId)
}
function price() {
  store.price()
}
</script>
