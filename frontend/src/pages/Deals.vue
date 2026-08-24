<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="Deals" />
    </template>
    <template #right-header>
      <CustomActions
        v-if="dealsListView?.customListActions"
        :actions="dealsListView.customListActions"
      />
      <Button
        variant="solid"
        :label="__('Create')"
        iconLeft="plus"
        @click="showDealModal = true"
      />
    </template>
  </LayoutHeader>
  <ViewControls
    ref="viewControls"
    v-model="deals"
    v-model:loadMore="loadMore"
    v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount"
    doctype="CRM Deal"
    :options="{
      allowedViews: ['list', 'group_by', 'kanban'],
    }"
  />
  <KanbanView
    v-if="route.params.viewType == 'kanban'"
    v-model="deals"
    colorful
    hide-card-footer
    hide-field-section
    :options="{
      getRoute: (row) => ({
        name: 'Deal',
        params: { dealId: row.name },
        query: { view: route.query.view, viewType: route.params.viewType },
      }),
      onNewClick: (column) => onNewClick(column),
    }"
    @update="(data) => viewControls.updateKanbanSettings(data)"
    @loadMore="(columnName) => viewControls.loadMoreKanban(columnName)"
  >
    <template #title="{ itemName, fields, titleField, stageTheme }">
      <div class="flex min-w-0 flex-col gap-1">
        <div class="truncate text-[15px] font-semibold leading-snug text-ink-gray-9">
          {{ dealCardTitle(fields, itemName, titleField) || __('No Title') }}
        </div>
        <div
          v-if="dealCardLabel(fields, itemName, 'organization')"
          class="truncate text-xs text-ink-gray-6"
        >
          {{ dealCardLabel(fields, itemName, 'organization') }}
        </div>
        <div
          v-if="showDealCardContact(fields, itemName, titleField)"
          class="truncate text-xs text-ink-gray-5"
        >
          {{ dealCardLabel(fields, itemName, 'contact') }}
        </div>
        <div
          class="mt-2 flex flex-col gap-1.5 rounded-md px-2.5 py-2 ring-1 ring-inset"
          :class="stageTheme?.chip || 'bg-surface-gray-2 ring-outline-gray-2'"
        >
          <div class="flex items-center justify-between gap-2">
            <span class="shrink-0 text-[10px] font-semibold uppercase tracking-wide text-ink-gray-5">
              {{ __('Deal value') }}
            </span>
            <span class="truncate text-sm font-bold tabular-nums text-ink-gray-9">
              {{ dealCardDealValue(fields, itemName) }}
            </span>
          </div>
          <div class="flex items-center justify-between gap-2">
            <span class="shrink-0 text-[10px] font-semibold uppercase tracking-wide text-ink-gray-5">
              {{ __('Expected revenue') }}
            </span>
            <span
              class="truncate text-sm font-bold tabular-nums"
              :class="stageTheme?.total || 'text-ink-gray-9'"
            >
              {{ dealCardExpectedRevenue(fields, itemName) }}
            </span>
          </div>
        </div>
      </div>
    </template>

    <template #fields="{ fieldName, itemName }">
      <div
        v-if="getRow(itemName, fieldName).label"
        class="truncate flex items-center gap-2"
      >
        <div v-if="fieldName === 'status'">
          <IndicatorIcon :class="getRow(itemName, fieldName).color" />
        </div>
        <div v-else-if="fieldName === 'contact'" class="truncate text-base text-ink-gray-7">
          {{ getRow(itemName, fieldName).label }}
        </div>
        <div v-else-if="fieldName === 'organization'">
          <Avatar
            v-if="getRow(itemName, fieldName).label"
            class="flex items-center"
            :image="getRow(itemName, fieldName).logo"
            :label="getRow(itemName, fieldName).label"
            size="xs"
          />
        </div>
        <div v-else-if="fieldName === 'deal_owner'">
          <Avatar
            v-if="getRow(itemName, fieldName).full_name"
            class="flex items-center"
            :image="getRow(itemName, fieldName).user_image"
            :label="getRow(itemName, fieldName).full_name"
            size="xs"
          />
        </div>
        <div
          v-if="
            [
              'modified',
              'creation',
              'first_response_time',
              'first_responded_on',
              'response_by',
            ].includes(fieldName)
          "
          class="truncate text-base"
        >
          <Tooltip :text="getRow(itemName, fieldName).label">
            <div>{{ getRow(itemName, fieldName).timeAgo }}</div>
          </Tooltip>
        </div>
        <div v-else-if="fieldName === 'sla_status'" class="truncate text-base">
          <Badge
            v-if="getRow(itemName, fieldName).value"
            :variant="'subtle'"
            :theme="getRow(itemName, fieldName).color"
            size="md"
            :label="getRow(itemName, fieldName).value"
          />
        </div>
        <div
          v-else-if="fieldName === '_assign'"
          class="flex items-center truncate"
        >
          <MultipleAvatar
            :avatars="getRow(itemName, fieldName).label"
            size="xs"
          />
        </div>
        <div
          v-else-if="fieldName === 'deal_value'"
          class="truncate text-base font-semibold text-ink-gray-9"
        >
          {{ getRow(itemName, fieldName).label }}
        </div>
        <div v-else class="truncate text-base">
          {{ getRow(itemName, fieldName).label }}
        </div>
      </div>
    </template>

    <template #actions></template>
  </KanbanView>
  <DealsListView
    v-else-if="deals.data && rows.length"
    ref="dealsListView"
    v-model="deals.data.page_length_count"
    v-model:list="deals"
    :rows="rows"
    :columns="columns"
    :options="{
      showTooltip: false,
      resizeColumn: true,
      rowCount: deals.data.row_count,
      totalCount: deals.data.total_count,
    }"
    @loadMore="() => loadMore++"
    @columnWidthUpdated="() => triggerResize++"
    @updatePageCount="(count) => (updatedPageCount = count)"
    @applyFilter="(data) => viewControls.applyFilter(data)"
    @applyLikeFilter="(data) => viewControls.applyLikeFilter(data)"
    @likeDoc="(data) => viewControls.likeDoc(data)"
    @selectionsChanged="
      (selections) => viewControls.updateSelections(selections)
    "
  />
  <EmptyState
    v-else-if="deals.data && !rows.length"
    name="Deals"
    :icon="DealsIcon"
  />
  <DealModal
    v-if="showDealModal"
    v-model="showDealModal"
    :defaults="defaults"
  />
