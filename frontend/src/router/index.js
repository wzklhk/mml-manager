import { createRouter, createWebHistory } from 'vue-router'
import HomeLayout from '../layouts/HomeLayout.vue'
import ModuleLayout from '../layouts/ModuleLayout.vue'
import HomeView from '../views/Home/HomeView.vue'
import { appModules } from '../modules/registry'

export const routes = [
  { path: '/', component: HomeLayout, children: [
    { path: '', name: 'home', component: HomeView, meta: { title: 'workspace.home' } }
  ] },
  ...appModules.filter(module => module.enabled && module.path && module.routes)
    .map(module => ({
      path: module.path, component: ModuleLayout,
      meta: { moduleId: module.id }, children: module.routes
    })),
  { path: '/:pathMatch(.*)*', redirect: '/' }
]

// Resource base (/static/) is independent of the application URL root.
const router = createRouter({ history: createWebHistory('/'), routes })
export default router
