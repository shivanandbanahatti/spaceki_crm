<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs">
        <template #prefix="{ item }">
          <Icon v-if="item.icon" :icon="item.icon" class="mr-2 h-4" />
        </template>
      </Breadcrumbs>
      <DocumentNavButtons
        v-if="leadId"
        doctype="CRM Lead"
        :docname="leadId"
        route-name="Lead"
        param-key="leadId"
      />
    </template>
    <template v-if="!errorTitle" #right-header>
      <CustomActions
        v-if="document._actions?.length"
        :actions="document._actions"
      />
      <CustomActions
        v-if="document.actions?.length"
        :actions="document.actions"
      />
      <AssignTo v-model="assignees.data" doctype="CRM Lead" :docname="leadId" />
      <Dropdown
        v-if="doc && document.statuses"
        :options="statuses"
        placement="right"
      >
        <template #default="{ open }">
          <Button
            v-if="doc.status"
            :label="statusLabel(doc.status)"
            :iconRight="open ? 'chevron-up' : 'chevron-down'"
          >
            <template #prefix>
              <IndicatorIcon :class="getLeadStatus(doc.status).color" />
            </template>
          </Button>
        </template>
      </Dropdown>
      <Button
        :label="__('Convert to Deal')"
        variant="solid"
        @click="showConvertToDealModal = true"
      />
    </template>
  </LayoutHeader>
  <div
    v-if="doc.name"
    class="flex h-full flex-col overflow-hidden bg-surface-gray-1"
  >
    <RecordHero
      :title="title"
      :subtitle="leadId"
      :label="title"
      :status-label="doc.status ? statusLabel(doc.status) : ''"
      :status-theme="leadStatusTheme"
      @copy-subtitle="copyToClipboard(leadId)"
    >
      <template #avatar>
        <FileUploader
          :validateFile="validateIsImageFile"
          @success="(file) => updateField('image', file.file_url)"
        >
          <template #default="{ openFileSelector }">
            <div class="group relative">
              <Avatar
                size="3xl"
                class="size-14 shadow-sm ring-2 ring-outline-gray-2"
                :label="title"
                :image="doc.image"
              />
              <button
                type="button"
                class="absolute inset-0 flex items-end justify-center rounded-full bg-black/0 pb-2 opacity-0 transition group-hover:bg-black/35 group-hover:opacity-100"
                @click="openFileSelector()"
              >
                <CameraIcon class="size-4 text-white" />
              </button>
            </div>
          </template>
        </FileUploader>
      </template>
      <template #actions>
        <Button
          v-if="callEnabled"
          :tooltip="__('Make a Call')"
          :icon="PhoneIcon"
          @click="
            () =>
              doc.mobile_no
                ? makeCall(doc.mobile_no)
                : toast.error(__('Please set a mobile number to make calls'))
          "
        />
        <Button
          :tooltip="__('Send an Email')"
          :icon="Email2Icon"
          @click="
            doc.email
              ? openEmailBox()
              : toast.error(__('Please set an email address to send emails'))
          "
        />
        <Button
          :tooltip="__('Go to Website')"
          :icon="LinkIcon"
          @click="
            doc.website
              ? openWebsite(doc.website)
              : toast.error(__('Please set a website to visit'))
          "
        />
        <Button
          :tooltip="__('Attach a File')"
          :icon="AttachmentIcon"
          @click="showFilesUploader = true"
        />
        <Button
          v-if="canDelete"
          :tooltip="__('Delete')"
          variant="subtle"
          theme="red"
          icon="trash-2"
          @click="deleteLead"
        />
      </template>
      <template #below>
        <SLASection
          v-if="doc.sla_status"
          v-model="doc"
          class="mt-2"
          @updateField="updateField"
        />
        <ErrorMessage v-if="error" class="mt-2" :message="__(error)" />
      </template>
    </RecordHero>
    <Tabs
      v-model="tabIndex"
      :tabs="tabs"
      :class="RECORD_TAB_LIST_CLASSES"
    >
      <template #tab-item="{ tab }">
        <RecordTabItem :tab="tab" />
      </template>
      <template #tab-panel>
        <DealBOQPanel
          v-if="tabs[tabIndex] && tabs[tabIndex].name === 'BOQ'"
          parent-doctype="CRM Lead"
          :parent-id="leadId"
          @updated="counts.reload()"
        />
        <Activities
          v-else
          ref="activities"
          v-model:reload="reload"
          v-model:tabIndex="tabIndex"
          doctype="CRM Lead"
          :docname="leadId"
          :tabs="tabs"
          @beforeSave="beforeStatusChange"
          @afterSave="reloadResources"
        />
      </template>
    </Tabs>
  </div>
  <ErrorPage
    v-else-if="errorTitle"
    :errorTitle="errorTitle"
    :errorMessage="errorMessage"
  />
  <ConvertToDealModal
    v-if="showConvertToDealModal"
    v-model="showConvertToDealModal"
    :lead="doc"
  />
  <FilesUploader
    v-model="showFilesUploader"
    doctype="CRM Lead"
    :docname="leadId"
    @after="
      () => {
        activities?.all_activities?.reload()
        changeTabTo('attachments')
      }
    "
  />
  <DeleteLinkedDocModal
    v-if="showDeleteLinkedDocModal"
    v-model="showDeleteLinkedDocModal"
    :doctype="'CRM Lead'"
    :docname="leadId"
    name="Leads"
  />
  <LostReasonModal
    v-if="showLostReasonModal"
    v-model="showLostReasonModal"
    doctype="CRM Lead"
    :document="document"
  />
