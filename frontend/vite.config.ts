import { defineConfig, loadEnv } from "vite"
import vue from "@vitejs/plugin-vue"
import { resolve } from "path"
import ElementPlus from 'unplugin-element-plus/vite'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, __dirname, "")
  const devProxyTarget = env.VITE_DEV_PROXY_TARGET || "http://127.0.0.1:8000"

  return {
    plugins: [
      vue(),
      ElementPlus({
        useSource: true,
      }),
    ],
    resolve: {
      alias: {
        "@": resolve(__dirname, "src"),
        "~/": `${resolve(__dirname, "src")}/`,
      },
    },
    server: {
      proxy: {
        "/api": {
          target: devProxyTarget,
          changeOrigin: true,
        },
      },
    },
    css: {
      preprocessorOptions: {
        scss: {
          additionalData: `@use "~/styles/element/index.scss" as *;`,
        },
      },
    },
  }
})
