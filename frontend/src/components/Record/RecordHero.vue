<template>
  <div class="border-b border-outline-gray-2 bg-surface-white">
    <div
      class="border-l-4 px-3 py-3 sm:px-6 sm:py-3.5"
      :class="accentClass"
    >
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div class="flex min-w-0 items-center gap-3">
          <slot name="avatar">
            <Avatar
              size="lg"
              class="size-11 shrink-0 shadow-sm ring-2 ring-white"
              :label="label || title"
              :image="image"
            />
          </slot>
          <div class="min-w-0">
            <div class="flex flex-wrap items-center gap-2">
              <h1 class="truncate text-lg font-semibold text-ink-gray-9 sm:text-xl">
                {{ title }}
              </h1>
              <Badge
                v-if="statusLabel"
                variant="subtle"
                :theme="statusTheme"
                :label="statusLabel"
              />
            </div>
            <button
              v-if="subtitle"
              type="button"
              class="mt-0.5 truncate text-xs text-ink-gray-5 hover:text-ink-gray-7"
              @click="$emit('copySubtitle')"
            >
              {{ subtitle }}
            </button>
            <p v-if="meta" class="mt-0.5 truncate text-xs font-medium text-ink-gray-6">
              {{ meta }}
            </p>
          </div>
        </div>
        <div class="flex flex-wrap items-center gap-1">
          <slot name="actions" />
        </div>
      </div>
      <slot name="below" />
    </div>
  </div>
</template>

<script setup>
import { Avatar, Badge } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  label: { type: String, default: '' },
  image: { type: String, default: '' },
  statusLabel: { type: String, default: '' },
  statusTheme: { type: String, default: 'gray' },
  meta: { type: String, default: '' },
})

defineEmits(['copySubtitle'])

const accentClass = computed(() => {
  const themes = {
    green: 'border-l-green-500 bg-green-50/40',
    red: 'border-l-red-500 bg-red-50/40',
    orange: 'border-l-orange-500 bg-orange-50/40',
    blue: 'border-l-blue-500 bg-blue-50/40',
    purple: 'border-l-violet-500 bg-violet-50/40',
    gray: 'border-l-surface-gray-6 bg-surface-gray-1/60',
  }
  return themes[props.statusTheme] || themes.gray
})
</script>
