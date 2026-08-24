<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs">
        <template #prefix="{ item }">
          <Icon v-if="item.icon" :icon="item.icon" class="mr-2 h-4" />
        </template>
      </Breadcrumbs>
      <DocumentNavButtons
        v-if="dealId"
        doctype="CRM Deal"
        :docname="dealId"
        route-name="Deal"
        param-key="dealId"
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
      <AssignTo v-model="assignees.data" doctype="CRM Deal" :docname="dealId" />
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
              <IndicatorIcon :class="getDealStatus(doc.status).color" />
            </template>
          </Button>
        </template>
      </Dropdown>
    </template>
  </LayoutHeader>
  <div
    v-if="doc.name"
    class="flex h-full flex-col overflow-hidden bg-surface-gray-1"
  >
    <RecordHero
      :title="title"
      :subtitle="dealId"
      :label="title"
      :image="organization?.organization_logo"
      :status-label="doc.status ? statusLabel(doc.status) : ''"
      :status-theme="dealStatusTheme"
      @copy-subtitle="copyToClipboard(dealId)"
    >
      <template #actions>
        <Button
          v-if="callEnabled"
          :tooltip="__('Make a Call')"
          :icon="PhoneIcon"
          @click="triggerCall"
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
          icon="trash-2"
          theme="red"
          @click="deleteDeal"
        />
      </template>
      <template #below>
        <SLASection
          v-if="doc.sla_status"
          v-model="doc"
          class="mt-2"
          @updateField="updateField"
        />
      </template>
    </RecordHero>
    <Tabs
      v-model="tabIndex"
      as="div"
      :tabs="tabs"
      :class="RECORD_TAB_LIST_CLASSES"
    >
      <template #tab-item="{ tab }">
        <RecordTabItem :tab="tab" />
      </template>
      <template #tab-panel>
        <DealBOQPanel
          v-if="tabs[tabIndex] && tabs[tabIndex].name === 'BOQ'"
          parent-doctype="CRM Deal"
          :parent-id="dealId"
          @updated="counts.reload()"
        />
        <Activities
          v-else
          ref="activities"
          v-model:reload="reload"
          v-model:tabIndex="tabIndex"
          doctype="CRM Deal"
          :docname="dealId"
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
  <FilesUploader
    v-model="showFilesUploader"
    doctype="CRM Deal"
    :docname="dealId"
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
    :doctype="'CRM Deal'"
    :docname="dealId"
    name="Deals"
  />
  <LostReasonModal
    v-if="showLostReasonModal"
    v-model="showLostReasonModal"
    doctype="CRM Deal"
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
import LinkIcon from '@/components/Icons/LinkIcon.vue'
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import RecordHero from '@/components/Record/RecordHero.vue'
import RecordTabItem from '@/components/Record/RecordTabItem.vue'
import { RECORD_TAB_LIST_CLASSES } from '@/composables/recordPageTabs'
import Activities from '@/components/Activities/Activities.vue'
import DealBOQPanel from '@/estimation/DealBOQPanel.vue'
import DocumentNavButtons from '@/components/Record/DocumentNavButtons.vue'
import LostReasonModal from '@/components/Modals/LostReasonModal.vue'
import AssignTo from '@/components/AssignTo.vue'
import FilesUploader from '@/components/FilesUploader/FilesUploader.vue'
import SLASection from '@/components/SLASection.vue'
import CustomActions from '@/components/CustomActions.vue'
import {
  openWebsite,
  setupCustomizations,
  copyToClipboard,
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
  createResource,
  Dropdown,
  Tooltip,
  Avatar,
  Tabs,
  Breadcrumbs,
  call,
  usePageMeta,
  toast,
} from 'frappe-ui'
import { useOnboarding } from 'frappe-ui/frappe'
import {
  ref,
  computed,
  onMounted,
  onBeforeUnmount,
  nextTick,
  watch,
} from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useRecordTabManager } from '@/composables/useRecordTabManager'
import { useRelatedCounts } from '@/composables/useRelatedCounts'

const { brand } = getSettings()
const { $dialog, $socket, makeCall } = globalStore()
const { statusOptions, getDealStatus } = statusesStore()
const { doctypeMeta } = getMeta('CRM Deal')

const { updateOnboardingStep, isOnboardingStepsCompleted } =
  useOnboarding('frappecrm')

const route = useRoute()
const router = useRouter()

const props = defineProps({
  dealId: { type: String, required: true },
})

const { counts, countLabel } = useRelatedCounts('CRM Deal', () => props.dealId)

const errorTitle = ref('')
const errorMessage = ref('')
const showDeleteLinkedDocModal = ref(false)

const {
  triggerOnChange,
  triggerOnRender,
  assignees,
  permissions,
  document,
  scripts,
  error,
} = useDocument('CRM Deal', props.dealId)

