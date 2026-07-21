<template>
  <div class="login-page">
    <!-- ═══ 柔光背景层 ═══ -->
    <canvas ref="particleCanvas" class="particle-canvas"></canvas>
    <div class="glow glow--top"></div>
    <div class="glow glow--mid"></div>
    <div class="glow glow--bottom"></div>

    <!-- ═══ 主内容 ═══ -->
    <div class="login-body">
      <!-- ── 水晶球 ── -->
      <div class="crystal">
        <div class="crystal-body">
          <div class="crystal-core"></div>
          <div class="crystal-ring c-ring--1"></div>
          <div class="crystal-ring c-ring--2"></div>
        </div>
        <div class="crystal-aura"></div>
        <span v-for="i in 6" :key="i" class="c-spark" :style="sparkStyle(i)"></span>
      </div>

      <!-- ── 品牌 ── -->
      <div class="brand">
        <h1 class="brand-title">
          <span v-for="(c, i) in '星灵花园'" :key="i" class="brand-char" :style="{ animationDelay: 0.3 + i * 0.07 + 's' }">{{ c }}</span>
        </h1>
        <p class="brand-sub">十颗星辰，在你的花园里苏醒</p>
      </div>

      <!-- ── 一键登录 ── -->
      <div class="card" v-if="loginMode === 'oneclick'">
        <div class="phone-box">
          <span class="prefix">+86</span>
          <span class="sep"></span>
          <input v-model="phone" class="phone-inp" type="tel" maxlength="11" placeholder="请输入手机号" @input="onPhoneInput" />
        </div>

        <button class="main-btn" :class="{ 'main-btn--dev': isDevBypass }" :disabled="!canOneClick || oneClicking" @click="doOneClickLogin">
          <span v-if="oneClicking" class="loader"></span>
          <span v-else>{{ isDevBypass ? '进入花园' : '一键登录' }}</span>
        </button>

        <button class="link-btn" @click="loginMode = 'sms'">其他方式登录</button>
      </div>

      <!-- ── 验证码登录 ── -->
      <div class="card" v-else>
        <div class="phone-box">
          <span class="prefix">+86</span>
          <span class="sep"></span>
          <input v-model="phone" class="phone-inp" type="tel" maxlength="11" placeholder="请输入手机号" />
        </div>

        <div class="code-row">
          <input v-model="code" class="code-inp" type="text" maxlength="6" placeholder="验证码" :disabled="isDevBypass" @keyup.enter="doSmsLogin" />
          <button class="send-btn" :disabled="!canSend || countdown > 0 || isDevBypass" @click="doSendCode">
            {{ countdown > 0 ? `${countdown}s` : '获取验证码' }}
          </button>
        </div>

        <button v-if="isDevBypass" class="main-btn main-btn--dev" :disabled="!agreed || verifying" @click="devDirectLogin">
          直接进入花园
        </button>
        <button v-else class="main-btn" :disabled="!canLogin || verifying" @click="doSmsLogin">
          <span v-if="verifying" class="loader"></span><span v-else>登录</span>
        </button>

        <button class="link-btn" @click="loginMode = 'oneclick'">返回一键登录</button>
      </div>

      <!-- ── 协议 ── -->
      <div class="agree">
        <div class="agree-dot" :class="{ on: agreed }" @click="agreed = !agreed"><span v-if="agreed">✓</span></div>
        <span class="agree-text">同意
          <span class="agree-link" @click.stop="showAgreement('user')">《用户协议》</span>和
          <span class="agree-link" @click.stop="showAgreement('privacy')">《隐私政策》</span>
        </span>
      </div>

      <!-- ── 协议弹窗 ── -->
      <Teleport to="body">
        <transition name="modal">
          <div v-if="agreementType" class="modal-mask" @click.self="agreementType = ''">
            <div class="modal-card agreement-card">
              <div class="modal-icon">{{ agreementType === 'user' ? '📋' : '🔒' }}</div>
              <div class="modal-title">{{ agreementType === 'user' ? '用户协议' : '隐私政策' }}</div>
              <div class="agreement-body">
                <p v-if="agreementType === 'user'">
                  用户协议内容将在后续版本完善。<br /><br />
                  使用星灵花园即表示你同意遵守相关服务条款。<br />
                  我们致力于保护你的数据安全和隐私权利。
                </p>
                <p v-else>
                  隐私政策内容将在后续版本完善。<br /><br />
                  我们仅收集必要的用户信息用于提供占星分析服务。<br />
                  你的数据不会分享给第三方。
                </p>
              </div>
              <button class="link-btn" @click="agreementType = ''">关闭</button>
            </div>
          </div>
        </transition>
      </Teleport>
    </div>

    <!-- ── 运营商弹窗 ── -->
    <Teleport to="body">
      <transition name="modal">
        <div v-if="showCarrierDialog" class="modal-mask" @click.self="showCarrierDialog = false">
          <div class="modal-card">
            <div class="modal-icon">📶</div>
            <div class="modal-title">中国移动认证</div>
            <div class="modal-phone">{{ maskedPhone }}</div>
            <div class="modal-desc">本机号码一键登录</div>
            <button class="main-btn" @click="confirmOneClick" style="width:100%;margin-bottom:10px">确认登录</button>
            <button class="link-btn" @click="showCarrierDialog = false">取消</button>
          </div>
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useAuth, isDevBypassPhone } from "@/utils/auth";