</template>
<script setup>
import DeleteLinkedDocModal from '@/components/DeleteLinkedDocModal.vue'
import ErrorPage from '@/components/ErrorPage.vue'
import Icon from '@/components/Icon.vue'
import ActivityIcon from '@/components/Icons/ActivityIcon.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import DetailsIcon from '@/components/Icons/DetailsIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import CameraIcon from '@/components/Icons/CameraIcon.vue'
import LinkIcon from '@/components/Icons/LinkIcon.vue'
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'
import DealBOQPanel from '@/estimation/DealBOQPanel.vue'
import DocumentNavButtons from '@/components/Record/DocumentNavButtons.vue'
import LostReasonModal from '@/components/Modals/LostReasonModal.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import RecordHero from '@/components/Record/RecordHero.vue'
import RecordTabItem from '@/components/Record/RecordTabItem.vue'
import { RECORD_TAB_LIST_CLASSES } from '@/composables/recordPageTabs'
import Activities from '@/components/Activities/Activities.vue'
import AssignTo from '@/components/AssignTo.vue'
import FilesUploader from '@/components/FilesUploader/FilesUploader.vue'
import SLASection from '@/components/SLASection.vue'
import CustomActions from '@/components/CustomActions.vue'
import ConvertToDealModal from '@/components/Modals/ConvertToDealModal.vue'
import {
  openWebsite,
  setupCustomizations,
  copyToClipboard,
  validateIsImageFile,
  isTranslatable,
} from '@/utils'
import { getView } from '@/utils/view'
import { getSettings } from '@/stores/settings'
import { globalStore } from '@/stores/global'
import { statusesStore } from '@/stores/statuses'
import { getMeta } from '@/stores/meta'
import { useDocument } from '@/data/document'
import { whatsappEnabled } from '@/composables/whatsapp'
import { callEnabled } from '@/composables/telephony'
import {
  FileUploader,
  Dropdown,
  Tooltip,
  Avatar,
  Tabs,
  Breadcrumbs,
  call,
  usePageMeta,
  toast,
  ErrorMessage,
} from 'frappe-ui'
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useRecordTabManager } from '@/composables/useRecordTabManager'
import { useRelatedCounts } from '@/composables/useRelatedCounts'

const { brand } = getSettings()
const { $dialog, $socket, makeCall } = globalStore()
const { statusOptions, getLeadStatus } = statusesStore()
const { doctypeMeta } = getMeta('CRM Lead')

const route = useRoute()
const router = useRouter()

const props = defineProps({
  leadId: { type: String, required: true },
})

const { counts, countLabel } = useRelatedCounts('CRM Lead', () => props.leadId)

const reload = ref(false)
const activities = ref(null)
const errorTitle = ref('')
const errorMessage = ref('')
const showDeleteLinkedDocModal = ref(false)
const showConvertToDealModal = ref(false)
const showFilesUploader = ref(false)

const {
  triggerOnChange,
  triggerOnRender,
  assignees,
  permissions,
  document,
  scripts,
  error,
} = useDocument('CRM Lead', props.leadId)

const canDelete = computed(() => permissions.data?.permissions?.delete || false)

const doc = computed(() => document.doc || {})

onMounted(async () => {
  if (document.doc) await triggerOnRender()
})

watch(error, (err) => {
  if (err) {
    errorTitle.value = __(
      err.exc_type == 'DoesNotExistError'
        ? 'Document not found'
        : 'Error occurred',
    )
    errorMessage.value = __(err.messages?.[0] || 'An error occurred')
  } else {
    errorTitle.value = ''
    errorMessage.value = ''
  }
})

watch(
  () => document.doc,
  async (_doc) => {
    if (scripts.data?.length) {
      let s = await setupCustomizations(scripts.data, {
        doc: _doc,
        $dialog,
        $socket,
        router,
        toast,
        updateField,
        createToast: toast.create,
        deleteDoc: deleteLead,
        call,
      })
      document._actions = s.actions || []
      document._statuses = s.statuses || []
    }
  },
  { once: true },
)

const breadcrumbs = computed(() => {
  let items = [{ label: __('Leads'), route: { name: 'Leads' } }]

  if (route.query.view || route.query.viewType) {
    let view = getView(route.query.view, route.query.viewType, 'CRM Lead')
    if (view) {
      items.push({
        label: __(view.label),
        icon: view.icon,
        route: {
          name: 'Leads',
          params: { viewType: route.query.viewType },
          query: { view: route.query.view },
        },
      })
    }
  }

  items.push({
    label: title.value,
    route: { name: 'Lead', params: { leadId: props.leadId } },
  })
  return items
})

