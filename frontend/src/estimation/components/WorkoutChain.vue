<!-- Read-only view of the estimate's Overhead Profile chain (the workout). -->
<template>
  <div v-if="heads.length" class="rounded-lg border bg-gray-50 p-2.5">
    <div class="mb-1.5 font-mono text-[10px] uppercase tracking-wide text-gray-400">
      Workout · {{ profile }}
    </div>
    <div class="flex flex-wrap gap-1.5">
      <span
        v-for="h in heads"
        :key="h.sequence"
        class="rounded px-1.5 py-0.5 font-mono text-[10px]"
        :class="h.head_type === 'Overhead' || h.head_type === 'Margin'
          ? 'bg-blue-50 text-blue-700' : 'bg-white text-gray-500 ring-1 ring-gray-200'"
      >
        {{ h.head_name }}<template v-if="h.head_type !== 'Labour'"> {{ h.percent }}%</template>
      </span>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { call } from 'frappe-ui'

const props = defineProps({ profile: String })
const heads = ref([])

async function load(name) {
  heads.value = []
  if (!name) return
  const doc = await call('frappe.client.get', { doctype: 'Overhead Profile', name })
  heads.value = (doc.heads || []).slice().sort((a, b) => (a.sequence || 0) - (b.sequence || 0))
}

watch(() => props.profile, load, { immediate: true })
</script>
