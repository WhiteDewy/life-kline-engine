import { createRouter, createWebHistory } from "vue-router";
import Entry from "@/views/home/index.vue";

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "entry", component: Entry },
    {
      path: "/users",
      name: "users",
      component: () => import("@/views/Users/index.vue"),
    },
    {
      path: "/analysis/:type",
      name: "analysis",
      component: () => import("@/views/Analysis/index.vue"),
    },
    {
      path: "/reports/:id?",
      alias: ["/kline", "/LifeRhythm"],
      name: "report",
      component: () => import("@/views/Kline/index.vue"),
    },
    {
      path: "/monthly-return/:id?",
      name: "monthly-return",
      component: () => import("@/views/MonthlyReturn/index.vue"),
    },
    {
      path: "/history",
      name: "history",
      component: () => import("@/views/History/index.vue"),
    },
    {
      path: "/login",
      name: "login",
      component: () => import("@/views/Login/index.vue"),
    },
    {
      path: "/onboarding",
      name: "onboarding",
      component: () => import("@/views/Onboarding/index.vue"),
    },
    {
      path: "/spirit-garden",
      name: "spirit-garden",
      component: () => import("@/views/Wanxiang/index.vue"),
    },
    {
      path: "/spirit-garden/:planet",
      name: "spirit-detail",
      component: () => import("@/views/Wanxiang/index.vue"),
    },
  ],
});
