/**
 * 全局 Toast 通知系统
 * 轻量级：用 document.createElement 创建 toast DOM，无需组件依赖
 */

const TOAST_CONTAINER_ID = "lk-toast-container";

function ensureContainer(): HTMLElement {
  let el = document.getElementById(TOAST_CONTAINER_ID);
  if (!el) {
    el = document.createElement("div");
    el.id = TOAST_CONTAINER_ID;
    el.style.cssText = `
      position: fixed; top: 20px; left: 50%; transform: translateX(-50%);
      z-index: 9999; display: flex; flex-direction: column;
      align-items: center; gap: 8px; pointer-events: none;
      max-width: 90vw;
    `;
    document.body.appendChild(el);
  }
  return el;
}

function createToastEl(text: string, type: "info" | "success" | "error") {
  const el = document.createElement("div");
  const bg = type === "error" ? "rgba(220,80,70,0.9)" : type === "success" ? "rgba(120,190,140,0.9)" : "rgba(60,50,40,0.85)";
  el.style.cssText = `
    padding: 10px 22px; border-radius: 14px; background: ${bg};
    color: #fff; font-size: 13px; font-weight: 500; font-family: inherit;
    backdrop-filter: blur(12px); box-shadow: 0 6px 24px rgba(0,0,0,0.12);
    pointer-events: auto; animation: lk-toast-in 0.3s ease both;
    max-width: 360px; text-align: center; line-height: 1.5;
  `;
  el.textContent = text;
  return el;
}

function injectAnim() {
  if (document.getElementById("lk-toast-style")) return;
  const style = document.createElement("style");
  style.id = "lk-toast-style";
  style.textContent = `
    @keyframes lk-toast-in {
      from { opacity: 0; transform: translateY(-12px) scale(0.95); }
      to { opacity: 1; transform: translateY(0) scale(1); }
    }
  `;
  document.head.appendChild(style);
}

export function showToast(text: string, type: "info" | "success" | "error" = "info", duration = 3000) {
  injectAnim();
  const container = ensureContainer();
  const el = createToastEl(text, type);
  container.appendChild(el);
  setTimeout(() => {
    el.style.transition = "opacity 0.3s ease, transform 0.3s ease";
    el.style.opacity = "0";
    el.style.transform = "translateY(-8px)";
    setTimeout(() => el.remove(), 300);
  }, duration);
}

/** 便捷别名 */
export const toast = {
  info: (text: string, duration?: number) => showToast(text, "info", duration),
  success: (text: string, duration?: number) => showToast(text, "success", duration),
  error: (text: string, duration?: number) => showToast(text, "error", duration),
};
