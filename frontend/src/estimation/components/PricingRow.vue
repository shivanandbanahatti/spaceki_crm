<!-- Small label/value row for the pricing panel. -->
<template>
  <div class="flex items-baseline justify-between border-b border-dashed border-gray-200 py-2 last:border-0"
       :class="big ? 'pt-3' : ''">
    <span class="text-sm" :class="big ? 'font-medium text-gray-900' : 'text-gray-500'">{{ label }}</span>
    <span class="font-mono tabular-nums" :class="big ? 'text-base font-semibold' : 'text-sm font-medium'">
      <template v-if="pct">{{ num }}%</template>
      <template v-else>₹{{ num }}</template>
    </span>
  </div>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({
  label: String,
  value: [Number, String],
  pct: Boolean,
  big: Boolean,
})
const num = computed(() =>
  Number(props.value || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 }),
)
</script>
