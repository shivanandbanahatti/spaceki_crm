<template>
  <div
    v-if="quotations.data?.length || quotations.loading || action.data"
    class="overflow-hidden rounded-lg border border-outline-gray-2 bg-surface-white shadow-sm"
  >
    <div
      class="flex items-center justify-between gap-2 border-b border-sky-100 bg-sky-50/60 px-3 py-2"
    >
      <div class="flex items-center gap-2 text-sm font-semibold text-sky-900">
        <span class="inline-block size-2 rounded-full bg-sky-500" />
        {{ __('Quotations') }}
        <span
          v-if="quotations.data?.length"
          class="rounded-full bg-sky-100 px-1.5 py-0.5 text-xs font-medium text-sky-800"
        >
          {{ quotations.data.length }}
        </span>
      </div>
      <button
        v-if="action.data?.can_new_version"
        type="button"
        class="rounded-md bg-sky-600 px-2.5 py-1 text-xs font-semibold text-white hover:bg-sky-700 disabled:opacity-50"
        :disabled="creating"
        @click="createVersion"
      >
        {{ creating ? __('Creating…') : __('New Version') }}
      </button>
      <span
        v-else-if="action.data?.has_draft"
        class="text-xs font-medium text-orange-700"
      >
        {{ __('Open Draft V{0} below', [draftVersionLabel]) }}
      </span>
    </div>

    <div
      v-if="quotations.loading && !quotations.data?.length"
      class="flex items-center justify-center gap-2 px-3 py-4 text-xs text-ink-gray-5"
    >
      <LoadingIndicator class="h-4 w-4" />
      {{ __('Loading...') }}
    </div>

    <ul v-else class="divide-y divide-outline-gray-1">
      <li
        v-for="row in quotations.data"
        :key="row.name"
        class="flex items-center justify-between gap-3 px-3 py-2.5 hover:bg-surface-gray-1"
      >
        <a
          :href="row.url"
          target="_blank"
          class="min-w-0 flex-1 no-underline"
        >
          <div class="flex flex-wrap items-center gap-2 truncate text-sm font-medium text-ink-gray-9">
            <span>{{ row.name }}</span>
            <span
              v-if="row.quotation_version"
              class="rounded bg-indigo-50 px-1.5 py-0.5 text-xs font-semibold text-indigo-800"
            >
              V{{ row.quotation_version }}
            </span>
            <span
              v-if="row.is_latest_quotation"
              class="rounded bg-sky-50 px-1.5 py-0.5 text-xs font-medium text-sky-800"
            >
              {{ __('Latest') }}
            </span>
          </div>
          <div class="mt-0.5 flex flex-wrap items-center gap-2 text-xs text-ink-gray-5">
            <span
              class="rounded px-1.5 py-0.5 font-medium"
              :class="
                row.docstatus === 0
                  ? 'bg-orange-50 text-orange-700'
                  : 'bg-green-50 text-green-700'
              "
            >
              {{ row.docstatus_label || (row.docstatus === 0 ? __('Draft') : __('Submitted')) }}
            </span>
            <span v-if="row.status">{{ row.status }}</span>
            <span v-if="row.grand_total != null">
              {{ formatMoney(row.grand_total, row.currency) }}
            </span>
          </div>
        </a>
        <a
          :href="row.url"
          target="_blank"
          class="shrink-0 text-xs font-medium text-sky-700 no-underline hover:underline"
        >
          {{ __('Open') }}
        </a>
      </li>
    </ul>

    <p
      v-if="hintText"
      class="border-t border-outline-gray-1 bg-surface-gray-1 px-3 py-2 text-xs text-ink-gray-6"
    >
      {{ hintText }}
    </p>
  </div>
</template>

<script setup>
import { createResource, LoadingIndicator, toast } from 'frappe-ui'
import { computed, ref, watch } from 'vue'

const props = defineProps({
  dealId: { type: String, required: true },
})

const creating = ref(false)

const quotations = createResource({
  url: 'cost_estimate.estimation.api.get_deal_quotations',
  makeParams: () => ({ crm_deal: props.dealId }),
  auto: false,
})

const action = createResource({
  url: 'cost_estimate.estimation.api.get_deal_quotation_action',
  makeParams: () => ({ crm_deal: props.dealId }),
  auto: false,
})

watch(
  () => props.dealId,
  (id) => {
    if (id) {
      quotations.reload()
      action.reload()
    }
  },
  { immediate: true },
)

const draftVersionLabel = computed(() => {
  const draftName = action.data?.draft
  const row = (quotations.data || []).find((r) => r.name === draftName)
  return row?.quotation_version || '2'
})

const hintText = computed(() => {
  if (action.data?.has_draft) {
    return __(
      'A Draft quotation already exists (with GST). Open it, edit rate/discount if needed, then Submit. After submit you can create V3.',
    )
  }
  if (action.data?.can_new_version) {
    return __(
      'Click New Version to create the next quotation from current Estimations (keeps old versions for history).',
    )
  }
  return ''
})

function formatMoney(value, currency) {
  if (value === undefined || value === null) return ''
  try {
    return Number(value).toLocaleString(undefined, {
      style: currency ? 'currency' : 'decimal',
      currency: currency || undefined,
      maximumFractionDigits: 2,
    })
  } catch {
    return Number(value).toLocaleString()
  }
}

async function createVersion() {
  if (!props.dealId || creating.value) return
  creating.value = true
  try {
    const url = await createResource({
      url: 'cost_estimate.estimation.api.get_quotation_url_from_deal',
      makeParams: () => ({
        crm_deal: props.dealId,
        force_new_version: 1,
      }),
    }).fetch()
    toast.success(__('Quotation version created'))
    quotations.reload()
    action.reload()
    if (url) window.open(url, '_blank')
  } catch (e) {
    toast.error(e?.messages?.[0] || e?.message || __('Could not create quotation version'))
  } finally {
    creating.value = false
  }
}
</script>
