import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { call, toast } from 'frappe-ui'

/**
 * Prev/next navigation for CRM Lead/Deal detail pages (Desk-style <>).
 */
export function useDocumentNav(doctype, getDocname, routeName, paramKey) {
  const router = useRouter()
  const loading = ref(false)

  async function go(prev) {
    const name = typeof getDocname === 'function' ? getDocname() : getDocname
    if (!name || loading.value) return
    loading.value = true
    try {
      const nextName = await call('frappe.desk.form.utils.get_next', {
        doctype,
        value: name,
        prev: prev ? 1 : 0,
        // omit empty filters — some clients drop [] and confuse get_query
        sort_order: 'desc',
        sort_field: 'modified',
      })
      if (!nextName) {
        toast.create({
          title: prev ? __('No previous record') : __('No next record'),
          icon: 'alert-circle',
          iconClasses: 'text-ink-gray-5',
        })
        return
      }
      await router.push({ name: routeName, params: { [paramKey]: nextName } })
    } catch (e) {
      const msg =
        e?.messages?.[0] || e?.message || __('Could not open the next record')
      toast.error(typeof msg === 'string' ? msg : __('Could not open the next record'))
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    goPrev: () => go(true),
    goNext: () => go(false),
  }
}
