<template>
  <div class="flex flex-col gap-2 overflow-y-auto p-3 sm:p-4">
    <div class="flex items-center justify-between gap-3">
      <div class="flex flex-wrap items-baseline gap-x-2 gap-y-0.5 min-w-0">
        <span class="text-base font-semibold tabular-nums text-ink-gray-9">
          ₹ {{ fmt(data.total_quoted) }}
        </span>
        <span class="text-xs text-ink-gray-5">
          · {{ data.count }} {{ data.count === 1 ? __('item') : __('items') }}
          <span v-if="data.show_cost"> · {{ __('cost') }} ₹ {{ fmt(data.total_cost) }}</span>
        </span>
      </div>
      <Button variant="solid" size="sm" @click="openAdd">
        <template #prefix><span class="text-base leading-none">+</span></template>
        {{ __('Add BOQ Item') }}
      </Button>
    </div>

    <div class="overflow-x-auto rounded-lg border border-outline-gray-2">
      <table class="w-full text-sm">
        <thead class="sticky top-0 z-10 bg-surface-gray-2 text-ink-gray-6">
          <tr>
            <th class="px-2 py-1.5 text-left font-medium">#</th>
            <th
              v-if="showSectionColumn"
              class="px-2 py-1.5 text-left font-medium"
            >{{ __('Section') }}</th>
            <th class="px-2 py-1.5 text-left font-medium">{{ __('Description') }}</th>
            <th class="px-2 py-1.5 text-left font-medium">{{ __('System') }}</th>
            <th class="px-2 py-1.5 text-right font-medium whitespace-nowrap">{{ __('Size') }}</th>
            <th class="px-2 py-1.5 text-right font-medium whitespace-nowrap">{{ __('Qty') }}</th>
            <th class="px-2 py-1.5 text-left font-medium">{{ __('Ver') }}</th>
            <th class="px-2 py-1.5 text-left font-medium">{{ __('Status') }}</th>
            <th class="px-2 py-1.5 text-right font-medium whitespace-nowrap">{{ __('Quoted') }}</th>
            <th
              v-if="data.show_cost"
              class="px-2 py-1.5 text-right font-medium whitespace-nowrap"
            >{{ __('Cost') }}</th>
            <th class="px-2 py-1.5 text-right font-medium"></th>
          </tr>
        </thead>
        <tbody>
          <template v-for="group in groupedItems" :key="group.key">
            <tr v-if="groupedItems.length > 1" class="border-t border-outline-gray-1 bg-surface-gray-1">
              <td
                :colspan="colCount"
                class="px-2 py-1 text-xs font-medium text-ink-gray-6"
              >
                {{ group.key }}
                <span class="font-normal text-ink-gray-4">
                  · {{ group.rows.length }} · ₹ {{ fmt(groupQuoted(group.rows)) }}
                </span>
              </td>
            </tr>
            <tr
              v-for="row in group.rows"
              :key="row.name"
              class="border-t border-outline-gray-1 hover:bg-surface-gray-1"
            >
              <td class="px-2 py-1.5 whitespace-nowrap text-ink-gray-5">
                {{ row.item_no || '—' }}
              </td>
              <td
                v-if="showSectionColumn"
                class="px-2 py-1.5 whitespace-nowrap text-ink-gray-5"
              >
                {{ row.section || row.product_group || '—' }}
              </td>
              <td class="px-2 py-1.5 text-ink-gray-8 max-w-[14rem] sm:max-w-[20rem]">
                <div
                  class="truncate"
                  :title="descriptionTitle(row)"
                >
                  {{ row.description }}
                </div>
              </td>
              <td
                class="px-2 py-1.5 whitespace-nowrap text-ink-gray-6 max-w-[8rem] truncate"
                :title="row.system_template || ''"
              >
                {{ row.system_template || '—' }}
              </td>
              <td class="px-2 py-1.5 text-right tabular-nums whitespace-nowrap text-ink-gray-6">
                <template v-if="row.width || row.height">
                  {{ row.width || 0 }}×{{ row.height || 0 }}
                  <span class="text-ink-gray-4">{{ row.dim_unit || 'mm' }}</span>
                </template>
                <span v-else class="text-ink-gray-4">—</span>
              </td>
              <td class="px-2 py-1.5 text-right tabular-nums whitespace-nowrap text-ink-gray-6">
                {{ row.qty }} {{ row.uom || '' }}
              </td>
              <td class="relative px-2 py-1.5 whitespace-nowrap text-ink-gray-6">
                <Button
                  v-if="row.estimation"
                  variant="ghost"
                  size="sm"
                  class="!px-1"
                  :label="'v' + (row.latest_version || 1)"
                  :tooltip="
                    isDraftEstimation(row)
                      ? __('Draft — submit or delete before new version')
                      : __('Version history')
                  "
                  @click="toggleVersionHistory(row)"
                />
                <span v-else>—</span>
                <div
                  v-if="versionHistoryFor === row.name"
                  class="absolute left-0 z-20 mt-1 min-w-[220px] rounded-lg border border-outline-gray-2 bg-surface-white p-2 text-xs shadow-lg"
                >
                  <div v-if="versionHistoryLoading" class="px-1 py-1 text-ink-gray-5">
                    {{ __('Loading…') }}
                  </div>
                  <template v-else>
                    <div
                      v-for="v in versionHistory"
                      :key="v.name"
                      class="flex items-center justify-between gap-2 rounded px-1 py-1 hover:bg-surface-gray-1"
                    >
                      <button
                        type="button"
                        class="text-left text-ink-gray-8 hover:underline"
                        @click="openEstimationName(v.name)"
                      >
                        v{{ v.version }}
                        <span class="text-ink-gray-5">
                          · {{ v.docstatus === 1 ? __('Submitted') : __('Draft') }}
                          <span v-if="v.is_latest"> · {{ __('latest') }}</span>
                        </span>
                      </button>
                    </div>
                    <div v-if="!versionHistory.length" class="px-1 py-1 text-ink-gray-5">
                      {{ __('No versions') }}
                    </div>
                  </template>
                </div>
              </td>
              <td class="px-2 py-1.5 whitespace-nowrap">
                <Badge
                  :theme="statusTheme(row)"
                  :label="displayStatus(row)"
                />
              </td>
              <td class="px-2 py-1.5 text-right tabular-nums whitespace-nowrap font-medium text-ink-gray-9">
                {{ row.quoted_value ? '₹ ' + fmt(row.quoted_value) : '—' }}
              </td>
              <td
                v-if="data.show_cost"
                class="px-2 py-1.5 text-right tabular-nums whitespace-nowrap text-ink-gray-6"
              >
                {{ row.cost_value ? '₹ ' + fmt(row.cost_value) : '—' }}
              </td>
              <td class="px-2 py-1.5 text-right whitespace-nowrap">
                <div class="inline-flex gap-0.5">
                  <Button
                    size="sm"
                    variant="ghost"
                    icon="edit-2"
                    :label="__('Edit')"
                    :tooltip="__('Edit')"
                    @click="openEdit(row)"
                  />
                  <Button
                    v-if="!row.estimation"
                    size="sm"
                    variant="subtle"
                    icon="file-plus"
                    :label="__('Create Estimate')"
                    :tooltip="__('Create Estimate')"
                    :loading="busy === row.name"
                    @click="openCreateEstimate(row)"
                  />
                  <template v-else>
                    <Button
                      size="sm"
                      variant="subtle"
                      icon="external-link"
                      :label="__('Open')"
                      :tooltip="__('Open')"
                      @click="openEstimate(row)"
                    />
                    <Button
                      v-if="!isDraftEstimation(row)"
                      size="sm"
                      variant="ghost"
                      icon="copy"
                      :label="__('New Version')"
                      :tooltip="__('New Version')"
                      :loading="busy === 'v-' + row.name"
                      @click="openCreateEstimate(row, true)"
                    />
                  </template>
                </div>
              </td>
            </tr>
          </template>
          <tr v-if="!data.items.length">
            <td :colspan="colCount" class="px-2 py-8 text-center text-ink-gray-5">
              {{ __('No BOQ items yet. Add one costable line from the client requirement (any format).') }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Add / Edit BOQ -->
    <Dialog v-model="showDialog" :options="{ title: editingName ? __('Edit BOQ Item') : __('Add BOQ Item') }">
      <template #body-content>
        <div class="flex flex-col gap-3">
          <FormControl
            :label="__('Client Mark / BOQ No')"
            v-model="form.item_no"
            :placeholder="__('e.g. D-6, W-01')"
          />
          <FormControl
            :label="__('Section / RFQ Group')"
            v-model="form.section"
            :placeholder="__('e.g. Spider Glazing — optional quote grouping')"
          />
          <FormControl
            :label="__('Description')"
            v-model="form.description"
            :placeholder="__('e.g. SPIDER GLAZING, Door D-6')"
          />
          <FormControl
            type="textarea"
            :label="__('Notes / Spec')"
            v-model="form.notes"
            :placeholder="__('Glass thickness, finish, location…')"
          />
          <Link
            :label="__('Product Group')"
            doctype="Estimation Product Group"
            :value="form.product_group"
            @change="(v) => (form.product_group = v)"
            :onCreate="(v, close) => openNewProductGroupDialog(v, close, 'boq')"
            :filters="{ is_active: 1 }"
            :placeholder="__('Search / select group…')"
          />
          <Link
            :label="__('System Template (optional)')"
            doctype="Estimation Template"
            :value="form.system_template"
            @change="(v) => (form.system_template = v)"
            :onCreate="createTemplate"
            :placeholder="__('Search templates…')"
          />
          <p class="text-xs text-ink-gray-5 -mt-1">
            {{ __('Optional here. Estimation is created only when you click Create Estimate.') }}
          </p>
          <div class="grid grid-cols-2 gap-2">
            <FormControl type="number" :label="__('Qty')" v-model="form.qty" />
            <Link
              :label="__('Unit (commercial)')"
              doctype="UOM"
              :value="form.uom"
              @change="(v) => (form.uom = v)"
              :onCreate="createUom"
              :placeholder="__('Sqm, nos, RMT…')"
            />
          </div>
          <FormControl
            type="select"
            :label="__('Dim Unit')"
            :options="dimUnitOptions"
            v-model="form.dim_unit"
          />
          <div class="grid grid-cols-2 gap-2">
            <FormControl type="number" :label="__('Width (optional)')" v-model="form.width" />
            <FormControl type="number" :label="__('Height (optional)')" v-model="form.height" />
          </div>
          <div class="grid grid-cols-2 gap-2">
            <FormControl type="number" :label="__('Grids Nw')" v-model="form.grids_w" />
            <FormControl type="number" :label="__('Grids Nh')" v-model="form.grids_h" />
          </div>
          <p class="text-xs text-ink-gray-5">{{ sizeHint }}</p>
        </div>
      </template>
      <template #actions>
        <Button class="w-full" variant="solid" :loading="saving" @click="saveItem">
          {{ editingName ? __('Save') : __('Add') }}
        </Button>
      </template>
    </Dialog>

    <!-- Create Estimate / New Version picker -->
    <Dialog
      v-model="showEstimateDialog"
      :options="{ title: estimateAsVersion ? __('New Estimation Version') : __('Create Estimate') }"
    >
      <template #body-content>
        <div class="flex flex-col gap-3" v-if="estimateRow">
          <p class="text-sm text-ink-gray-7">{{ estimateRow.description }}</p>
          <Link
            :label="__('Product Group')"
            doctype="Estimation Product Group"
            :value="estimateForm.product_group"
            @change="(v) => (estimateForm.product_group = v)"
            :onCreate="(v, close) => openNewProductGroupDialog(v, close, 'estimate')"
            :filters="{ is_active: 1 }"
            :placeholder="__('Search / select group…')"
          />
          <Link
            :label="__('System Template *')"
            doctype="Estimation Template"
            :value="estimateForm.system_template"
            @change="(v) => (estimateForm.system_template = v)"
            :onCreate="createTemplateForEstimate"
            :placeholder="__('Search / select template…')"
          />
          <p class="text-xs text-ink-gray-5 -mt-1">
            {{ __('Required to create an estimation — select a product BOM template') }}
          </p>
          <FormControl
            type="select"
            :label="__('Dim Unit')"
            :options="dimUnitOptions"
            v-model="estimateForm.dim_unit"
          />
          <div class="rounded-md bg-surface-gray-2 p-3 text-sm text-ink-gray-7 space-y-1">
            <div>{{ __('Commercial Unit') }}: <b>{{ estimateRow.uom || 'Sqm' }}</b></div>
            <div>
              {{ __('Size') }}:
              <b>{{ estimateRow.width || 0 }}×{{ estimateRow.height || 0 }} {{ estimateForm.dim_unit }}</b>
              → <b>{{ metrePreview }}</b>
            </div>
            <div>{{ __('Approx. area') }}: <b>{{ areaPreview }}</b> {{ estimateRow.uom || 'Sqm' }}</div>
            <div v-if="perimeterPreview !== '—'" class="text-xs text-ink-gray-5">
              {{ __('Perimeter (for alu Weight lines)') }}: <b>{{ perimeterPreview }}</b>
            </div>
          </div>
        </div>
      </template>
      <template #actions>
        <Button
          class="w-full"
          variant="solid"
          :loading="!!busy"
          :disabled="!estimateForm.system_template"
          @click="confirmCreateEstimate"
        >
          {{ estimateAsVersion ? __('Create Version') : __('Create Estimate') }}
        </Button>
      </template>
    </Dialog>

    <!-- New Estimation Template (from Link Create New) -->
    <Dialog
      v-model="showNewTemplateDialog"
      :options="{ title: __('New System Template') }"
    >
      <template #body-content>
        <div class="flex flex-col gap-3">
          <p class="text-sm text-ink-gray-6">
            {{ __('Enter a name for the new template. You can add BOM cost lines after it is created.') }}
          </p>
          <FormControl
            :label="__('Template Name *')"
            v-model="newTemplateForm.name"
            :placeholder="__('e.g. Custom Spider Glazing')"
          />
          <Link
            :label="__('Product Group')"
            doctype="Estimation Product Group"
            :value="newTemplateForm.system_group"
            @change="(v) => (newTemplateForm.system_group = v)"
            :onCreate="(v, close) => openNewProductGroupDialog(v, close, 'template')"
            :filters="{ is_active: 1 }"
            :placeholder="__('Search / select group…')"
          />
        </div>
      </template>
      <template #actions>
        <Button
          class="w-full"
          variant="solid"
          :loading="creatingTemplate"
          :disabled="!newTemplateForm.name?.trim()"
          @click="confirmNewTemplate"
        >
          {{ __('Create Template') }}
        </Button>
      </template>
    </Dialog>

    <!-- New Product Group -->
    <Dialog
      v-model="showNewProductGroupDialog"
      :options="{ title: __('New Product Group') }"
    >
      <template #body-content>
        <div class="flex flex-col gap-3">
          <FormControl
            :label="__('Group Name *')"
            v-model="newProductGroupName"
            :placeholder="__('e.g. Canopy & Skylight')"
          />
        </div>
      </template>
      <template #actions>
        <Button
          class="w-full"
          variant="solid"
          :loading="creatingProductGroup"
          :disabled="!newProductGroupName?.trim()"
          @click="confirmNewProductGroup"
        >
          {{ __('Create Product Group') }}
        </Button>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { Button, Badge, Dialog, FormControl, call, createResource, toast } from 'frappe-ui'
import Link from '@/components/Controls/Link.vue'

const MM_DEFAULT_GROUPS = new Set(['Spider Glazing', 'Windows & Doors'])

const props = defineProps({
  dealId: { type: String, default: '' },
  leadId: { type: String, default: '' },
  parentDoctype: { type: String, default: '' },
  parentId: { type: String, default: '' },
})

const emit = defineEmits(['updated'])

const resolvedDoctype = computed(() => {
  if (props.parentDoctype) return props.parentDoctype
  if (props.leadId) return 'CRM Lead'
  return 'CRM Deal'
})

const resolvedId = computed(() => props.parentId || props.leadId || props.dealId)

const showDialog = ref(false)
const showEstimateDialog = ref(false)
const showNewTemplateDialog = ref(false)
const showNewProductGroupDialog = ref(false)
const creatingTemplate = ref(false)
const creatingProductGroup = ref(false)
const newTemplateTarget = ref('boq') // 'boq' | 'estimate'
const newProductGroupTarget = ref('boq') // 'boq' | 'estimate' | 'template'
const newTemplateForm = reactive({
  name: '',
  system_group: '',
})
const newProductGroupName = ref('')
const editingName = ref(null)
const saving = ref(false)
const busy = ref(null)
const estimateRow = ref(null)
const estimateAsVersion = ref(false)
const versionHistoryFor = ref(null)
const versionHistory = ref([])
const versionHistoryLoading = ref(false)

const form = reactive({
  item_no: '',
  section: '',
  description: '',
  notes: '',
  product_group: '',
  system_template: '',
  dim_unit: 'mm',
  width: 0,
  height: 0,
  grids_w: 1,
  grids_h: 1,
  qty: 1,
  uom: 'Sqm',
})

const estimateForm = reactive({
  product_group: '',
  system_template: '',
  dim_unit: 'mm',
})

const boq = createResource({
  url: 'cost_estimate.estimation.api.get_deal_boq',
  makeParams: () =>
    resolvedDoctype.value === 'CRM Lead'
      ? { lead: resolvedId.value }
      : { deal: resolvedId.value },
  auto: true,
})

const data = computed(
  () =>
    boq.data || {
      items: [],
      total_quoted: 0,
      total_cost: 0,
      count: 0,
      show_cost: false,
      by_section: [],
    },
)

const groupedItems = computed(() => {
  const items = data.value.items || []
  const map = new Map()
  for (const row of items) {
    const key = (row.section || row.product_group || 'Ungrouped').trim() || 'Ungrouped'
    if (!map.has(key)) map.set(key, [])
    map.get(key).push(row)
  }
  return Array.from(map.entries()).map(([key, rows]) => ({ key, rows }))
})

const showSectionColumn = computed(() => groupedItems.value.length <= 1)

const colCount = computed(() => {
  // #, [Section], Description, System, Size, Qty, Ver, Status, Quoted, [Cost], actions
  let n = 9
  if (showSectionColumn.value) n += 1
  if (data.value.show_cost) n += 1
  return n
})

const dimUnitOptions = [
  { label: 'mm', value: 'mm' },
  { label: 'm', value: 'm' },
]

const sizeHint = computed(() => {
  const du = form.dim_unit || 'mm'
  const w = Number(form.width) || 0
  const h = Number(form.height) || 0
  if (!w || !h) {
    return __(
      'Width/Height optional for lump SQM/RMT. When set, Dim Unit is separate from commercial Unit (e.g. mm openings + SQM quote).',
    )
  }
  const wm = du === 'm' ? w : w / 1000
  const hm = du === 'm' ? h : h / 1000
  const area = (wm * hm * (Number(form.qty) || 1)).toFixed(2)
  const perim = (2 * (wm + hm)).toFixed(3)
  return `${w}×${h} ${du} → ${wm.toFixed(3)}×${hm.toFixed(3)} m · ~${area} ${form.uom || 'Sqm'} · perimeter ${perim} m`
})

const metrePreview = computed(() => {
  if (!estimateRow.value) return '—'
  const du = estimateForm.dim_unit || 'mm'
  const w = Number(estimateRow.value.width) || 0
  const h = Number(estimateRow.value.height) || 0
  const wm = du === 'm' ? w : w / 1000
  const hm = du === 'm' ? h : h / 1000
  return `${wm.toFixed(3)}×${hm.toFixed(3)} m`
})

const areaPreview = computed(() => {
  if (!estimateRow.value) return '—'
  const du = estimateForm.dim_unit || 'mm'
  const w = Number(estimateRow.value.width) || 0
  const h = Number(estimateRow.value.height) || 0
  const qty = Number(estimateRow.value.qty) || 1
  const wm = du === 'm' ? w : w / 1000
  const hm = du === 'm' ? h : h / 1000
  return (wm * hm * qty).toFixed(2)
})

const perimeterPreview = computed(() => {
  if (!estimateRow.value) return '—'
  const du = estimateForm.dim_unit || 'mm'
  const w = Number(estimateRow.value.width) || 0
  const h = Number(estimateRow.value.height) || 0
  if (!w || !h) return '—'
  const wm = du === 'm' ? w : w / 1000
  const hm = du === 'm' ? h : h / 1000
  return `${(2 * (wm + hm)).toFixed(3)} m`
})

onMounted(() => {})
watch(resolvedId, () => boq.reload())
watch(
  () => form.product_group,
  (g) => {
    if (!editingName.value) {
      if (MM_DEFAULT_GROUPS.has(g)) form.dim_unit = 'mm'
      else if (g) form.dim_unit = 'm'
    }
    if (!form.section && g) form.section = g
  },
)

function fmt(v) {
  return Number(v || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })
}

