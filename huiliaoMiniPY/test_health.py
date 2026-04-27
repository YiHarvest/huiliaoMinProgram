import urllib.request
import json

def test_health():
    try:
        url = 'http://127.0.0.1:8020/health'
        req = urllib.request.Request(url)
        
        with urllib.request.urlopen(req, timeout=5) as resp:
            response = resp.read().decode('utf-8')
            print('Status:', resp.status)
            print('Response:', response)
            
            response_data = json.loads(response)
            if response_data.get('status') == 'ok':
                print('健康检查通过')
                return True
            else:
                print('健康检查失败')
                return False
                
    except Exception as e:
        print(f'健康检查失败: {e}')
        return False

if __name__ == '__main__':
    success = test_health()
    print('测试结果:', '成功' if success else '失败')
