import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from socketserver import ThreadingMixIn
from typing import Any, Optional
from urllib import error, request

from config import config


def build_xiaohui_reply(question: str) -> str:
    normalized_question = question.strip()

    if not normalized_question:
        return '您好，我是小慧，请先告诉我您想咨询的妇科问题。'

    return (
        '您好，我是小慧，当前妇科智能体接口还未单独配置。'
        f'您刚才的问题是：{normalized_question}。'
        '目前我先提供妇科方向的分诊引导：如果涉及月经、白带、备孕、复诊准备或检查报告，可继续补充症状、持续时间和既往检查结果。'
    )


def call_fastgpt(question: str, chat_id: Optional[str] = None) -> dict[str, Any]:
    url = f"{config['fastgpt']['base_url'].rstrip('/')}/v1/chat/completions"
    payload: dict[str, Any] = {
        'stream': False,
        'detail': False,
        'messages': [
            {
                'role': 'user',
                'content': question
            }
        ]
    }

    if chat_id:
        payload['chatId'] = chat_id

    req = request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
        headers={
            'Authorization': f"Bearer {config['fastgpt']['api_key']}",
            'Content-Type': 'application/json'
        },
        method='POST'
    )

    try:
        with request.urlopen(req, timeout=20) as response:
            response_data = json.loads(response.read().decode('utf-8'))
    except error.HTTPError as exc:
        error_body = exc.read().decode('utf-8', errors='ignore')
        raise RuntimeError(f'上游接口调用失败: {error_body}') from exc
    except error.URLError as exc:
        raise RuntimeError(f'上游接口连接失败: {exc.reason}') from exc

    content = (
        response_data.get('choices', [{}])[0]
        .get('message', {})
        .get('content', '')
        .strip()
    )

    if not content:
        raise RuntimeError('上游接口返回成功，但没有有效回复内容')

    return {
        'content': content,
        'chatId': response_data.get('id') or chat_id
    }


class ChatProxyHandler(BaseHTTPRequestHandler):
    server_version = 'ChatProxy/1.0'

    def _write_json(self, data: Any, status: int = 200) -> None:
        encoded = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(encoded)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        self.end_headers()
        self.wfile.write(encoded)

    def do_OPTIONS(self) -> None:
        self._write_json({})

    def do_GET(self) -> None:
        if self.path != '/health':
            self._write_json({'error': 'Not Found'}, status=404)
            return

        self._write_json(
            {
                'status': 'ok',
                'fastgptBaseUrl': config['fastgpt']['base_url'],
                'supportedAssistants': ['xiaohui', 'chen']
            }
        )

    def do_POST(self) -> None:
        if self.path != '/api/chat':
            self._write_json({'error': 'Not Found'}, status=404)
            return

        content_length = int(self.headers.get('Content-Length', '0') or 0)
        raw_body = self.rfile.read(content_length)

        try:
            payload = json.loads(raw_body.decode('utf-8'))
        except json.JSONDecodeError:
            self._write_json({'error': '请求体必须是 JSON'}, status=400)
            return

        assistant_id = str(payload.get('assistantId') or '').strip()
        question = str(payload.get('question') or '').strip()
        chat_id = str(payload.get('chatId') or '').strip() or None

        if assistant_id not in {'xiaohui', 'chen'}:
            self._write_json({'error': 'assistantId 无效'}, status=400)
            return

        if not question:
            self._write_json({'error': 'question 不能为空'}, status=400)
            return

        try:
            # 小慧和陈主任都调用 FastGPT API
            result = call_fastgpt(question, chat_id)
            self._write_json(
                {
                    'assistantId': assistant_id,
                    'content': result['content'],
                    'chatId': result.get('chatId')
                }
            )
        except Exception as exc:
            self._write_json({'error': str(exc)}, status=502)

    def log_message(self, format: str, *args: Any) -> None:
        return


def run_server() -> None:
    host = config['server']['host']
    port = 8010  # 智能体服务使用 8010 端口
    server = ThreadingHTTPServer((host, port), ChatProxyHandler)
    print(f'Chat proxy server running on http://{host}:{port}')
    server.serve_forever()


if __name__ == '__main__':
    run_server()