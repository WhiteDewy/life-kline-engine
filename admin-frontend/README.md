# 星灵花园 · CMS (Admin Frontend)

独立的后台管理系统前端，从 `frontend/` 项目分离而来。

## 开发

```bash
cd admin-frontend
npm install
npm run dev          # 启动 Vite，默认端口 5174
npm run build        # 类型检查 + 生产构建
```

开发服务器会自动把 `/api` 代理到 `VITE_DEV_PROXY_TARGET`（默认 `http://127.0.0.1:8000`），
与主应用 `frontend/` 共享同一个 FastAPI 后端。

## 目录

```
admin-frontend/
├── src/
│   ├── views/Admin/      ← 所有 Admin 页面
│   ├── config/adminApi.ts
│   ├── router/index.ts
│   ├── App.vue
│   ├── main.ts
│   └── style.css
├── public/
├── index.html
├── vite.config.ts
├── tsconfig.json
├── package.json
└── .env.example
```

## 环境变量

复制 `.env.example` 为 `.env.development`：

```
VITE_API_BASE_URL=/api
VITE_DEV_PROXY_TARGET=http://127.0.0.1:8000
```
