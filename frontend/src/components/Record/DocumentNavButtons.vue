<template>
  <div class="flex items-center gap-0.5 border-l border-outline-gray-2 pl-2 ml-1">
    <button
      type="button"
      class="inline-flex size-7 items-center justify-center rounded-md text-ink-gray-7 hover:bg-surface-gray-2 hover:text-ink-gray-9 disabled:opacity-40"
      :title="__('Previous')"
      :aria-label="__('Previous')"
      :disabled="loading"
      @click="goPrev"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
        class="size-4"
      >
        <polyline points="15 18 9 12 15 6" />
      </svg>
    </button>
    <button
      type="button"
      class="inline-flex size-7 items-center justify-center rounded-md text-ink-gray-7 hover:bg-surface-gray-2 hover:text-ink-gray-9 disabled:opacity-40"
      :title="__('Next')"
      :aria-label="__('Next')"
      :disabled="loading"
      @click="goNext"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
        class="size-4"
      >
        <polyline points="9 18 15 12 9 6" />
      </svg>
    </button>
  </div>
</template>

<script setup>
import { useDocumentNav } from '@/composables/useDocumentNav'

const props = defineProps({
  doctype: { type: String, required: true },
  docname: { type: String, required: true },
  routeName: { type: String, required: true },
  paramKey: { type: String, required: true },
})

const { loading, goPrev, goNext } = useDocumentNav(
  props.doctype,
  () => props.docname,
  props.routeName,
  props.paramKey,
)
</script>
