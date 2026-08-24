<template>
  <div class="flex flex-col">
    <Tabs
      v-if="hasTabs"
      v-model="tabIndex"
      as="div"
      :tabs="processedTabs"
      :class="[
        `border border-outline-gray-1 rounded-lg border-outline-gray-modals`,
        `[&_[role='tablist']::-webkit-scrollbar]:h-0 [&_[role='tab']]:shrink-0 [&_[role='tabpanel']]:overflow-visible !overflow-visible`,
      ]"
    >
      <template #tab-panel="{ tab }">
        <div class="sections my-2 sm:my-3">
          <template v-for="section in tab.sections" :key="section.name">
            <Section :section="section" :data-name="section.name" />
          </template>
        </div>
      </template>
    </Tabs>
    <div v-else class="sections px-3 py-2 sm:px-4 sm:py-3">
      <template
        v-for="section in singleTabSections"
        :key="section.name"
      >
        <Section :section="section" :data-name="section.name" />
      </template>
    </div>
  </div>
</template>

<script setup>
import Section from '@/components/FieldLayout/Section.vue'
import { useDocument } from '@/data/document'
import { Tabs } from 'frappe-ui'
import { ref, computed, provide } from 'vue'

const props = defineProps({
  tabs: { type: Array, default: () => [] },
  data: { type: Object, default: () => ({}) },
  doctype: { type: String, default: 'CRM Lead' },
  docname: { type: String, default: '' },
  isGridRow: { type: Boolean, default: false },
  preview: { type: Boolean, default: false },
  context: { type: Object, default: null },
})

const tabIndex = ref(0)

const resolvedDocname = computed(() => props.docname || props.data?.name || '')

let overrides = {}
if (props.context) {
  overrides = computed(() => props.context?.fieldPropertyOverrides || {})
} else if (!props.isGridRow) {
  const { document: doc } = useDocument(props.doctype, resolvedDocname.value)
  overrides = computed(() => doc?.fieldPropertyOverrides || {})
} else {
  overrides = computed(() => ({}))
}

const processedTabs = computed(() => {
  const ov = overrides.value
  return props.tabs
    .map((tab) => {
      const tabOverrides = ov[tab.name]
      const processedTab = tabOverrides ? { ...tab, ...tabOverrides } : tab
      return {
        ...processedTab,
        sections: processedTab.sections.map((section) => {
          const sectionOverrides = ov[section.name]
          return sectionOverrides
            ? { ...section, ...sectionOverrides }
            : section
        }),
      }
    })
    .filter((tab) => !tab.hidden)
})

const hasTabs = computed(() => processedTabs.value.length > 1)

const singleTabSections = computed(
  () => processedTabs.value[0]?.sections || [],
)

provide(
  'data',
  computed(() => props.data),
)
provide('hasTabs', hasTabs)
provide('doctype', props.doctype)
provide('docname', resolvedDocname)
provide('preview', props.preview)
provide('isGridRow', props.isGridRow)
provide('fieldLayoutContext', props.context)
</script>
<style scoped>
.section:not(:has(.field)) {
  display: none;
}

.section:has(.field):nth-child(1 of .section:has(.field)) {
  border-top: none;
  margin-top: 0;
  padding-top: 0;
}
</style>