function groupQuoted(rows) {
  return rows.reduce((s, r) => s + Number(r.quoted_value || 0), 0)
}

function descriptionTitle(row) {
  const parts = [row.description]
  if (row.notes) parts.push(row.notes)
  return parts.filter(Boolean).join('\n')
}

function isDraftEstimation(row) {
  if (!row?.estimation) return false
  return Number(row.estimation_docstatus ?? 0) !== 1
}

function displayStatus(row) {
  if (!row.estimation) return row.status || __('Draft')
  return isDraftEstimation(row) ? __('Estimating') : __('Estimated')
}

function statusTheme(row) {
  if (!row.estimation) return 'gray'
  return isDraftEstimation(row) ? 'orange' : 'green'
}

async function toggleVersionHistory(row) {
  if (versionHistoryFor.value === row.name) {
    versionHistoryFor.value = null
    versionHistory.value = []
    return
  }
  versionHistoryFor.value = row.name
  versionHistoryLoading.value = true
  versionHistory.value = []
  try {
    versionHistory.value =
      (await call('cost_estimate.estimation.api.get_boq_estimation_versions', {
        boq_item: row.name,
      })) || []
  } finally {
    versionHistoryLoading.value = false
  }
}

function openEstimationName(name) {
  if (name) window.open('/app/estimation/' + name, '_blank')
  versionHistoryFor.value = null
}

