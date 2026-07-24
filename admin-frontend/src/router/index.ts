import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      redirect: "/admin",
    },
    {
      path: "/admin/login",
      name: "admin-login",
      component: () => import("@/views/Admin/login.vue"),
    },
    {
      path: "/admin",
      component: () => import("@/views/Admin/AdminLayout.vue"),
      children: [
        {
          path: "",
          name: "admin-dashboard",
          component: () => import("@/views/Admin/Dashboard.vue"),
        },
        {
          path: "users",
          name: "admin-users",
          component: () => import("@/views/Admin/users/index.vue"),
        },
        {
          path: "users/:id",
          name: "admin-user-detail",
          component: () => import("@/views/Admin/users/Detail.vue"),
        },
        {
          path: "diaries",
          name: "admin-diaries",
          component: () => import("@/views/Admin/diaries/index.vue"),
        },
        {
          path: "diaries/:id",
          name: "admin-diary-detail",
          component: () => import("@/views/Admin/diaries/Detail.vue"),
        },
        {
          path: "reports",
          name: "admin-reports",
          component: () => import("@/views/Admin/reports/index.vue"),
        },
        {
          path: "reports/:id",
          name: "admin-report-detail",
          component: () => import("@/views/Admin/reports/Detail.vue"),
        },
        {
          path: "audit",
          name: "admin-audit",
          component: () => import("@/views/Admin/audit/index.vue"),
        },
        {
          path: "settings",
          name: "admin-settings",
          component: () => import("@/views/Admin/settings/index.vue"),
        },
      ],
    },
  ],
});

// ── 路由守卫 ── Admin CMS 独立鉴权
router.beforeEach((to, _from, next) => {
  if (to.path === "/admin/login") {
    next();
    return;
  }
  const adminToken = localStorage.getItem("lk_admin_token");
  if (!adminToken) {
    next(`/admin/login?redirect=${encodeURIComponent(to.fullPath)}`);
    return;
  }
  next();
});

export default router;