const router = useRouter();
const route = useRoute();
const { sendCode, verifyCode } = useAuth();
/** 登录后先进入 Onboarding 完善档案（已有档案则回主页） */
const redirectPath = computed(() => {
  if (localStorage.getItem("spirit_profile_completed") === "1") {
    return (route.query.redirect as string) || "/";
  }
  return "/onboarding";
});

const loginMode = ref<"oneclick" | "sms">("oneclick");
const phone = ref("");
const code = ref("");
const agreed = ref(false);
const countdown = ref(0);
const oneClicking = ref(false);
const verifying = ref(false);
const sending = ref(false);
const showCarrierDialog = ref(false);
const agreementType = ref<"" | "user" | "privacy">("");

function showAgreement(type: "user" | "privacy") { agreementType.value = type; }

const canOneClick = computed(() => phone.value.length === 11 && agreed.value);
const canSend = computed(() => phone.value.length === 11);
const canLogin = computed(() => phone.value.length === 11 && code.value.length >= 4 && agreed.value);
const isDevBypass = computed(() => isDevBypassPhone(phone.value));
const maskedPhone = computed(() => { const p = phone.value; return p.length < 11 ? p : p.slice(0, 3) + " **** " + p.slice(-4); });

function onPhoneInput() { phone.value = phone.value.replace(/\D/g, "").slice(0, 11); }

function doOneClickLogin() {
  if (!canOneClick.value) return;
  if (isDevBypass.value) { devDirectLogin(); return; }
  showCarrierDialog.value = true;
}
async function devDirectLogin() {
  oneClicking.value = true;
  try { await verifyCode(phone.value, "000000"); router.replace(redirectPath.value); } catch { loginMode.value = "sms"; }
  oneClicking.value = false;
}
async function confirmOneClick() {
  showCarrierDialog.value = false; oneClicking.value = true;
  try { await verifyCode(phone.value, "888888"); router.replace(redirectPath.value); } catch { loginMode.value = "sms"; }
  oneClicking.value = false;
}
let timer: any = null;
async function doSendCode() {
  if (!canSend.value) return; sending.value = true;
  try { await sendCode(phone.value); } catch {}
  countdown.value = 60; timer = setInterval(() => { countdown.value--; if (countdown.value <= 0) clearInterval(timer); }, 1000);
  sending.value = false;
}
async function doSmsLogin() {
  if (!canLogin.value) return; verifying.value = true;
  try { await verifyCode(phone.value, code.value); router.replace(redirectPath.value); } catch {}
  verifying.value = false;
}

// ── 柔光粒子画布 ──
const particleCanvas = ref<HTMLCanvasElement | null>(null);
let animId = 0;
let onResize: (() => void) | null = null;