function resetForm() {
  Object.assign(form, {
    item_no: '',
    section: '',
    description: '',
    notes: '',
    product_group: '',
    system_template: '',
    dim_unit: 'mm',
    width: 0,
    height: 0,
    grids_w: 1,
    grids_h: 1,
    qty: 1,
    uom: 'Sqm',
  })
}

function openAdd() {
  editingName.value = null
  resetForm()
  showDialog.value = true
}

function openEdit(row) {
  editingName.value = row.name
  Object.assign(form, {
    item_no: row.item_no || '',
    section: row.section || '',
    description: row.description || '',
    notes: row.notes || '',
    product_group: row.product_group || '',
    system_template: row.system_template || '',
    dim_unit: row.dim_unit || 'mm',
    width: row.width || 0,
    height: row.height || 0,
    grids_w: row.grids_w || 1,
    grids_h: row.grids_h || 1,
    qty: row.qty || 1,
    uom: row.uom || 'Sqm',
  })
  showDialog.value = true
}

async function createUom(value, close) {
  const name = (typeof value === 'string' ? value : value?.label || value?.value || '').trim()
  if (!name) {
    toast.create({
      title: __('UOM name required'),
      text: __('Type a unit name in the search box, then click Create New'),
      icon: 'alert-triangle',
      iconClasses: 'text-ink-amber-3',
    })
    return
  }
  try {
    await call('cost_estimate.estimation.api.add_uom', { uom_name: name })
    form.uom = name
    if (close) close()
  } catch (e) {
    toast.create({
      title: __('Could not create UOM'),
      text: e?.messages?.[0] || e?.message || __('Please try again'),
      icon: 'x',
      iconClasses: 'text-ink-red-3',
    })
  }
}

