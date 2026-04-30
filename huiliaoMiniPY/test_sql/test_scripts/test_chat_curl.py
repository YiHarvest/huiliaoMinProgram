import subprocess
import json

def test_chat_with_curl():
    try:
        # 使用 curl 测试接口
        cmd = [
            'curl', '-X', 'POST',
            'http://127.0.0.1:8020/api/chat',
            '-H', 'Content-Type: application/json',
            '-d', json.dumps({
                'assistantId': 'xiaohui',
                'question': '测试聊天功能',
                'chatId': '',
                'userId': 'test_user',
                'openid': 'test_openid'
            }),
            '--connect-timeout', '10'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        
        print('Status Code:', result.returncode)
        print('Output:', result.stdout)
        print('Error:', result.stderr)
        
        if result.returncode == 0:
            try:
                response_data = json.loads(result.stdout)
                if 'content' in response_data:
                    print('AI 回复:', response_data['content'])
                    return True
                else:
                    print('响应中没有 content 字段')
                    return False
            except json.JSONDecodeError as e:
                print(f'解析响应失败: {e}')
                return False
        else:
            print(f'curl 命令失败，返回码: {result.returncode}')
            return False
            
    except Exception as e:
        print(f'测试失败: {e}')
        return False

if __name__ == '__main__':
    success = test_chat_with_curl()
    print('测试结果:', '成功' if success else '失败')
