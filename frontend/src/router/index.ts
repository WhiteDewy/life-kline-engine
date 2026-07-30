import { createRouter, createWebHistory } from "vue-router";
import type { RouteRecordRaw } from "vue-router";
import Entry from "@/views/home/index.vue";

const devOnlyRoutes: RouteRecordRaw[] = import.meta.env.DEV
  ? [
      {
        path: "/users",
        name: "users",
        component: () => import("@/views/Users/index.vue"),
      },
    ]
  : [];

// Sprint 7: 12星座灵生产入口 — 从 DEV-only 移到生产路由
const constellationRoute: RouteRecordRaw = {
  path: "/constellation-stories",
  name: "constellation-stories",
  component: () => import("@/views/ConstellationStories/index.vue"),
};

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "entry", component: Entry },
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
      path: "/transit-now",
      name: "transit-now",
      component: () => import("@/views/TransitNow/index.vue"),
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
      path: "/profile",
      name: "profile",
      component: () => import("@/views/Profile/index.vue"),
    },
    {
      path: "/transits/yearly/:reportId?",
      name: "transits-yearly",
      component: () => import("@/views/Transits/YearlyPage.vue"),
    },
    {
      path: "/transits/monthly/:reportId?",
      name: "transits-monthly",
      component: () => import("@/views/Transits/MonthlyPage.vue"),
    },
    {
      path: "/transits/weekly/:reportId?",
      name: "transits-weekly",
      component: () => import("@/views/Transits/WeeklyPage.vue"),
    },
    constellationRoute,
    ...devOnlyRoutes,
  ],
});

// ── 路由守卫（主应用，Admin CMS 已迁移到独立项目 admin-frontend/） ──
router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem("lk_token");

  // 不需要登录即可访问的公开页面
  const PUBLIC_PATHS = ["/login", "/transit-now"];
  if (PUBLIC_PATHS.includes(to.path)) {
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
