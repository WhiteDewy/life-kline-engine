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
  ],
});