function extractSearchName(value) {
  if (typeof value === 'string') return value.trim()
  if (value && typeof value === 'object') {
    return String(value.label || value.value || '').trim()
  }
  return ''
}

function createTemplate(value, close) {
  openNewTemplateDialog(value, close, 'boq', form.product_group || '')
}

function createTemplateForEstimate(value, close) {
  openNewTemplateDialog(value, close, 'estimate', estimateForm.product_group || '')
}

function openNewTemplateDialog(value, close, target, systemGroup) {
  if (close) close()
  newTemplateTarget.value = target
  newTemplateForm.name = extractSearchName(value)
  newTemplateForm.system_group = systemGroup || ''
  showNewTemplateDialog.value = true
}

async function confirmNewTemplate() {
  const name = (newTemplateForm.name || '').trim()
  if (!name) {
    toast.create({
      title: __('Template name required'),
      text: __('Enter a name for the new System Template'),
      icon: 'alert-triangle',
      iconClasses: 'text-ink-amber-3',
    })
    return
  }
  creatingTemplate.value = true
  try {
    const code = await call('cost_estimate.estimation.api.add_estimation_template', {
      template_name: name,
      system_group: newTemplateForm.system_group || null,
    })
    if (newTemplateTarget.value === 'estimate') {
      estimateForm.system_template = code
    } else {
      form.system_template = code
    }
    showNewTemplateDialog.value = false
    toast.create({
      title: __('Template created'),
      text: __('Opening the template so you can add BOM lines'),
      icon: 'check',
      iconClasses: 'text-ink-green-3',
    })
    if (code) window.open('/app/estimation-template/' + encodeURIComponent(code), '_blank')
  } catch (e) {
    toast.create({
      title: __('Could not create template'),
      text: e?.messages?.[0] || e?.message || __('Please try again'),
      icon: 'x',
      iconClasses: 'text-ink-red-3',
    })
  } finally {
    creatingTemplate.value = false
  }
}

