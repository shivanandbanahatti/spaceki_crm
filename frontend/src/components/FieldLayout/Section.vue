<template>
  <div
    v-if="!section.hidden"
    class="section"
    :class="[
      section.hideBorder
        ? 'pt-2'
        : 'border-t border-outline-gray-1 mt-3 pt-3',
    ]"
  >
    <CollapsibleSection
      class="flex sm:flex-row flex-col gap-3"
      :class="{ 'px-3 sm:px-5': hasTabs }"
      :labelClass="['text-sm font-semibold', sectionLabelClass, { 'px-3 sm:px-5': hasTabs }]"
      :label="section.label"
      :hideLabel="section.hideLabel || !section.label"
      :opened="section.opened"
      :collapsible="section.collapsible"
      collapseIconPosition="right"
    >
      <template v-for="column in section.columns" :key="column.name">
        <Column
          :class="{ 'mt-3': section.label && !section.hideLabel }"
          :column="column"
          :data-name="column.name"
        />
      </template>
    </CollapsibleSection>
  </div>
</template>
<script setup>
import CollapsibleSection from '@/components/CollapsibleSection.vue'
import Column from '@/components/FieldLayout/Column.vue'
import { computed, inject } from 'vue'

const props = defineProps({
  section: { type: Object, required: true },
})

const hasTabs = inject('hasTabs')

const SECTION_ACCENTS = {
  deal_information: 'text-blue-800 before:bg-blue-500',
  lead_information: 'text-blue-800 before:bg-blue-500',
  client_project: 'text-violet-800 before:bg-violet-500',
  description_section: 'text-amber-900 before:bg-amber-500',
  follow_up_section: 'text-teal-800 before:bg-teal-500',
  organization_profile: 'text-slate-700 before:bg-slate-400',
  address_section: 'text-slate-700 before:bg-slate-400',
  products_section: 'text-orange-800 before:bg-orange-500',
}

const sectionLabelClass = computed(() => {
  const accent =
    SECTION_ACCENTS[props.section.name] ||
    'text-ink-gray-8 before:bg-surface-gray-5'
  return `before:mr-2 before:inline-block before:size-2 before:rounded-full ${accent}`
})
</script>