</template>

<script setup>
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import MultipleAvatar from '@/components/MultipleAvatar.vue'
import CustomActions from '@/components/CustomActions.vue'
import EmailAtIcon from '@/components/Icons/EmailAtIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import DealsListView from '@/components/ListViews/DealsListView.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import KanbanView from '@/components/Kanban/KanbanView.vue'
import DealModal from '@/components/Modals/DealModal.vue'
import ViewControls from '@/components/ViewControls.vue'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { getMeta } from '@/stores/meta'
import { globalStore } from '@/stores/global'
import { usersStore } from '@/stores/users'
import { organizationsStore } from '@/stores/organizations'
import { statusesStore } from '@/stores/statuses'
import { callEnabled } from '@/composables/telephony'
import { formatDate, timeAgo, website, formatTime } from '@/utils'
import { useOnboarding, useTelemetry } from 'frappe-ui/frappe'
import { Tooltip, Avatar, Dropdown } from 'frappe-ui'
import { useRoute } from 'vue-router'
import { ref, reactive, computed, h } from 'vue'

const { getFormattedPercent, getFormattedFloat, getFormattedCurrency } =
  getMeta('CRM Deal')
const { makeCall } = globalStore()
const { getUser } = usersStore()
const { getOrganization } = organizationsStore()
const { getDealStatus } = statusesStore()
const { updateOnboardingStep } = useOnboarding('frappecrm')
const { capture } = useTelemetry()
const { showModal } = useDoctypeModal()

const route = useRoute()

const dealsListView = ref(null)
const showDealModal = ref(false)

const defaults = reactive({})

// deals data is loaded in the ViewControls component
const deals = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

function getRow(name, field) {
  function getValue(value) {
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      return value
    }
    return { label: value }
  }
  return getValue(rows.value?.find((row) => row.name == name)?.[field])
}

// Rows
const rows = computed(() => {
  if (!deals.value?.data?.data) return []
  if (deals.value.data.view_type === 'group_by') {
    if (!deals.value?.data.group_by_field?.fieldname) return []
    return getGroupedByRows(
      deals.value?.data.data,
      deals.value?.data.group_by_field,
      deals.value.data.columns,
    )
  } else if (deals.value.data.view_type === 'kanban') {
    return getKanbanRows(deals.value.data.data, deals.value.data.fields)
  } else {
    return parseRows(deals.value?.data.data, deals.value.data.columns)
  }
})

const columns = computed(() => {
  let _columns = deals.value?.data?.columns || []

  if (_columns.length) {
    _columns = _columns.map((col, index) => {
      if (index === _columns.length - 1) {
        return { ...col, align: 'right' }
      }
      return col
    })
  }

  return _columns
})