function openNewProductGroupDialog(value, close, target) {
  if (close) close()
  newProductGroupTarget.value = target
  newProductGroupName.value = extractSearchName(value)
  showNewProductGroupDialog.value = true
}

async function confirmNewProductGroup() {
  const name = (newProductGroupName.value || '').trim()
  if (!name) {
    toast.create({
      title: __('Group name required'),
      text: __('Enter a name for the new Product Group'),
      icon: 'alert-triangle',
      iconClasses: 'text-ink-amber-3',
    })
    return
  }
  creatingProductGroup.value = true
  try {
    const group = await call('cost_estimate.estimation.api.add_product_group', {
      group_name: name,
    })
    if (newProductGroupTarget.value === 'estimate') {
      estimateForm.product_group = group
    } else if (newProductGroupTarget.value === 'template') {
      newTemplateForm.system_group = group
    } else {
      form.product_group = group
    }
    showNewProductGroupDialog.value = false
    toast.create({
      title: __('Product Group created'),
      text: group,
      icon: 'check',
      iconClasses: 'text-ink-green-3',
    })
  } catch (e) {
    toast.create({
      title: __('Could not create product group'),
      text: e?.messages?.[0] || e?.message || __('Please try again'),
      icon: 'x',
      iconClasses: 'text-ink-red-3',
    })
  } finally {
    creatingProductGroup.value = false
  }
}

