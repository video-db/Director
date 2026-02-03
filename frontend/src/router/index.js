import { createRouter, createWebHistory } from "vue-router";
import DefaultView from "../views/DefaultView.vue";
import ShareView from "../views/ShareView.vue";

const routes = [
  {
    path: "/",
    name: "Default",
    component: DefaultView,
  },
  {
    path: "/share/:sessionId",
    name: "Share",
    component: ShareView,
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
