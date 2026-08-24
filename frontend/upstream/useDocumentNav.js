// Stock FCRM has no useDocumentNav composable.
// Spaceki CRM provides this; removed from FCRM tree on frontend restore.
export function useDocumentNav() {
  throw new Error('useDocumentNav is a Spaceki CRM override')
}