function initParticles() {
  const c = particleCanvas.value; if (!c) return;
  const ctx = c.getContext("2d"); if (!ctx) return;
  const dpr = window.devicePixelRatio || 1;
  onResize = () => { c.width = window.innerWidth * dpr; c.height = window.innerHeight * dpr; c.style.width = window.innerWidth + "px"; c.style.height = window.innerHeight + "px"; };
  onResize(); window.addEventListener("resize", onResize);
  const motes: { x: number; y: number; r: number; vx: number; vy: number; a: number; phase: number }[] = [];
  for (let i = 0; i < 40; i++) {
    motes.push({ x: Math.random() * window.innerWidth * dpr, y: Math.random() * window.innerHeight * dpr, r: 1 + Math.random() * 3, vx: (Math.random() - 0.5) * 0.3, vy: -0.2 - Math.random() * 0.4, a: 0.2 + Math.random() * 0.5, phase: Math.random() * Math.PI * 2 });
  }
  function draw() {
    ctx!.clearRect(0, 0, c!.width, c!.height); const t = Date.now();
    for (const m of motes) {
      m.x += m.vx; m.y += m.vy;
      if (m.y < -20) { m.y = c!.height + 20; m.x = Math.random() * c!.width; }
      if (m.x < -20) m.x = c!.width + 20;
      if (m.x > c!.width + 20) m.x = -20;
      const alpha = m.a * (0.5 + 0.5 * Math.sin(t * 0.001 + m.phase));
      ctx!.beginPath(); ctx!.arc(m.x, m.y, m.r, 0, Math.PI * 2);
      ctx!.fillStyle = `rgba(255,220,200,${alpha.toFixed(2)})`; ctx!.fill();
      if (m.r > 2) { ctx!.beginPath(); ctx!.arc(m.x, m.y, m.r * 4, 0, Math.PI * 2); ctx!.fillStyle = `rgba(255,200,180,${(alpha * 0.12).toFixed(3)})`; ctx!.fill(); }
    }
    animId = requestAnimationFrame(draw);
  }
  draw();
}

function sparkStyle(i: number) { const a = (i / 6) * 360; return { '--a': a + 'deg', animationDelay: i * 0.5 + 's' }; }
</script>

<style scoped>
/* ═══ 基底：朝霞暖光 ═══ */
.login-page {
  min-height: 100vh; position: relative;
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(175deg, #FFF5EE 0%, #FFEFE6 25%, #FFF0F5 55%, #F5F0FF 80%, #FDF5F0 100%);
  overflow: hidden;
}
.particle-canvas { position: absolute; inset: 0; z-index: 0; pointer-events: none; }

/* ── 柔光大光斑 ── */
.glow { position: absolute; border-radius: 50%; pointer-events: none; z-index: 3; }
.glow--top { width: 420px; height: 420px; top: -180px; left: 50%; transform: translateX(-50%); background: radial-gradient(circle, rgba(255,200,170,0.18) 0%, transparent 65%); animation: glow-drift 7s ease-in-out infinite; }
.glow--mid { width: 300px; height: 300px; top: 35%; right: -120px; background: radial-gradient(circle, rgba(220,190,230,0.12) 0%, transparent 65%); animation: glow-drift 9s ease-in-out infinite reverse; }
.glow--bottom { width: 360px; height: 360px; bottom: -140px; left: -100px; background: radial-gradient(circle, rgba(255,220,190,0.14) 0%, transparent 65%); animation: glow-drift 8s ease-in-out infinite; }
@keyframes glow-drift { 0%,100%{transform:translate(0,0) scale(1)} 50%{transform:translate(15px,-15px) scale(1.1)} }

/* ═══ 水晶球 ═══ */
.crystal { position: relative; width: 96px; height: 96px; margin: 0 auto 28px; z-index: 1; }
.crystal-body {
  width: 100%; height: 100%; border-radius: 50%; position: relative; z-index: 2;
  background: radial-gradient(circle at 38% 32%,
    rgba(255,255,255,0.8) 0%, rgba(255,245,240,0.5) 15%,
    rgba(255,220,200,0.3) 35%, rgba(240,200,220,0.2) 55%,
    rgba(220,180,210,0.25) 75%, rgba(200,170,200,0.3) 100%);
  box-shadow: 0 0 30px rgba(255,180,150,0.2), 0 0 60px rgba(255,200,170,0.1), inset 0 0 25px rgba(255,255,255,0.3);
  animation: orb-float 4s ease-in-out infinite;
}
@keyframes orb-float { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-6px)} }
.crystal-core {
  position: absolute; top: 36%; left: 36%; width: 28%; height: 28%; border-radius: 50%;
  background: rgba(255,255,255,0.7); box-shadow: 0 0 18px rgba(255,220,190,0.5);
  animation: core-breathe 2.5s ease-in-out infinite;
}
@keyframes core-breathe { 0%,100%{transform:scale(1);opacity:0.6} 50%{transform:scale(1.25);opacity:0.9} }
.crystal-ring { position: absolute; border-radius: 50%; border: 1px solid; }
.c-ring--1 { inset: 12%; border-color: rgba(220,190,200,0.25); animation: ring-spin 10s linear infinite; }
.c-ring--2 { inset: 22%; border-color: rgba(210,180,190,0.2); animation: ring-spin 14s linear infinite reverse; }
@keyframes ring-spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }
.crystal-aura {
  position: absolute; bottom: -28px; left: 50%; transform: translateX(-50%); z-index: 1;
  width: 70px; height: 28px; border-radius: 50%;
  background: radial-gradient(ellipse, rgba(255,190,160,0.25), transparent);
  animation: aura-breathe 3s ease-in-out infinite;
}
@keyframes aura-breathe { 0%,100%{opacity:0.5;transform:translateX(-50%) scale(1)} 50%{opacity:1;transform:translateX(-50%) scale(1.25)} }
.c-spark {
  position: absolute; top: 50%; left: 50%; width: 3px; height: 3px; border-radius: 50%;
  background: rgba(255,220,190,0.7); z-index: 3; pointer-events: none;
  animation: spark-fly 3.5s ease-in-out infinite;
}
@keyframes spark-fly {
  0%{transform:translate(-50%,-50%) rotate(var(--a)) translateX(44px) scale(0);opacity:0}
  25%{opacity:0.9}
  60%{opacity:0.5}
  100%{transform:translate(-50%,-50%) rotate(var(--a)) translateX(64px) scale(1.4);opacity:0}
}

