<template>
  <div class="admin-shell">
    <!-- 侧边栏 -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <h2 class="logo">🌙 星灵花园 CMS</h2>
      </div>
      <nav class="nav">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          custom
          v-slot="{ navigate, isExactActive, isActive }"
        >
          <button
            :class="{
              navItem: true,
              active: item.path === '/admin'
                ? isExactActive
                : isActive,
            }"
            @click="navigate"
          >
            <span class="icon">{{ item.icon }}</span>
            <span class="label">{{ item.label }}</span>
          </button>
        </router-link>
      </nav>
      <div class="sidebar-footer">
        <div class="admin-info" v-if="admin">
          <span class="admin-name">{{ admin.username }}</span>
          <span class="admin-role" v-if="admin.role">{{ admin.role }}</span>
        </div>
        <button class="logout" @click="logout">
          <span>退出登录</span>
        </button>
      </div>
    </aside>

    <!-- 主区 -->
    <main class="main">
      <header class="topbar">
        <div class="topbar-left">
          <h1 class="page-title">{{ currentTitle }}</h1>
          <span class="page-sub" v-if="currentSub">{{ currentSub }}</span>
        </div>
        <div class="topbar-right">
          <slot name="topbar-actions" />
        </div>
      </header>

      <section class="content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { clearAdminToken, getAdminToken } from "@/config/adminApi";

const route = useRoute();
const router = useRouter();

const admin = ref<{ username: string; role?: string } | null>(null);

const navItems = [
  { path: "/admin", label: "📊 数据统计", icon: "📊", title: "数据统计", sub: "系统总览" },
  { path: "/admin/users", label: "👤 用户管理", icon: "👤", title: "用户管理", sub: "查看 / 编辑 / 禁用用户" },
  { path: "/admin/diaries", label: "📔 星灵日记", icon: "📔", title: "星灵日记", sub: "审核 / 删除 / 隐藏" },
  { path: "/admin/reports", label: "📜 星语者报告", icon: "📜", title: "星语者报告", sub: "查看 / 删除" },
  { path: "/admin/audit", label: "📋 审计日志", icon: "📋", title: "审计日志", sub: "管理员操作记录" },
  { path: "/admin/settings", label: "⚙️ 系统设置", icon: "⚙️", title: "系统设置", sub: "站点配置 KV" },
];

const currentTitle = computed(() => {
  // 详情子路由匹配父级标题
  const match = navItems.find((n) => {
    if (n.path === "/admin") {
      return route.path === "/admin";
    }
    return route.path === n.path || route.path.startsWith(n.path + "/");
  });
  return match?.title || "星灵花园 CMS";
});

const currentSub = computed(() => {
  const match = navItems.find((n) => {
    if (n.path === "/admin") {
      return route.path === "/admin";
    }
    return route.path === n.path || route.path.startsWith(n.path + "/");
  });
  return match?.sub || "";
});

function logout() {
  clearAdminToken();
  router.push("/admin/login");
}

async function loadAdmin() {
  // 从 localStorage 简单恢复管理员信息（无独立 /me 时直接用 token 解析失败则跳过）
  const token = getAdminToken();
  if (!token) return;
  try {
    const payload = token.split(".")[1];
    if (!payload) return;
    const decoded = JSON.parse(atob(payload.replace(/-/g, "+").replace(/_/g, "/")));
    if (decoded?.sub) {
      admin.value = { username: decoded.sub, role: decoded.role };
    }
  } catch {
    // ignore
  }
}

onMounted(() => {
  loadAdmin();
});
</script>

<style scoped>
.admin-shell {
  display: flex;
  min-height: 100vh;
  background: #f7f5f2;
}
.sidebar {
  width: 220px;
  background: linear-gradient(180deg, #1a1a2e, #2d2d44);
  color: #f0e6d8;
  display: flex;
  flex-direction: column;
  padding: 20px 14px;
  flex-shrink: 0;
}
.sidebar-header {
  padding: 0 6px 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.logo {
  font-size: 15px;
  font-weight: 700;
  margin: 0;
  color: #f2a900;
}
.nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 16px 0;
}
.navItem {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 12px;
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.7);
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  text-align: left;
  transition: all 0.2s;
  font-family: inherit;
  width: 100%;
}
.navItem:hover {
  background: rgba(255, 255, 255, 0.05);
  color: #fff;
}
.navItem.active {
  background: rgba(242, 169, 0, 0.15);
  color: #f2a900;
}
.icon {
  font-size: 16px;
  width: 22px;
  text-align: center;
}
.label {
  flex: 1;
}
.sidebar-footer {
  padding-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.admin-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.04);
  font-size: 12px;
}
.admin-name {
  color: #f2a900;
  font-weight: 600;
}
.admin-role {
  color: rgba(255, 255, 255, 0.5);
  font-size: 11px;
}
.logout {
  width: 100%;
  padding: 10px 14px;
  border-radius: 12px;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: rgba(255, 255, 255, 0.7);
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
  font-family: inherit;
}
.logout:hover {
  background: rgba(255, 154, 139, 0.15);
  color: #ff9a8b;
}
.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow-x: hidden;
  min-width: 0;
}
.topbar {
  background: #fff;
  padding: 18px 28px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}
.topbar-left {
  display: flex;
  align-items: baseline;
  gap: 14px;
}
.topbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
}
.page-title {
  font-size: 18px;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
}
.page-sub {
  font-size: 13px;
  color: #6b7280;
}
.content {
  flex: 1;
  padding: 24px 28px;
  overflow-y: auto;
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>