from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import uuid

class SimpleHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/chat':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                print(f'收到聊天请求: {data}')
                
                # 返回简单的测试响应
                response = {
                    'assistantId': data.get('assistantId', 'xiaohui'),
                    'content': '测试回复：' + data.get('question', ''),
                    'chatId': str(uuid.uuid4()),
                    'replyId': str(uuid.uuid4()),
                    'notifyResult': None
                }
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                
            except Exception as e:
                print(f'处理请求失败: {e}')
                self.send_response(500)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    server = HTTPServer(('127.0.0.1', 8020), SimpleHandler)
    print('简单测试服务器运行在 http://127.0.0.1:8020')
    server.serve_forever()
