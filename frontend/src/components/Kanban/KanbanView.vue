<template>
  <div class="flex overflow-x-auto h-full">
    <Draggable
      v-if="columns"
      :list="columns"
      item-key="column"
      :delay="isTouchScreenDevice() ? 200 : 0"
      class="flex sm:mx-2.5 mx-2 pb-3.5"
      @end="updateColumn"
    >
      <template #item="{ element: column }">
        <div
          v-if="!column.column.delete"
          :class="[
            'flex h-full min-h-0 w-80 min-w-80 max-w-80 shrink-0 flex-col rounded-xl p-2 ring-1',
            colorful ? getStageTheme(column.column.color).shell : 'hover:bg-surface-gray-2',
          ]"
        >
          <div :class="[
            'group mb-2 shrink-0 rounded-lg border px-2.5 pb-2.5 pt-2',
            colorful
              ? getStageTheme(column.column.color).header
              : 'border-b border-outline-gray-2 bg-transparent px-0 pt-0',
          ]">
            <div class="flex min-w-0 items-start gap-1.5">
              <Popover>
                <template #target="{ togglePopover }">
                  <Button
                    variant="ghost"
                    size="sm"
                    class="mt-0.5 shrink-0 hover:!bg-surface-gray-2"
                    @click="togglePopover"
                  >
                    <IndicatorIcon :class="parseColor(column.column.color)" />
                  </Button>
                </template>
                <template #body>
                  <div
                    class="flex flex-col gap-3 px-3 py-2.5 min-w-40 rounded-lg bg-surface-modal shadow-2xl ring-1 ring-black ring-opacity-5 focus:outline-none"
                  >
                    <div class="flex gap-1">
                      <Button
                        v-for="color in colors"
                        :key="color"
                        variant="ghost"
                        @click="() => (column.column.color = color)"
                      >
                        <IndicatorIcon :class="parseColor(color)" />
                      </Button>
                    </div>
                    <div class="flex flex-row-reverse">
                      <Button
                        variant="solid"
                        :label="__('Apply')"
                        @click="updateColumn"
                      />
                    </div>
                  </div>
                </template>
              </Popover>
              <div class="min-w-0 flex-1">
                <Tooltip :text="column.column.name">
                  <div :class="[
                    'block w-full truncate text-sm font-semibold leading-5',
                    colorful
                      ? getStageTheme(column.column.color).title
                      : 'text-ink-gray-9',
                  ]">
                    {{ column.column.name }}
                  </div>
                </Tooltip>
              </div>
              <div class="flex shrink-0">
                <Dropdown :options="actions(column)">
                  <template #default>
                    <Button
                      class="opacity-0 group-hover:opacity-100 pointer-events-none group-hover:pointer-events-auto transition-opacity"
                      icon="more-horizontal"
                      variant="ghost"
                    />
                  </template>
                </Dropdown>
                <Button
                  icon="plus"
                  variant="ghost"
                  @click="options.onNewClick(column)"
                />
              </div>
            </div>
            <div class="mt-1 flex items-center gap-1.5 pl-8 text-xs leading-4 text-ink-gray-6">
              <span
                v-if="columnDealCount(column) != null"
                :class="[
                'inline-flex min-w-[1.25rem] items-center justify-center rounded-full px-1.5 py-0.5 text-xs font-semibold ring-1 ring-inset',
                colorful
                  ? getStageTheme(column.column.color).chip
                  : 'bg-surface-gray-3 text-ink-gray-7',
              ]"
              >{{ columnDealCount(column) }}</span>
              <template v-if="column.column.stage_probability != null">
                <span class="text-ink-gray-4">·</span>
                <span>{{ column.column.stage_probability }}%</span>
              </template>
            </div>
            <div :class="[
              'mt-0.5 truncate pl-8 text-sm font-bold leading-5 tabular-nums',
              colorful
                ? getStageTheme(column.column.color).total
                : 'text-ink-gray-9',
            ]">
              {{ formatStageTotal(columnStageTotal(column)) }}
            </div>
          </div>
          <div class="flex min-h-0 flex-1 flex-col gap-2 overflow-y-auto">
            <Draggable
              :list="column.data"
              group="fields"
              item-key="name"
              class="flex flex-col gap-3.5 flex-1"
              :delay="isTouchScreenDevice() ? 200 : 0"
              :data-column="column.column.name"
              @end="updateColumn"
            >
              <template #item="{ element: fields }">
                <component
                  :is="options.getRoute ? 'router-link' : 'div'"
                  :class="[
                    'px-3 py-3 rounded-lg text-base flex flex-col text-ink-gray-9 shadow-sm hover:shadow-md transition-all',
                    colorful
                      ? getStageTheme(column.column.color).card
                      : 'border border-outline-gray-2 bg-surface-white',
                  ]"
                  :data-name="fields.name"
                  v-bind="{
                    to: options.getRoute ? options.getRoute(fields) : undefined,
                    onClick: options.onClick
                      ? () => options.onClick(fields)
                      : undefined,
                  }"
                >
                  <slot
                    name="title"
                    v-bind="{
                      fields,
                      titleField,
                      itemName: fields.name,
                      column,
                      columnColor: column.column.color,
                      stageTheme: getStageTheme(column.column.color),
                    }"
                  >
                    <div class="h-5 flex items-center">
                      <div v-if="fields[titleField]">
                        {{ fields[titleField] }}
                      </div>
                      <div v-else class="text-ink-gray-4">
                        {{ __('No Title') }}
                      </div>
                    </div>
                  </slot>
                  <div
                    v-if="!hideFieldSection && column.fields?.length"
                    class="border-b h-px my-2.5"
                  />

                  <div
                    v-if="!hideFieldSection && column.fields?.length"
                    class="flex flex-col gap-3.5"
                  >
                    <template v-for="value in column.fields" :key="value">
                      <slot
                        name="fields"
                        v-bind="{
                          fields,
                          fieldName: value,
                          itemName: fields.name,
                        }"
                      >
                        <div v-if="fields[value]" class="truncate">
                          {{ fields[value] }}
                        </div>
                      </slot>
                    </template>
                  </div>
                  <div
                    v-if="!hideCardFooter"
                    class="border-b h-px mt-2.5 mb-2"
                  />
                  <slot
                    v-if="!hideCardFooter"
                    name="actions" v-bind="{ itemName: fields.name }">
                    <div class="flex gap-2 items-center justify-between">
                      <div></div>
                      <Button icon="plus" variant="ghost" @click.stop.prevent />
                    </div>
                  </slot>
                </component>
              </template>
            </Draggable>
            <div
              v-if="column.column.count < column.column.all_count"
              class="flex items-center justify-center"
            >
              <Button
                :label="__('Load More')"
                @click="emit('loadMore', column.column.name)"
              />
            </div>
          </div>
        </div>
      </template>
    </Draggable>
    <div class="shrink-0 min-w-64">
      <Autocomplete
        value=""
        :options="deletedColumns"
        @change="(e) => addColumn(e)"
      >
        <template #target="{ togglePopover }">
          <Button
            class="w-full mt-2.5 mb-1 mr-5"
            :label="__('Add Column')"
            iconLeft="plus"
            @click="togglePopover()"
          />
        </template>
        <template #footer>
          <Button
            class="w-full"
            :label="__('Reload Columns')"
            :iconLeft="RefreshIcon"
            @click="updateColumn(null, true)"
          />
        </template>
      </Autocomplete>
    </div>
  </div>
