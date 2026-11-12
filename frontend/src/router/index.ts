import { createRouter, createWebHistory } from "vue-router";

import AppLayout from "@/layouts/AppLayout.vue";
import { useConfigStore } from "@/stores/config";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      component: AppLayout,
      children: [
        {
          path: "",
          name: "home",
          component: () => import("@/pages/HomePage.vue"),
        },
        {
          path: "chat/:sessionId",
          name: "chat",
          component: () => import("@/pages/ChatPage.vue"),
        },
        {
          path: "collection/:collectionId",
          name: "collection",
          component: () => import("@/pages/CollectionPage.vue"),
        },
        {
          path: "collection/:collectionId/video/:videoId",
          name: "video",
          component: () => import("@/pages/VideoPage.vue"),
        },
        {
          path: "setup",
          name: "setup",
          component: () => import("@/pages/SetupPage.vue"),
        },
        {
          path: ":pathMatch(.*)*",
          name: "not-found",
          component: () => import("@/pages/NotFoundPage.vue"),
        },
      ],
    },
  ],
});

// Until the backend reports a complete setup, every route lands on /setup.
router.beforeEach(async (to) => {
  const config = useConfigStore();
  await config.loadConfig();
  if (!config.isSetupComplete && to.name !== "setup") {
    return { name: "setup", query: { redirect: to.fullPath } };
  }
  if (config.isSetupComplete && to.name === "setup") {
    return (to.query.redirect as string) || { name: "home" };
  }
});

export default router;
