import { ref, watch, unref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const DEFAULT_TAB = 'data'

const WORK_SUBTABS = {
  tasks: 'Tasks',
  events: 'Events',
  comments: 'Comments',
}

function resolveRecordId(recordId) {
  if (typeof recordId === 'function') return recordId()
  return unref(recordId)
}

export function useRecordTabManager(tabs, recordId) {
  const route = useRoute()
  const router = useRouter()

  function findTabIndex(tabName) {
    return tabs.value?.findIndex(
      (tab) => tab.name.toLowerCase() === tabName.toLowerCase(),
    )
  }

  function syncHash(tabName) {
    const hash = '#' + tabName.toLowerCase()
    if (route.hash !== hash) {
      router.replace({ ...route, hash })
    }
  }

  function changeTabTo(tabName) {
    const lower = tabName.toLowerCase()
    if (WORK_SUBTABS[lower]) {
      const workIndex = findTabIndex('Work')
      if (workIndex === -1) return
      tabIndex.value = workIndex
      syncHash(lower)
      return
    }
    const index = findTabIndex(tabName)
    if (index === -1) return
    tabIndex.value = index
  }

  function overviewIndex() {
    const index = findTabIndex(DEFAULT_TAB)
    return index === -1 ? 0 : index
  }

  function indexFromHash(hash) {
    const h = (hash || '').replace(/^#/, '').toLowerCase()
    if (WORK_SUBTABS[h]) {
      const workIndex = findTabIndex('Work')
      return workIndex === -1 ? overviewIndex() : workIndex
    }
    if (!h) return overviewIndex()
    const index = findTabIndex(h)
    return index === -1 ? overviewIndex() : index
  }

  const tabIndex = ref(indexFromHash(route.hash))

  function openOverview() {
    tabIndex.value = overviewIndex()
    syncHash(DEFAULT_TAB)
  }

  watch(tabIndex, (value) => {
    const currentTab = tabs.value?.[value]?.name
    if (!currentTab) return

    if (currentTab === 'Work') {
      const h = route.hash.slice(1).toLowerCase()
      if (Object.keys(WORK_SUBTABS).includes(h)) return
      syncHash('tasks')
      return
    }

    syncHash(currentTab)
  })

  watch(
    () => route.hash,
    (hash) => {
      const nextIndex = indexFromHash(hash)
      if (nextIndex !== tabIndex.value) {
        tabIndex.value = nextIndex
      }
    },
  )

  watch(
    () => resolveRecordId(recordId),
    (newId, oldId) => {
      if (oldId === undefined || newId !== oldId) {
        openOverview()
      }
    },
    { immediate: true },
  )

  return { tabIndex, changeTabTo }
}
