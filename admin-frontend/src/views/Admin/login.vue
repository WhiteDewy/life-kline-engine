<template>
  <div class="admin-login">
    <div class="login-card">
      <h1 class="logo">🌙 星灵花园 · CMS</h1>
      <p class="subtitle">管理员登录</p>

      <form @submit.prevent="handleLogin" class="form">
        <label class="lbl">
          <span>账号</span>
          <input
            v-model="username"
            type="text"
            placeholder="管理员账号"
            autocomplete="username"
          />
        </label>
        <label class="lbl">
          <span>密码</span>
          <input
            v-model="password"
            type="password"
            placeholder="管理员密码"
            autocomplete="current-password"
          />
        </label>

        <p v-if="error" class="error">{{ error }}</p>

        <button type="submit" class="submit" :disabled="loading">
          {{ loading ? "登录中..." : "登录" }}
        </button>
      </form>

      <p class="hint">
        默认账号: <code>admin</code> / 密码: <code>admin@2026</code>（首次启动自动创建）
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import axios from "axios";
import { setAdminToken } from "@/config/adminApi";

const router = useRouter();
const username = ref("admin");
const password = ref("admin@2026");
const error = ref("");
const loading = ref(false);

async function handleLogin() {
  if (!username.value || !password.value) {
    error.value = "请输入账号和密码";
    return;
  }
  error.value = "";
  loading.value = true;
  try {
    const res = await axios.post("/api/admin/login", {
      username: username.value,
      password: password.value,
    });
    if (res.data?.data?.token) {
      setAdminToken(res.data.data.token);
      router.push("/admin");
    } else {
      error.value = res.data?.detail || "登录失败";
    }
  } catch (e: any) {
    error.value = e?.response?.data?.detail || "网络错误，请稍后再试";
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.admin-login {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a1a2e, #2d2d44);
  padding: 20px;
}
.login-card {
  width: 100%;
  max-width: 420px;
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(16px);
  border-radius: 24px;
  padding: 36px 32px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.4);
  color: #f0e6d8;
}
.logo {
  font-size: 22px;
  font-weight: 700;
  margin: 0 0 8px;
  text-align: center;
  color: #f2a900;
}
.subtitle {
  text-align: center;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
  margin: 0 0 24px;
}
.form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.lbl {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
}
.lbl input {
  padding: 12px 14px;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(255, 255, 255, 0.05);
  color: #f0e6d8;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}
.lbl input:focus {
  border-color: #f2a900;
}
.submit {
  margin-top: 6px;
  padding: 13px 20px;
  border-radius: 14px;
  background: linear-gradient(135deg, #f2a900, #ff9a8b);
  border: none;
  color: #1a1a2e;
  font-weight: 700;
  font-size: 15px;
  cursor: pointer;
  letter-spacing: 1px;
  transition: all 0.2s;
}
.submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.submit:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 24px rgba(255, 154, 139, 0.4);
}
.error {
  font-size: 13px;
  color: #ff7373;
  margin: 0;
  text-align: center;
}
.hint {
  margin-top: 24px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
  text-align: center;
  line-height: 1.6;
}
.hint code {
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.08);
  font-family: monospace;
}
</style>
