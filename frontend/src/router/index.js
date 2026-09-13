import { createRouter, createWebHashHistory } from "vue-router";
import HomeLayout from "../layouts/HomeLayout.vue";
import ModuleLayout from "../layouts/ModuleLayout.vue";
import HomeView from "../views/Home/HomeView.vue";
import { appModules } from "../modules/registry";

export const routes = [
  {
    path: "/",
    component: HomeLayout,
    children: [{ path: "", name: "home", component: HomeView, meta: { title: "workspace.home" } }],
  },
  ...appModules
    .filter((module) => module.enabled && module.path && module.routes)
    .map((module) => ({
      path: module.path,
      component: ModuleLayout,
      meta: { moduleId: module.id },
      children: module.routes,
    })),
  { path: "/:pathMatch(.*)*", redirect: "/" },
];

// Keep client-side routes after `#` so deployment does not require History API fallback.
const router = createRouter({ history: createWebHashHistory(), routes });
export default router;
