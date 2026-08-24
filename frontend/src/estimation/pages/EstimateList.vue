<!-- Estimate list — landing page. Opens a row in the Builder; New starts the picker. -->
<template>
  <div class="mx-auto max-w-5xl p-6">
    <div class="flex items-center">
      <h1 class="text-xl font-semibold">Estimates</h1>
      <Button variant="solid" class="ml-auto" @click="$router.push({ name: 'EstimateNew' })">New estimate</Button>
    </div>

    <div class="mt-5 overflow-hidden rounded-lg border">
      <table class="w-full text-sm">
        <thead class="bg-gray-50 text-left font-mono text-xs uppercase tracking-wide text-gray-400">
          <tr>
            <th class="px-3 py-2">Ref</th>
            <th class="px-3 py-2">Project</th>
            <th class="px-3 py-2">Customer</th>
            <th class="px-3 py-2">Status</th>
            <th class="px-3 py-2 text-right">Grand total</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="e in rows"
            :key="e.name"
            class="cursor-pointer border-t hover:bg-gray-50"
            @click="$router.push({ name: 'EstimateBuilder', params: { name: e.name } })"
          >
            <td class="px-3 py-2 font-mono text-xs">{{ e.name }}</td>
            <td class="px-3 py-2">{{ e.project_name }}</td>
            <td class="px-3 py-2 text-gray-500">{{ e.customer }}</td>
            <td class="px-3 py-2"><Badge :label="e.workflow_state || 'Draft'" :theme="theme(e.workflow_state)" /></td>
            <td class="px-3 py-2 text-right font-mono tabular-nums">₹{{ fmt(e.grand_total) }}</td>
          </tr>
          <tr v-if="!rows.length"><td colspan="5" class="px-3 py-8 text-center text-gray-400">No estimates yet.</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Button, Badge, call } from 'frappe-ui'

const rows = ref([])
const fmt = (n) => Number(n || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })
const theme = (s) => (s === 'Approved' || s === 'Quotation Created' ? 'green' : s === 'Superseded' ? 'gray' : 'blue')

onMounted(async () => {
  rows.value = await call('frappe.client.get_list', {
    doctype: 'Estimate',
    fields: ['name', 'project_name', 'customer', 'workflow_state', 'grand_total'],
    order_by: 'modified desc',
    limit_page_length: 50,
  })
})
</script>
