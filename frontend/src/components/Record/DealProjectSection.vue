<template>
  <div
    v-if="project.data?.project || project.loading"
    class="overflow-hidden rounded-lg border border-outline-gray-2 bg-surface-white shadow-sm"
  >
    <div
      class="flex items-center justify-between gap-2 border-b border-violet-100 bg-violet-50/60 px-3 py-2"
    >
      <div class="flex items-center gap-2 text-sm font-semibold text-violet-900">
        <span class="inline-block size-2 rounded-full bg-violet-500" />
        {{ __('Project') }}
      </div>
    </div>

    <div
      v-if="project.loading && !project.data?.project"
      class="flex items-center justify-center gap-2 px-3 py-4 text-xs text-ink-gray-5"
    >
      <LoadingIndicator class="h-4 w-4" />
      {{ __('Loading...') }}
    </div>

    <div
      v-else-if="project.data?.project"
      class="flex items-center justify-between gap-3 px-3 py-2.5"
    >
      <a
        :href="project.data.url"
        target="_blank"
        class="min-w-0 flex-1 no-underline"
      >
        <div class="truncate text-sm font-medium text-ink-gray-9">
          {{ project.data.project }}
        </div>
        <div class="mt-0.5 text-xs text-ink-gray-5">
          {{ __('Linked execution project') }}
        </div>
      </a>
      <a
        :href="project.data.url"
        target="_blank"
        class="shrink-0 text-xs font-medium text-violet-700 no-underline hover:underline"
      >
        {{ __('Open') }}
      </a>
    </div>
  </div>
</template>

<script setup>
import { createResource, LoadingIndicator } from 'frappe-ui'
import { onBeforeUnmount, onMounted, watch } from 'vue'
import { globalStore } from '@/stores/global'

const props = defineProps({
  dealId: { type: String, required: true },
})

const { $socket } = globalStore()

const project = createResource({
  url: 'cost_estimate.estimation.project_from_deal.get_deal_project_action',
  makeParams: () => ({ crm_deal: props.dealId }),
  auto: false,
})

function onDealProjectCreated(data) {
  if (data?.deal === props.dealId) project.reload()
}

watch(
  () => props.dealId,
  (id) => {
    if (id) project.reload()
  },
  { immediate: true },
)

onMounted(() => {
  $socket.on('deal_project_created', onDealProjectCreated)
})

onBeforeUnmount(() => {
  $socket.off('deal_project_created', onDealProjectCreated)
})
</script>
