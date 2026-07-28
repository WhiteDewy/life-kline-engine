# scripts/

本地开发工具。

## mock_llm_server.py

OpenAI 兼容的 mock LLM server，给 `LIFE_KLINE_LLM_BASE_URL` 指过去就能在
没有真 LLM API key 的情况下跑通整条 chat 链路（v1 / v2 / council / garden
consultation），验证"引擎层把真实星盘证据塞进 system prompt → LLM 被调用"
的整条流水线。

返回的内容会打印 system prompt 长度和"是否含真实星盘证据"的判断，
方便在 backend 日志里肉眼确认 prompt 不再是空架子。

用法：

```bash
# 1. 起 mock
python3 scripts/mock_llm_server.py --port 9876 &

# 2. 在 backend/.env 里配
LIFE_KLINE_LLM_API_KEY=mock-key          # 任意非空，让 is_configured=True
LIFE_KLINE_LLM_BASE_URL=http://127.0.0.1:9876/v1

# 3. 正常起 backend
python3 -m uvicorn backend.main:app --reload

# 4. 调 /api/spirit-chat 等端点，response.data.source 会是 llm_enhanced
```

**不要**在生产环境用——mock 返回的是固定字符串，不是真 LLM。
