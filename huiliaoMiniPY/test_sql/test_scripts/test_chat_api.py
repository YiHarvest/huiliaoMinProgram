import json
import urllib.request
import urllib.parse

def test_chat_api():
    url = 'http://127.0.0.1:8020/api/chat'
    data = {
        'assistantId': 'xiaohui',
        'question': '测试聊天功能',
        'chatId': '',
        'userId': 'test_user',
        'openid': 'test_openid'
    }
    
    try:
        req = urllib.request.Request(
            url=url,
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=30) as resp:
            response = resp.read().decode('utf-8')
            print('Status:', resp.status)
            print('Response:', response)
            
            response_data = json.loads(response)
            if 'content' in response_data:
                print('AI 回复:', response_data['content'])
                return True
            else:
                print('响应中没有 content 字段')
                return False
                
    except Exception as e:
        print('测试失败:', str(e))
        return False

if __name__ == '__main__':
    success = test_chat_api()
    print('测试结果:', '成功' if success else '失败')