</template>
<script setup>
import RefreshIcon from '@/components/Icons/RefreshIcon.vue'
import Autocomplete from '@/components/frappe-ui/Autocomplete.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import { isTouchScreenDevice, colors, parseColor } from '@/utils'
import Draggable from 'vuedraggable'
import { Dropdown, Popover, Tooltip } from 'frappe-ui'
import { computed } from 'vue'

const STAGE_THEME = {
  gray: {
    shell: 'bg-gray-50/80 ring-gray-200',
    header: 'bg-gray-100 border-gray-300',
    title: 'text-gray-900',
    total: 'text-gray-800',
    chip: 'bg-white text-gray-700 ring-gray-200',
    card: 'border-l-[4px] border-l-gray-500 bg-white ring-gray-200/80',
    icon: 'gray',
  },
  blue: {
    shell: 'bg-blue-50/70 ring-blue-200',
    header: 'bg-blue-100/80 border-blue-300',
    title: 'text-blue-950',
    total: 'text-blue-800',
    chip: 'bg-white text-blue-800 ring-blue-200',
    card: 'border-l-[4px] border-l-blue-500 bg-white ring-blue-200/70',
    icon: 'blue',
  },
  cyan: {
    shell: 'bg-cyan-50/70 ring-cyan-200',
    header: 'bg-cyan-100/80 border-cyan-300',
    title: 'text-cyan-950',
    total: 'text-cyan-800',
    chip: 'bg-white text-cyan-800 ring-cyan-200',
    card: 'border-l-[4px] border-l-cyan-500 bg-white ring-cyan-200/70',
    icon: 'cyan',
  },
  teal: {
    shell: 'bg-teal-50/70 ring-teal-200',
    header: 'bg-teal-100/80 border-teal-300',
    title: 'text-teal-950',
    total: 'text-teal-800',
    chip: 'bg-white text-teal-800 ring-teal-200',
    card: 'border-l-[4px] border-l-teal-500 bg-white ring-teal-200/70',
    icon: 'teal',
  },
  orange: {
    shell: 'bg-orange-50/70 ring-orange-200',
    header: 'bg-orange-100/80 border-orange-300',
    title: 'text-orange-950',
    total: 'text-orange-800',
    chip: 'bg-white text-orange-800 ring-orange-200',
    card: 'border-l-[4px] border-l-orange-500 bg-white ring-orange-200/70',
    icon: 'orange',
  },
  green: {
    shell: 'bg-green-50/70 ring-green-200',
    header: 'bg-green-100/80 border-green-300',
    title: 'text-green-950',
    total: 'text-green-800',
    chip: 'bg-white text-green-800 ring-green-200',
    card: 'border-l-[4px] border-l-green-600 bg-white ring-green-200/70',
    icon: 'green',
  },
  red: {
    shell: 'bg-red-50/70 ring-red-200',
    header: 'bg-red-100/80 border-red-300',
    title: 'text-red-950',
    total: 'text-red-800',
    chip: 'bg-white text-red-800 ring-red-200',
    card: 'border-l-[4px] border-l-red-500 bg-white ring-red-200/70',
    icon: 'red',
  },
  pink: {
    shell: 'bg-pink-50/70 ring-pink-200',
    header: 'bg-pink-100/80 border-pink-300',
    title: 'text-pink-950',
    total: 'text-pink-800',
    chip: 'bg-white text-pink-800 ring-pink-200',
    card: 'border-l-[4px] border-l-pink-500 bg-white ring-pink-200/70',
    icon: 'pink',
  },
  violet: {
    shell: 'bg-violet-50/70 ring-violet-200',
    header: 'bg-violet-100/80 border-violet-300',
    title: 'text-violet-950',
    total: 'text-violet-800',
    chip: 'bg-white text-violet-800 ring-violet-200',
    card: 'border-l-[4px] border-l-violet-500 bg-white ring-violet-200/70',
    icon: 'violet',
  },
  purple: {
    shell: 'bg-purple-50/70 ring-purple-200',
    header: 'bg-purple-100/80 border-purple-300',
    title: 'text-purple-950',
    total: 'text-purple-800',
    chip: 'bg-white text-purple-800 ring-purple-200',
    card: 'border-l-[4px] border-l-purple-500 bg-white ring-purple-200/70',
    icon: 'purple',
  },
  amber: {
    shell: 'bg-amber-50/70 ring-amber-200',
    header: 'bg-amber-100/80 border-amber-300',
    title: 'text-amber-950',
    total: 'text-amber-800',
    chip: 'bg-white text-amber-800 ring-amber-200',
    card: 'border-l-[4px] border-l-amber-500 bg-white ring-amber-200/70',
    icon: 'amber',
  },
  yellow: {
    shell: 'bg-yellow-50/70 ring-yellow-200',
    header: 'bg-yellow-100/80 border-yellow-300',
    title: 'text-yellow-950',
    total: 'text-yellow-800',
    chip: 'bg-white text-yellow-800 ring-yellow-200',
    card: 'border-l-[4px] border-l-yellow-500 bg-white ring-yellow-200/70',
    icon: 'yellow',
  },
  black: {
    shell: 'bg-ink-gray-1 ring-ink-gray-3',
    header: 'bg-ink-gray-2 border-ink-gray-4',
    title: 'text-ink-gray-9',
    total: 'text-ink-gray-9',
    chip: 'bg-white text-ink-gray-8 ring-ink-gray-3',
    card: 'border-l-[4px] border-l-ink-gray-8 bg-white ring-ink-gray-3',
    icon: 'black',
  },
}

