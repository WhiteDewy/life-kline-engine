<template>
  <div class="settings">
    <div class="card">
      <h3>系统配置 (KV)</h3>
      <p class="hint">常用的站点开关可以在这里维护。比如：每日一问开关、AI 增强开关、测试手机号白名单等。</p>

      <div class="kv-list">
        <div v-for="s in settings" :key="s.key" class="kv-row">
          <span class="key">{{ s.key }}</span>
          <input v-model="editValues[s.key]" class="val" />
          <button class="btn ghost" @click="save(s.key)">保存</button>
          <span class="updated">{{ formatTime(s.updated_at) }}</span>
        </div>
        <div v-if="settings.length === 0" class="empty">
          暂无设置项，可以新增 KV 用于站点开关。
        </div>
      </div>

      <h3>新增 KV</h3>
      <div class="form">
        <input v-model="newKey" placeholder="key" class="input" />
        <input v-model="newValue" placeholder="value" class="input" />
        <button class="btn" @click="add">添加</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import adminApi from "@/config/adminApi";

const settings = ref<any[]>([]);
const editValues = ref<Record<string, string>>({});
const newKey = ref("");
const newValue = ref("");

async function load() {
  try {
    const res = await adminApi.get("/settings");
    if (res.data?.status === "success") {
      settings.value = res.data.data || [];
      for (const s of settings.value) {
        editValues.value[s.key] = s.value;
      }
    }
  } catch {
    settings.value = [];
  }
}

async function save(key: string) {
  try {
    await adminApi.put("/settings", {
      key,
      value: editValues.value[key] || "",
    });
    await load();
    alert("已保存");
  } catch {
    alert("保存失败");
  }
}

async function add() {
  if (!newKey.value) {
    alert("请输入 key");
    return;
  }
  try {
    await adminApi.put("/settings", {
      key: newKey.value,
      value: newValue.value,
    });
    newKey.value = "";
    newValue.value = "";
    await load();
  } catch {
    alert("添加失败");
  }
}

function formatTime(s: string) {
  if (!s) return "";
  return "更新于 " + s.slice(0, 16).replace("T", " ");
}

onMounted(load);
</script>

<style scoped>
.settings {
  background: #fff;
  border-radius: 18px;
  padding: 24px;
  border: 1px solid rgba(0, 0, 0, 0.04);
}
h3 {
  font-size: 14px;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 8px;
}
.hint {
  font-size: 12px;
  color: #6b7280;
  margin: 0 0 16px;
}
.kv-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 32px;
}
.kv-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.key {
  min-width: 180px;
  font-weight: 600;
  font-size: 13px;
  color: #1f2937;
  font-family: monospace;
}
.val {
  flex: 1;
  max-width: 320px;
  padding: 7px 10px;
  border-radius: 8px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  font-size: 13px;
  outline: none;
  font-family: monospace;
}
.btn {
  padding: 7px 14px;
  border-radius: 8px;
  border: none;
  background: #1f2937;
  color: #fff;
  cursor: pointer;
  font-size: 12px;
  font-family: inherit;
}
.btn.ghost {
  background: transparent;
  color: #6b7280;
  border: 1px solid rgba(0, 0, 0, 0.1);
}
.updated {
  font-size: 11px;
  color: #9ca3af;
  margin-left: 8px;
}
.empty {
  padding: 16px;
  text-align: center;
  color: #9ca3af;
  font-size: 13px;
}
.form {
  display: flex;
  gap: 8px;
}
.input {
  flex: 1;
  padding: 8px 12px;
  border-radius: 10px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  font-size: 13px;
  outline: none;
  font-family: monospace;
}
</style>
