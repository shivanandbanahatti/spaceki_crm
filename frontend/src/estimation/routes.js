// Estimation route group. Merge these into the app router (see README.md).
export const estimationRoutes = [
  {
    path: '/estimates',
    name: 'EstimateList',
    component: () => import('./pages/EstimateList.vue'), // list view — build alongside CRM's list pattern
  },
  {
    path: '/estimate/new',
    name: 'EstimateNew',
    component: () => import('./pages/EstimateNew.vue'),
  },
  {
    path: '/estimate/:name',
    name: 'EstimateBuilder',
    component: () => import('./pages/EstimateBuilder.vue'),
    props: true,
  },
]