function getGroupedByRows(listRows, groupByField, columns) {
  let groupedRows = []

  groupByField.options?.forEach((option) => {
    let filteredRows

    if (!option) {
      filteredRows = listRows.filter((row) => !row[groupByField.fieldname])
    } else {
      filteredRows = listRows.filter(
        (row) => row[groupByField.fieldname] == option,
      )
    }

    let groupDetail = {
      label: groupByField.label,
      group: option || __(' '),
      collapsed: false,
      rows: parseRows(filteredRows, columns),
    }
    if (groupByField.fieldname == 'status') {
      groupDetail.icon = () =>
        h(IndicatorIcon, {
          class: getDealStatus(option)?.color,
        })
    }
    groupedRows.push(groupDetail)
  })

  return groupedRows || listRows
}

function getKanbanRows(data, columns) {
  let _rows = []
  data.forEach((column) => {
    column.data?.forEach((row) => {
      _rows.push(row)
    })
  })
  return parseRows(_rows, columns)
}

function parseRows(rows, columns = []) {
  let view_type = deals.value.data.view_type
  let key = view_type === 'kanban' ? 'fieldname' : 'key'
  let type = view_type === 'kanban' ? 'fieldtype' : 'type'

  return rows.map((deal) => {
    let _rows = {}
    deals.value.data.rows.forEach((row) => {
      _rows[row] = deal[row]

      let fieldType = columns?.find((col) => (col[key] || col.value) == row)?.[
        type
      ]

      if (
        fieldType &&
        ['Date', 'Datetime'].includes(fieldType) &&
        !['modified', 'creation'].includes(row)
      ) {
        _rows[row] = formatDate(deal[row], '', true, fieldType == 'Datetime')
      }

      if (fieldType && fieldType == 'Currency') {
        _rows[row] = getFormattedCurrency(row, deal)
      }

      if (fieldType && fieldType == 'Float') {
        _rows[row] = getFormattedFloat(row, deal)
      }

      if (fieldType && fieldType == 'Percent') {
        _rows[row] = getFormattedPercent(row, deal)
      }

      if (row == 'deal_name') {
        _rows[row] = {
          label: deal.deal_name || deal.name,
        }
      } else if (row == 'organization') {
        const org = getOrganization(deal.organization)
        _rows[row] = {
          label:
            org?.organization_name ||
            deal.organization_name ||
            deal.deal_name ||
            deal.organization,
          logo: org?.organization_logo,
        }
      } else if (row === 'website') {
        _rows[row] = website(deal.website)
      } else if (row == 'status') {
        _rows[row] = {
          label: deal.status,
          color: getDealStatus(deal.status)?.color,
        }
      } else if (row == 'sla_status') {
        let value = deal.sla_status
        let tooltipText = value
        let color =
          deal.sla_status == 'Failed'
            ? 'red'
            : deal.sla_status == 'Fulfilled'
              ? 'green'
              : 'orange'
        if (value == 'First Response Due' || value == 'Rolling Response Due') {
          value = __(timeAgo(deal.response_by))
          tooltipText = formatDate(deal.response_by)
          if (new Date(deal.response_by) < new Date()) {
            color = 'red'
          }
        }
        _rows[row] = {
          label: tooltipText,
          value: value,
          color: color,
        }
      } else if (row == 'deal_value') {
        const raw = deal.deal_value || deal.expected_deal_value || 0
        _rows[row] = {
          label: raw ? getFormattedCurrency('deal_value', deal) : '',
          raw,
        }
      } else if (row == 'expected_deal_value') {
        _rows[row] = {
          label: deal.expected_deal_value
            ? getFormattedCurrency('expected_deal_value', deal)
            : '',
        }
      } else if (row == 'organization_name') {
        _rows[row] = {
          label: deal.organization_name || '',
        }
      } else if (row == 'contact') {
        _rows[row] = {
          label: deal.contact,
        }
      } else if (row == 'deal_owner') {
        _rows[row] = {
          label: deal.deal_owner && getUser(deal.deal_owner).full_name,
          ...(deal.deal_owner && getUser(deal.deal_owner)),
        }
      } else if (row == '_assign') {
        let assignees = JSON.parse(deal._assign || '[]')
        _rows[row] = assignees.map((user) => ({
          name: user,
          image: getUser(user).user_image,
          label: getUser(user).full_name,
        }))
      } else if (['modified', 'creation'].includes(row)) {
        _rows[row] = {
          label: formatDate(deal[row]),
          timeAgo: __(timeAgo(deal[row])),
        }
      } else if (
        ['first_response_time', 'first_responded_on', 'response_by'].includes(
          row,
        )
      ) {
        let field = row == 'response_by' ? 'response_by' : 'first_responded_on'
        _rows[row] = {
          label: deal[field] ? formatDate(deal[field]) : '',
          timeAgo: deal[row]
            ? row == 'first_response_time'
              ? formatTime(deal[row])
              : __(timeAgo(deal[row]))
            : '',
        }
      }
    })
    _rows['_email_count'] = deal._email_count
    _rows['_note_count'] = deal._note_count
    _rows['_task_count'] = deal._task_count
    _rows['_comment_count'] = deal._comment_count
    return _rows
  })
}


