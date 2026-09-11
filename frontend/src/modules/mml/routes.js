export const mmlRoutes = [
  { path: '', redirect: '/mml/query' },
  {
    path: 'query', name: 'mml-query',
    component: () => import('../../views/Mml/MmlQueryView.vue'),
    meta: { title: 'workspace.query' }
  }
]