async function saveItem() {
  if (!form.description) return
  saving.value = true
  try {
    if (editingName.value) {
      const res = await call('cost_estimate.estimation.api.update_boq_item', {
        name: editingName.value,
        fields: { ...form },
      })
      if (res?.action === 'needs_new_version') {
        toast.create({
          title: __('Submitted estimate'),
          text: __('Create a new version to re-estimate with the new size'),
          icon: 'alert-triangle',
          iconClasses: 'text-ink-amber-3',
        })
      } else if (res?.action === 'needs_estimate') {
        toast.create({
          title: __('Manual cost lines'),
          text: __('Open the estimate and click Estimate to refresh'),
          icon: 'alert-triangle',
          iconClasses: 'text-ink-amber-3',
        })
      }
    } else {
      const args = { ...form }
      if (resolvedDoctype.value === 'CRM Lead') {
        args.lead = resolvedId.value
      } else {
        args.deal = resolvedId.value
      }
      await call('cost_estimate.estimation.api.add_deal_boq_item', args)
    }
    showDialog.value = false
    boq.reload()
    emit('updated')
  } finally {
    saving.value = false
  }
}

function openCreateEstimate(row, asVersion = false) {
  estimateRow.value = row
  estimateAsVersion.value = asVersion
  estimateForm.product_group = row.product_group || ''
  // Prefill only when the stored value is a known template code/name.
  // Legacy Spaceki labels (e.g. "Stick Glazing - Site Glazed") must be re-picked.
  const tpl = row.system_template || ''
  estimateForm.system_template = /^[A-Za-z0-9][A-Za-z0-9._-]*$/.test(tpl) ? tpl : ''
  estimateForm.dim_unit =
    row.dim_unit || (MM_DEFAULT_GROUPS.has(row.product_group) ? 'mm' : 'm')
  showEstimateDialog.value = true
}

async function confirmCreateEstimate() {
  if (!estimateForm.system_template) {
    toast.create({
      title: __('Template required'),
      text: __('Select a System Template to start the estimation'),
      icon: 'alert-triangle',
      iconClasses: 'text-ink-amber-3',
    })
    return
  }
  const row = estimateRow.value
  busy.value = estimateAsVersion.value ? 'v-' + row.name : row.name
  try {
    const method = estimateAsVersion.value
      ? 'cost_estimate.estimation.api.create_estimation_version'
      : 'cost_estimate.estimation.api.make_estimation_from_boq_item'
    const name = await call(method, {
      boq_item: row.name,
      system_template: estimateForm.system_template,
      dim_unit: estimateForm.dim_unit,
      product_group: estimateForm.product_group || null,
    })
    showEstimateDialog.value = false
    boq.reload()
    emit('updated')
    if (name) window.open('/app/estimation/' + name, '_blank')
  } finally {
    busy.value = null
  }
}

function openEstimate(row) {
  if (row.estimation) window.open('/app/estimation/' + row.estimation, '_blank')
}
</script>
