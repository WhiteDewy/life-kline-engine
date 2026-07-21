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
    {
      path: "/profile",
      name: "profile",
      component: () => import("@/views/Profile/index.vue"),
    },
  ],
});

// ── 路由守卫 ──
const PUBLIC_ROUTES = ["/login"];

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