function getStageTheme(color) {
  return STAGE_THEME[color] || STAGE_THEME.gray
}

function formatStageTotal(value) {
  if (!value) return '₹ 0.00'
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 2,
  }).format(value)
}

function columnDealCount(column) {
  const col = column?.column || {}
  if (col.deal_count != null) return col.deal_count
  if (col.count != null) return col.count
  return column?.data?.length ?? null
}

function columnStageTotal(column) {
  const col = column?.column || {}
  if (col.stage_total != null) return col.stage_total
  const deals = column?.data || []
  const stageProbability = col.stage_probability || 0
  return deals.reduce((sum, deal) => {
    const expected = deal.expected_deal_value || 0
    if (expected) return sum + Number(expected)
    const dealValue = deal.deal_value || 0
    const probability = deal.probability ?? stageProbability
    return sum + (Number(dealValue) * Number(probability)) / 100
  }, 0)
}

defineProps({
  hideCardFooter: {
    type: Boolean,
    default: false,
  },
  hideFieldSection: {
    type: Boolean,
    default: false,
  },
  options: {
    type: Object,
    default: () => ({
      getRoute: null,
      onClick: null,
      onNewClick: null,
    }),
  },
  colorful: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update', 'loadMore'])

const kanban = defineModel({ type: Object })

const titleField = computed(() => {
  return kanban.value?.data?.title_field
})

const columns = computed(() => {
  if (!kanban.value?.data?.data || kanban.value.data.view_type != 'kanban')
    return []
  let _columns = kanban.value.data.data

  let has_color = _columns.some((column) => column.column?.color)
  if (!has_color) {
    _columns.forEach((column, i) => {
      column.column['color'] = colors[i % colors.length]
    })
  }
  return _columns
})

const deletedColumns = computed(() => {
  const _columns = kanban.value?.data?.kanban_columns || []
  return _columns
    ?.filter((col) => col['delete'])
    .map((col) => {
      return { label: col.name, value: col.name }
    })
})

function actions(column) {
  return [
    {
      group: __('Options'),
      hideLabel: true,
      items: [
        {
          label: __('Delete'),
          icon: 'trash-2',
          onClick: () => {
            column.column['delete'] = true
            updateColumn()
          },
        },
      ],
    },
  ]
}

function addColumn(e) {
  let column = columns.value.find((col) => col.column.name == e.value)
  column.column['delete'] = false
  columns.value.splice(columns.value.indexOf(column), 1)
  columns.value.push(column)
  updateColumn()
}

function updateColumn(d, fetchNewColumns = false) {
  let toColumn = d?.to?.dataset.column
  let fromColumn = d?.from?.dataset.column
  let itemName = d?.item?.dataset.name

  let _columns = []
  columns.value.forEach((col) => {
    col.column['order'] = col.data.map((d) => d.name)
    if (col.column.page_length) {
      delete col.column.page_length
    }
    _columns.push(col.column)
  })

  let data = { kanban_columns: _columns, fetchNewColumns }

  if (toColumn != fromColumn) {
    data = { item: itemName, to: toColumn, kanban_columns: _columns }
  }

  emit('update', data)
}
</script>
