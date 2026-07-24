import { createRouter, createWebHistory } from "vue-router";
import Entry from "@/views/home/index.vue";

const router = createRouter({
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
      path: "/my-chart",
      name: "my-chart",
      component: () => import("@/views/MyChart/index.vue"),
    },
    {
      path: "/natal-chart/:reportId",
      name: "natal-chart",
      component: () => import("@/views/NatalChart/index.vue"),
      meta: { requiresAuth: true },
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
      path: "/chat/:planet",
      name: "spirit-chat",
      component: () => import("@/views/Chat/index.vue"),
    },
    {
      path: "/diary",
      name: "spirit-diary",
      component: () => import("@/views/Diary/index.vue"),
    },
    {
      path: "/spirit-garden",
      name: "spirit-garden",
      component: () => import("@/views/Garden/index.vue"),
    },
    {
      path: "/spirit-garden/history",
      name: "garden-history",
      component: () => import("@/views/Garden/index.vue"),
    },
    {
      path: "/spirit-garden/:planet",
      name: "spirit-detail",
      component: () => import("@/views/Garden/index.vue"),
    },
    {
      path: "/constellation-stories",
      name: "constellation-stories",
      component: () => import("@/views/ConstellationStories/index.vue"),
    },
    {
      path: "/profile",
      name: "profile",
      component: () => import("@/views/Profile/index.vue"),
    },
  ],
});

// ── 路由守卫（主应用，Admin CMS 已迁移到独立项目 admin-frontend/） ──
router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem("lk_token");

  if (to.path === "/login") {
    // 已登录用户不需要再看登录页
    if (token) {
      next("/");
    } else {
      next();
    }
    return;
  }

  // 除 /login 外的所有路由需要鉴权
  if (!token) {
    next(`/login?redirect=${encodeURIComponent(to.fullPath)}`);
    return;
  }

  next();
});

export default router;