/* ═══ 品牌 ═══ */
.brand { text-align: center; margin-bottom: 28px; position: relative; z-index: 1; }
.brand-title { font-size: 30px; font-weight: 600; color: #5c3d3a; margin: 0 0 8px; letter-spacing: 6px; }
.brand-char { display: inline-block; animation: char-in 0.5s cubic-bezier(0.25,0.46,0.45,0.94) both; }
@keyframes char-in { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }
.brand-sub { font-size: 13px; color: #b8a090; margin: 0; font-weight: 400; letter-spacing: 1.5px; }

/* ═══ 卡片 ═══ */
.login-body { position: relative; z-index: 4; width: 100%; max-width: 340px; padding: 0 24px; display: flex; flex-direction: column; align-items: center; }
.card { width: 100%; display: flex; flex-direction: column; gap: 12px; animation: card-up 0.7s cubic-bezier(0.25,0.46,0.45,0.94) both; }
@keyframes card-up { from{opacity:0;transform:translateY(20px)} to{opacity:1;transform:translateY(0)} }

/* ── 手机号框 ── */
.phone-box {
  display: flex; align-items: center; gap: 0; width: 100%;
  padding: 2px; border-radius: 18px;
  background: rgba(255,255,255,0.55); border: 1px solid rgba(0,0,0,0.04);
  backdrop-filter: blur(16px);
  transition: all 0.35s cubic-bezier(0.25,0.46,0.45,0.94);
}
.phone-box:focus-within { border-color: rgba(255,160,130,0.35); box-shadow: 0 0 0 5px rgba(255,180,150,0.08); background: rgba(255,255,255,0.7); }
.prefix { font-size: 15px; font-weight: 500; color: #8b6f5f; padding: 14px 0 14px 18px; }
.sep { width: 1px; height: 18px; background: rgba(0,0,0,0.06); margin: 0 10px; }
.phone-inp { flex: 1; border: none; background: transparent; padding: 14px 14px 14px 0; font-size: 16px; color: #4a3028; outline: none; font-family: inherit; letter-spacing: 1.5px; }
.phone-inp::placeholder { color: #c4b0a5; letter-spacing: 1px; }

/* ── 主按钮 ── */
.main-btn {
  width: 100%; padding: 15px; border: none; border-radius: 18px;
  background: linear-gradient(135deg, #f0b8a0 0%, #e8a890 50%, #f0c0b0 100%);
  color: #fff; font-size: 15px; font-weight: 600; cursor: pointer; font-family: inherit; letter-spacing: 2px;
  transition: all 0.35s cubic-bezier(0.25,0.46,0.45,0.94); position: relative; overflow: hidden;
  box-shadow: 0 4px 20px rgba(220,150,120,0.18);
}
.main-btn:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 10px 32px rgba(220,150,120,0.28); }
.main-btn:active:not(:disabled) { transform: scale(0.98); }
.main-btn:disabled { opacity: 0.45; cursor: not-allowed; box-shadow: none; }
.main-btn--dev { background: linear-gradient(135deg, #c8b0d8 0%, #b898c8 50%, #d0b8e0 100%); box-shadow: 0 4px 20px rgba(180,140,200,0.18); }
.main-btn--dev:hover:not(:disabled) { box-shadow: 0 10px 32px rgba(180,140,200,0.28); }
.loader { width: 20px; height: 20px; border-radius: 50%; display: inline-block; border: 2px solid rgba(255,255,255,0.25); border-top-color: #fff; animation: spin 0.7s linear infinite; }
@keyframes spin { to{transform:rotate(360deg)} }

.link-btn { border: none; background: none; color: #c4b0a5; font-size: 13px; cursor: pointer; font-family: inherit; padding: 6px; letter-spacing: 1px; transition: color 0.3s; }
.link-btn:hover { color: #8b6f5f; }

/* ── 验证码 ── */
.code-row { width: 100%; display: flex; gap: 10px; }
.code-inp {
  flex: 1; padding: 14px 16px; border-radius: 18px; border: 1px solid rgba(0,0,0,0.04);
  background: rgba(255,255,255,0.55); backdrop-filter: blur(16px);
  font-size: 16px; color: #4a3028; outline: none; font-family: inherit;
  letter-spacing: 6px; text-align: center; transition: all 0.35s;
}
.code-inp:focus { border-color: rgba(255,160,130,0.35); box-shadow: 0 0 0 5px rgba(255,180,150,0.08); }
.code-inp::placeholder { letter-spacing: 1px; color: #c4b0a5; }
.code-inp:disabled { opacity: 0.35; }
.send-btn {
  padding: 14px 14px; border-radius: 18px; white-space: nowrap;
  border: 1px solid rgba(0,0,0,0.04); background: rgba(255,255,255,0.45);
  color: #a89080; font-size: 12px; font-weight: 500; cursor: pointer; font-family: inherit; letter-spacing: 1px;
  backdrop-filter: blur(12px); transition: all 0.3s;
}
.send-btn:hover:not(:disabled) { color: #5c3d3a; border-color: rgba(255,160,130,0.2); background: rgba(255,255,255,0.65); }
.send-btn:disabled { opacity: 0.35; cursor: not-allowed; }

/* ── 协议 ── */
.agree { display: flex; align-items: center; gap: 8px; margin-top: 22px; cursor: pointer; position: relative; z-index: 1; }
.agree-dot {
  width: 15px; height: 15px; border-radius: 50%; flex-shrink: 0; border: 1.5px solid #d0c0b8;
  transition: all 0.3s; display: flex; align-items: center; justify-content: center; font-size: 9px; color: #fff;
}
.agree-dot.on { background: #e8b098; border-color: #e8b098; box-shadow: 0 0 8px rgba(220,160,130,0.2); }
.agree-text { font-size: 11px; color: #b8a090; }
.agree-link { color: #8b6f5f; }

/* ── 弹窗 ── */
.modal-mask { position: fixed; inset: 0; z-index: 9999; display: flex; align-items: center; justify-content: center; background: rgba(0,0,0,0.3); backdrop-filter: blur(6px); }
.modal-card { width: 280px; padding: 36px 28px 28px; border-radius: 24px; background: rgba(255,255,255,0.9); border: 1px solid rgba(0,0,0,0.04); text-align: center; backdrop-filter: blur(20px); display: flex; flex-direction: column; align-items: center; box-shadow: 0 20px 60px rgba(0,0,0,0.08); }
.modal-icon { font-size: 34px; margin-bottom: 10px; }
.modal-title { font-size: 16px; font-weight: 600; color: #4a3028; margin-bottom: 6px; }
.modal-phone { font-size: 22px; font-weight: 500; color: #5c3d3a; margin-bottom: 2px; letter-spacing: 2px; }
.modal-desc { font-size: 12px; color: #b8a090; margin-bottom: 26px; }
.modal-enter-active { transition: all 0.35s cubic-bezier(0.25,0.46,0.45,0.94); }
.modal-leave-active { transition: all 0.2s ease; }
.modal-enter-from { opacity: 0; }
.modal-enter-from .modal-card { transform: scale(0.93) translateY(10px); }
.modal-leave-to { opacity: 0; }

/* ── 协议弹窗 ── */
.agreement-card { max-width: 320px; }
.agreement-body { font-size: 13px; color: #8b6f5f; line-height: 1.8; text-align: left; padding: 0 4px; margin: 12px 0 16px; }
.agreement-body p { margin: 0; }
</style>
