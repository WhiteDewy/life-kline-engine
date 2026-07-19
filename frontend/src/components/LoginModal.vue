<template>
  <Teleport to="body">
    <div v-if="visible" class="overlay" @click.self="$emit('close')">
      <div class="card">
        <h3 class="title">登录</h3>
        <p class="hint">用手机号登录，保存你的报告和记录</p>

        <el-input
          v-model="phone"
          placeholder="输入手机号"
          size="large"
          :disabled="sending"
        />

        <div class="codeRow">
          <el-input
            v-model="code"
            placeholder="验证码"
            size="large"
            :disabled="sending"
            @keyup.enter="doLogin"
          />
          <el-button
            :disabled="!canSend || countdown > 0"
            :loading="sending"
            @click="doSend"
          >
            {{ countdown > 0 ? `${countdown}s` : "获取验证码" }}
          </el-button>
        </div>

        <el-button
          type="primary"
          size="large"
          :loading="verifying"
          :disabled="!phone || !code"
          class="loginBtn"
          @click="doLogin"
        >
          登录
        </el-button>

        <p class="note">开发模式：验证码会打印在服务器控制台</p>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { useAuth } from "@/utils/auth";

defineProps<{ visible: boolean }>();
const emit = defineEmits<{ close: []; loggedIn: [] }>();

const { sendCode, verifyCode } = useAuth();

const phone = ref("");
const code = ref("");
const sending = ref(false);
const verifying = ref(false);
const countdown = ref(0);

const canSend = computed(() => phone.value.length >= 10 && !sending.value);

let timer: any = null;
async function doSend() {
  sending.value = true;
  try {
    await sendCode(phone.value);
    countdown.value = 60;
    timer = setInterval(() => {
      countdown.value--;
      if (countdown.value <= 0) clearInterval(timer);
    }, 1000);
  } catch (e: any) {
    alert(e?.response?.data?.detail || "发送失败");
  }
  sending.value = false;
}

async function doLogin() {
  verifying.value = true;
  try {
    await verifyCode(phone.value, code.value);
    emit("loggedIn");
    emit("close");
  } catch (e: any) {
    alert(e?.response?.data?.detail || "验证码错误");
  }
  verifying.value = false;
}
</script>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(6px);
}
.card {
  width: 380px;
  max-width: 90vw;
  padding: 30px 28px;
  border-radius: 24px;
  background: #0f172a;
  border: 1px solid rgba(0,0,0,0.06);
  display: grid;
  gap: 16px;
}
.title {
  margin: 0;
  color: #4a3728;
  font-size: 22px;
}
.hint,
.note {
  margin: 0;
  color: #64748b;
  font-size: 13px;
}
.codeRow {
  display: flex;
  gap: 10px;
}
.codeRow .el-button {
  white-space: nowrap;
}
.loginBtn {
  width: 100%;
}
</style>