function resolveDealRow(row, itemName) {
  if (row && typeof row === 'object') return row
  for (const column of deals.value?.data?.data || []) {
    const deal = column.data?.find((d) => d.name === itemName)
    if (deal) return deal
  }
  return null
}

function dealCardTitle(row, itemName, titleField) {
  const deal = resolveDealRow(row, itemName)
  if (deal) {
    return (
      deal.deal_name ||
      (titleField && deal[titleField]) ||
      deal.contact ||
      deal.organization_name ||
      deal.organization ||
      ''
    )
  }
  return (
    getRow(itemName, 'deal_name')?.label ||
    (titleField ? getRow(itemName, titleField)?.label : '') ||
    getRow(itemName, 'contact')?.label ||
    ''
  )
}

function dealCardLabel(row, itemName, field) {
  const deal = resolveDealRow(row, itemName)
  if (deal) {
    if (field === 'organization') {
      const org = deal.organization ? getOrganization(deal.organization) : null
      return (
        org?.organization_name ||
        deal.organization_name ||
        deal.organization ||
        ''
      )
    }
    if (field === 'contact') return deal.contact || ''
    if (field === 'organization_name') return deal.organization_name || ''
    return deal[field] || ''
  }
  if (field === 'organization') {
    return (
      getRow(itemName, 'organization')?.label ||
      getRow(itemName, 'organization_name')?.label ||
      ''
    )
  }
  return getRow(itemName, field)?.label || ''
}

function dealCardDealValue(row, itemName) {
  const deal = resolveDealRow(row, itemName)
  if (deal) {
    return getFormattedCurrency('deal_value', deal)
  }
  return getRow(itemName, 'deal_value')?.label || '₹ 0.00'
}

function dealCardExpectedRevenue(row, itemName) {
  const deal = resolveDealRow(row, itemName)
  if (deal) {
    if (deal.expected_deal_value) {
      return getFormattedCurrency('expected_deal_value', deal)
    }
    const dealValue = deal.deal_value || 0
    const probability = deal.probability || 0
    if (dealValue && probability) {
      return getFormattedCurrency('expected_deal_value', {
        ...deal,
        expected_deal_value: (dealValue * probability) / 100,
      })
    }
    return getFormattedCurrency('expected_deal_value', deal)
  }
  return getRow(itemName, 'expected_deal_value')?.label || '₹ 0.00'
}

function showDealCardContact(row, itemName, titleField) {
  const contact = dealCardLabel(row, itemName, 'contact')
  if (!contact) return false
  const title = dealCardTitle(row, itemName, titleField)
  return contact !== title
}

function onNewClick(column) {
  let column_field = deals.value.params.column_field

  if (column_field) {
    defaults[column_field] = column.column.name
  }

  showDealModal.value = true
}

function actions(itemName) {
  let mobile_no = getRow(itemName, 'mobile_no')?.label || ''
  let actions = [
    {
      icon: h(PhoneIcon, { class: 'h-4 w-4' }),
      label: __('Make a Call'),
      onClick: () => makeCall(mobile_no),
      condition: () => mobile_no && callEnabled.value,
    },
    {
      icon: h(NoteIcon, { class: 'h-4 w-4' }),
      label: __('New Note'),
      onClick: () => showNote(itemName),
    },
    {
      icon: h(TaskIcon, { class: 'h-4 w-4' }),
      label: __('New Task'),
      onClick: () => showTask(itemName),
    },
  ]
  return actions.filter((action) =>
    action.condition ? action.condition() : true,
  )
}

function showNote(name) {
  showModal({
    doctype: 'FCRM Note',
    title: 'Note',
    defaults: {
      reference_doctype: 'CRM Deal',
      reference_docname: name,
    },
    callbacks: {
      afterInsert: (d) => after(d, true),
      afterUpdate: after,
    },
  })
}

function showTask(name) {
  showModal({
    doctype: 'CRM Task',
    title: 'Task',
    defaults: {
      reference_doctype: 'CRM Deal',
      reference_docname: name,
    },
    callbacks: {
      afterInsert: (d) => after(d, true),
      afterUpdate: after,
    },
  })
}

function after(d, isNew = false) {
  let a = d.doctype == 'CRM Task' ? 'task' : 'note'
  if (isNew) {
    updateOnboardingStep('create_first_' + a)
    capture(a + '_created')
  } else {
    capture(a + '_updated')
  }
}
</script>
