"""Mock OpenAI-compatible LLM server. Returns a deterministic response so we
can verify the spirit-chat pipeline picks up source='llm_enhanced' path.

Usage:
    python3 scripts/mock_llm_server.py --port 9876
"""
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer


def make_handler():
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8") if length else ""
            try:
                req = json.loads(body)
            except Exception:
                req = {}
            msgs = req.get("messages", [])
            # 拿到 system prompt 的开头（用来证明 mock 真的收到了真实 prompt）
            sys_prompt = next((m["content"] for m in msgs if m.get("role") == "system"), "")
            user_msg = next((m["content"] for m in reversed(msgs) if m.get("role") == "user"), "")

            reply = (
                f"[MOCK-LLM] 我听见了你说：'{user_msg[:40]}'。"
                f"（系统 prompt 长度 {len(sys_prompt)} 字，含真实星盘证据："
                f"{'是' if '飞星' in sys_prompt or '第' in sys_prompt else '否'}）"
                f"作为这颗星灵，我想用更温暖的方式回应你。"
            )
            resp = {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": reply,
                        }
                    }
                ]
            }
            payload = json.dumps(resp, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, fmt, *args):
            pass  # quiet

    return Handler


def main():
    port = 9876
    if "--port" in sys.argv:
        idx = sys.argv.index("--port")
        port = int(sys.argv[idx + 1])
    server = HTTPServer(("127.0.0.1", port), make_handler())
    print(f"[mock-llm] listening on 127.0.0.1:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
