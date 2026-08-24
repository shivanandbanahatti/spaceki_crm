<template>
  <button
    type="button"
    class="inline-flex shrink-0 items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-all duration-200 ease-out"
    :class="tabClasses"
  >
    <component :is="tab.icon" v-if="tab.icon" class="size-3.5 shrink-0" />
    <span class="whitespace-nowrap">{{ tab.label }}</span>
  </button>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  tab: { type: Object, required: true },
})

const TAB_STYLES = {
  Activity:
    'text-ink-gray-6 hover:bg-violet-50 hover:text-violet-800 data-[state=active]:bg-violet-50 data-[state=active]:text-violet-800 data-[state=active]:shadow-sm data-[state=active]:ring-1 data-[state=active]:ring-violet-200',
  Data: 'text-ink-gray-6 hover:bg-blue-50 hover:text-blue-800 data-[state=active]:bg-blue-50 data-[state=active]:text-blue-800 data-[state=active]:shadow-sm data-[state=active]:ring-1 data-[state=active]:ring-blue-200',
  Emails:
    'text-ink-gray-6 hover:bg-rose-50 hover:text-rose-800 data-[state=active]:bg-rose-50 data-[state=active]:text-rose-800 data-[state=active]:shadow-sm data-[state=active]:ring-1 data-[state=active]:ring-rose-200',
  Comments:
    'text-ink-gray-6 hover:bg-amber-50 hover:text-amber-900 data-[state=active]:bg-amber-50 data-[state=active]:text-amber-900 data-[state=active]:shadow-sm data-[state=active]:ring-1 data-[state=active]:ring-amber-200',
  Events:
    'text-ink-gray-6 hover:bg-teal-50 hover:text-teal-800 data-[state=active]:bg-teal-50 data-[state=active]:text-teal-800 data-[state=active]:shadow-sm data-[state=active]:ring-1 data-[state=active]:ring-teal-200',
  Calls:
    'text-ink-gray-6 hover:bg-green-50 hover:text-green-800 data-[state=active]:bg-green-50 data-[state=active]:text-green-800 data-[state=active]:shadow-sm data-[state=active]:ring-1 data-[state=active]:ring-green-200',
  Tasks:
    'text-ink-gray-6 hover:bg-indigo-50 hover:text-indigo-800 data-[state=active]:bg-indigo-50 data-[state=active]:text-indigo-800 data-[state=active]:shadow-sm data-[state=active]:ring-1 data-[state=active]:ring-indigo-200',
  Work:
    'text-ink-gray-6 hover:bg-indigo-50 hover:text-indigo-800 data-[state=active]:bg-indigo-50 data-[state=active]:text-indigo-800 data-[state=active]:shadow-sm data-[state=active]:ring-1 data-[state=active]:ring-indigo-200',
  BOQ:
    'text-ink-gray-6 hover:bg-cyan-50 hover:text-cyan-800 data-[state=active]:bg-cyan-50 data-[state=active]:text-cyan-800 data-[state=active]:shadow-sm data-[state=active]:ring-1 data-[state=active]:ring-cyan-200',
  Notes:
    'text-ink-gray-6 hover:bg-yellow-50 hover:text-yellow-900 data-[state=active]:bg-yellow-50 data-[state=active]:text-yellow-900 data-[state=active]:shadow-sm data-[state=active]:ring-1 data-[state=active]:ring-yellow-200',
  Attachments:
    'text-ink-gray-6 hover:bg-slate-100 hover:text-slate-800 data-[state=active]:bg-slate-100 data-[state=active]:text-slate-800 data-[state=active]:shadow-sm data-[state=active]:ring-1 data-[state=active]:ring-slate-200',
  WhatsApp:
    'text-ink-gray-6 hover:bg-emerald-50 hover:text-emerald-800 data-[state=active]:bg-emerald-50 data-[state=active]:text-emerald-800 data-[state=active]:shadow-sm data-[state=active]:ring-1 data-[state=active]:ring-emerald-200',
  ERPNext:
    'text-ink-gray-6 hover:bg-orange-50 hover:text-orange-800 data-[state=active]:bg-orange-50 data-[state=active]:text-orange-800 data-[state=active]:shadow-sm data-[state=active]:ring-1 data-[state=active]:ring-orange-200',
}

const tabClasses = computed(() => {
  return (
    TAB_STYLES[props.tab.name] ||
    'text-ink-gray-6 hover:bg-surface-gray-2 hover:text-ink-gray-9 data-[state=active]:bg-surface-gray-2 data-[state=active]:text-ink-gray-9 data-[state=active]:shadow-sm data-[state=active]:ring-1 data-[state=active]:ring-outline-gray-2'
  )
})
</script>
