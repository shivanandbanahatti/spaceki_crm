import { computed, watch } from 'vue'
import { createResource } from 'frappe-ui'

export function useRelatedCounts(doctype, getDocname) {
  const counts = createResource({
    url: 'spaceki_crm.api.record.get_related_counts',
    makeParams: () => ({
      doctype,
      name: typeof getDocname === 'function' ? getDocname() : getDocname,
    }),
    auto: false,
    transform(data) {
      // Ensure boq key always present for tab labels
      return {
        notes: 0,
        tasks: 0,
        calls: 0,
        attachments: 0,
        comments: 0,
        work: 0,
        quotations: 0,
        quotation_drafts: 0,
        boq: 0,
        ...(data || {}),
      }
    },
  })

  function refresh() {
    const name = typeof getDocname === 'function' ? getDocname() : getDocname
    if (!name) return
    counts.reload()
  }

  watch(
    () => (typeof getDocname === 'function' ? getDocname() : getDocname),
    (name) => {
      if (name) refresh()
    },
    { immediate: true },
  )

  function countLabel(label, key) {
    const n = counts.data?.[key]
    if (n == null && !counts.data) return __(label)
    return `${__(label)} (${n ?? 0})`
  }

  // Force dependents (tab computed) to track counts.data
  const data = computed(() => counts.data)

  return { counts, countLabel, data, refresh }
}