const title = computed(() => {
  return (
    doc.value?.lead_name ||
    doc.value?.[doctypeMeta.value?.title_field || 'name'] ||
    props.leadId
  )
})

const statuses = computed(() => {
  let customStatuses = document.statuses?.length
    ? document.statuses
    : document._statuses || []
  return statusOptions('lead', customStatuses, triggerStatusChange)
})

usePageMeta(() => {
  return { title: title.value, icon: brand.favicon }
})

const tabs = computed(() => {
  let tabOptions = [
    {
      name: 'Data',
      label: __('Overview'),
      icon: DetailsIcon,
    },
    {
      name: 'BOQ',
      label: countLabel('BOQ', 'boq'),
      icon: DetailsIcon,
    },
    {
      name: 'Attachments',
      label: countLabel('Attachments', 'attachments'),
      icon: AttachmentIcon,
    },
    {
      name: 'Emails',
      label: __('Emails'),
      icon: EmailIcon,
    },
    {
      name: 'Notes',
      label: countLabel('Notes', 'notes'),
      icon: NoteIcon,
    },
    {
      name: 'Work',
      label: countLabel('Work', 'work'),
      icon: TaskIcon,
    },
    {
      name: 'Activity',
      label: __('Activity'),
      icon: ActivityIcon,
    },
    {
      name: 'Calls',
      label: countLabel('Calls', 'calls'),
      icon: PhoneIcon,
      condition: () => callEnabled.value,
    },
    {
      name: 'ERPNext',
      label: __('ERPNext'),
      icon: LinkIcon,
      condition: () => erpnextInstalled.value,
    },
    {
      name: 'WhatsApp',
      label: __('WhatsApp'),
      icon: WhatsAppIcon,
      condition: () => whatsappEnabled.value,
    },
  ]
  return tabOptions.filter((tab) => (tab.condition ? tab.condition() : true))
})

const erpnextInstalled = ref(false)
onMounted(async () => {
  try {
    erpnextInstalled.value = !!(await call('frappe.client.get_single_value', {
      doctype: 'ERPNext CRM Settings',
      field: 'enabled',
    }))
  } catch {
    erpnextInstalled.value = 'erpnext' in (window.frappe?.boot?.versions || {})
  }
})

const { tabIndex, changeTabTo } = useRecordTabManager(tabs, () => props.leadId)

async function triggerStatusChange(value) {
  await triggerOnChange('status', value)
  setLostReason()
}

function updateField(name, value) {
  value = Array.isArray(name) ? '' : value
  let oldValues = Array.isArray(name) ? {} : doc.value[name]

  if (Array.isArray(name)) {
    name.forEach((field) => (doc.value[field] = value))
  } else {
    doc.value[name] = value
  }

  document.save.submit(null, {
    onSuccess: () => (reload.value = true),
    onError: (err) => {
      if (Array.isArray(name)) {
        name.forEach((field) => (doc.value[field] = oldValues[field]))
      } else {
        doc.value[name] = oldValues
      }
      toast.error(err.messages?.[0] || __('Error updating field'))
    },
  })
}

function deleteLead() {
  showDeleteLinkedDocModal.value = true
}

function openEmailBox() {
  let currentTab = tabs.value[tabIndex.value]
  if (!['Emails', 'Comments', 'Activities'].includes(currentTab.name)) {
    activities.value.changeTabTo('emails')
  }
  nextTick(() => (activities.value.emailBox.show = true))
}

const leadStatusTheme = computed(() => {
  const status = getLeadStatus(doc.value.status)
  if (!status) return 'gray'
  const type = (status.type || '').toLowerCase()
  if (type === 'won') return 'green'
  if (type === 'lost') return 'red'
  if (type === 'open') return 'blue'
  return 'purple'
})

function statusLabel(status) {
  if (isTranslatable('CRM Lead Status')) return __(status)
  return status
}

const showLostReasonModal = ref(false)

function setLostReason() {
  if (
    getLeadStatus(document.doc.status).type !== 'Lost' ||
    (document.doc.lost_reason && document.doc.lost_reason !== 'Other') ||
    (document.doc.lost_reason === 'Other' && document.doc.lost_notes)
  ) {
    document.save.submit(null, {
      onSuccess: () => {},
    })
    return
  }

  showLostReasonModal.value = true
}

function beforeStatusChange(data) {
  if (
    Object.hasOwn(data ?? {}, 'status') &&
    getLeadStatus(data.status).type == 'Lost'
  ) {
    setLostReason()
  } else {
    document.save.submit(null, {
      onSuccess: () => reloadResources(data),
    })
  }
}

function reloadResources(data) {
  counts.reload()
  if (Object.hasOwn(data ?? {}, 'lead_owner')) {
    assignees.reload()
  }

}

watch(reload, (value) => {
  if (value) counts.reload()
})
</script>