const canDelete = computed(() => permissions.data?.permissions?.delete || false)

const doc = computed(() => document.doc || {})

watch(error, (err) => {
  if (err) {
    errorTitle.value = __(
      err.exc_type == 'DoesNotExistError'
        ? 'Document Not Found'
        : 'Error Occurred',
    )
    errorMessage.value = __(err.messages?.[0] || 'An Error Occurred')
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
        deleteDoc: deleteDeal,
        call,
      })
      document._actions = s.actions || []
      document._statuses = s.statuses || []
    }
  },
  { once: true },
)

const organizationDocument = ref(null)

watch(
  () => doc.value.organization,
  (org) => {
    if (org && !organizationDocument.value?.doc) {
      let { document: _organizationDocument } = useDocument(
        'CRM Organization',
        org,
      )
      organizationDocument.value = _organizationDocument
    }
  },
  { immediate: true },
)

const organization = computed(() => organizationDocument.value?.doc || {})

onMounted(async () => {
  $socket.on('crm_customer_created', () => {
    toast.success(__('Customer Created Successfully'))
  })
  if (document.doc) await triggerOnRender()
})

onBeforeUnmount(() => {
  $socket.off('crm_customer_created')
})

const reload = ref(false)
const showFilesUploader = ref(false)

const breadcrumbs = computed(() => {
  let items = [{ label: __('Deals'), route: { name: 'Deals' } }]

  if (route.query.view || route.query.viewType) {
    let view = getView(route.query.view, route.query.viewType, 'CRM Deal')
    if (view) {
      items.push({
        label: __(view.label),
        icon: view.icon,
        route: {
          name: 'Deals',
          params: { viewType: route.query.viewType },
          query: { view: route.query.view },
        },
      })
    }
  }

  items.push({
    label: title.value,
    route: { name: 'Deal', params: { dealId: props.dealId } },
  })
  return items
})

const title = computed(() => {
  return (
    doc.value?.deal_name ||
    doc.value?.organization_name ||
    doc.value?.[doctypeMeta.value?.title_field || 'name'] ||
    props.dealId
  )
})

const statuses = computed(() => {
  let customStatuses = document.statuses?.length
    ? document.statuses
    : document._statuses || []
  return statusOptions('deal', customStatuses, triggerStatusChange)
})

usePageMeta(() => {
  return {
    title: title.value,
    icon: brand.favicon,
  }
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

const { tabIndex, changeTabTo } = useRecordTabManager(tabs, () => props.dealId)


const dealContacts = createResource({
  url: 'crm.fcrm.doctype.crm_deal.api.get_deal_contacts',
  params: { name: props.dealId },
  cache: ['deal_contacts', props.dealId],
  transform: (data) => {
    data.forEach((contact) => {
      contact.opened = false
    })
    return data
  },
})

if (!dealContacts.data) dealContacts.fetch()

function triggerCall() {
  let primaryContact = dealContacts.data?.find((c) => c.is_primary)
  let mobile_no = primaryContact.mobile_no || null

  if (!primaryContact) {
    toast.error(__('No Primary Contact Set'))
    return
  }

  if (!mobile_no) {
    toast.error(__('No Mobile Number Set'))
    return
  }

  makeCall(mobile_no)
}

async function triggerStatusChange(value) {
  await triggerOnChange('status', value)
  setLostReason()
}

function updateField(name, value) {
  if (name == 'status' && !isOnboardingStepsCompleted.value) {
    updateOnboardingStep('change_deal_status')
  }

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

function deleteDeal() {
  showDeleteLinkedDocModal.value = true
}

const activities = ref(null)

function openEmailBox() {
  let currentTab = tabs.value[tabIndex.value]
  if (!['Emails', 'Comments', 'Activities'].includes(currentTab.name)) {
    activities.value.changeTabTo('emails')
  }
  nextTick(() => (activities.value.emailBox.show = true))
}

const dealStatusTheme = computed(() => {
  const status = getDealStatus(doc.value.status)
  if (!status) return 'gray'
  const type = (status.type || '').toLowerCase()
  if (type === 'won') return 'green'
  if (type === 'lost') return 'red'
  if (type === 'open') return 'blue'
  return 'purple'
})

function statusLabel(status) {
  if (isTranslatable('CRM Deal Status')) return __(status)
  return status
}

const showLostReasonModal = ref(false)

function setLostReason() {
  if (
    getDealStatus(document.doc.status).type !== 'Lost' ||
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
    getDealStatus(data.status).type == 'Lost'
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
  if (Object.hasOwn(data ?? {}, 'deal_owner')) {
    assignees.reload()
  }

}

watch(reload, (value) => {
  if (value) counts.reload()
})
</script>
