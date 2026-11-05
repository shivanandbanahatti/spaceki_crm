<template>
  <div class="flex h-full min-h-0 flex-col">
    <div
      v-if="document.isDirty || (isManager() && !isMobileView)"
      class="flex shrink-0 items-center justify-end gap-2 border-b border-outline-gray-2 bg-surface-white px-3 py-2 sm:px-6"
    >
      <Badge
        v-if="document.isDirty"
        :label="__('Unsaved changes')"
        theme="orange"
      />
      <Button
        v-if="isManager() && !isMobileView"
        size="sm"
        :tooltip="__('Edit Fields Layout')"
        :icon="EditIcon"
        @click="showDataFieldsModal = true"
      />
      <Button
        size="sm"
        :label="__('Save')"
        :disabled="!document.isDirty"
        variant="solid"
        :loading="document.save.loading"
        @click="saveChanges"
      />
    </div>

    <div class="min-h-0 flex-1 overflow-y-auto px-3 py-3 sm:px-6 sm:py-4">
      <div
        v-if="document.get.loading"
        class="flex min-h-32 items-center justify-center gap-2 text-sm text-ink-gray-5"
      >
        <LoadingIndicator class="h-4 w-4" />
        <span>{{ __('Loading...') }}</span>
      </div>
      <div v-else class="mx-auto grid max-w-7xl gap-3 lg:grid-cols-12">
        <div class="space-y-3 lg:col-span-12">
          <DealContactsSection
            v-if="doctype === 'CRM Deal'"
            :deal-id="docname"
            :organization="document.doc?.organization || ''"
            @organization-created="(name) => updateOrganization(name)"
          />
          <DealQuotationsSection
            v-if="doctype === 'CRM Deal'"
            :deal-id="docname"
          />
          <DealProjectSection
            v-if="doctype === 'CRM Deal'"
            :deal-id="docname"
          />
          <div class="overflow-hidden rounded-lg border border-outline-gray-2 bg-surface-white shadow-sm">
            <FieldLayout
              v-if="tabs.data"
              :tabs="tabs.data"
              :data="document.doc"
              :doctype="doctype"
            />
          </div>
        </div>
      </div>
    </div>
  </div>

  <DataFieldsModal
    v-if="showDataFieldsModal"
    v-model="showDataFieldsModal"
    :doctype="doctype"
    @reload="
      () => {
        tabs.reload()
        document.reload()
      }
    "
  />
</template>

<script setup>
import EditIcon from '@/components/Icons/EditIcon.vue'
import DataFieldsModal from '@/components/Modals/DataFieldsModal.vue'
import FieldLayout from '@/components/FieldLayout/FieldLayout.vue'
import DealContactsSection from '@/components/Record/DealContactsSection.vue'
import DealQuotationsSection from '@/components/Record/DealQuotationsSection.vue'
import DealProjectSection from '@/components/Record/DealProjectSection.vue'
import { Badge, createResource } from 'frappe-ui'
import LoadingIndicator from '@/components/Icons/LoadingIndicator.vue'
import { usersStore } from '@/stores/users'
import { useDocument } from '@/data/document'
import { isMobileView } from '@/composables/settings'
import { ref, watch, getCurrentInstance } from 'vue'

const props = defineProps({
  doctype: { type: String, required: true },
  docname: { type: String, required: true },
})

const emit = defineEmits(['beforeSave', 'afterSave'])

const { isManager } = usersStore()
const instance = getCurrentInstance()
const attrs = instance?.vnode?.props ?? {}
const showDataFieldsModal = ref(false)
const { document } = useDocument(props.doctype, props.docname)

const tabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['DataFields', props.doctype],
  params: { doctype: props.doctype, type: 'Data Fields' },
  auto: true,
})

function updateOrganization(name) {
  document.doc.organization = name
  document.save.submit()
}

function saveChanges() {
  if (!document.isDirty) return

  const updatedDoc = { ...document.doc }
  const oldDoc = { ...document.originalDoc }
  const changes = Object.keys(updatedDoc).reduce((acc, key) => {
    if (JSON.stringify(updatedDoc[key]) !== JSON.stringify(oldDoc[key])) {
      acc[key] = updatedDoc[key]
    }
    return acc
  }, {})

  if (attrs['onBeforeSave'] !== undefined) {
    emit('beforeSave', changes)
  } else {
    document.save.submit(null, {
      onSuccess: () => emit('afterSave', changes),
    })
  }
}

watch(
  () => document.doc,
  (newValue, oldValue) => {
    if (!oldValue) return
    if (newValue && oldValue) {
      const isDirty =
        JSON.stringify(newValue) !== JSON.stringify(document.originalDoc)
      document.isDirty = isDirty
      if (isDirty) {
        document.save.loading = false
      }
    }
  },
  { deep: true },
)
</script>
