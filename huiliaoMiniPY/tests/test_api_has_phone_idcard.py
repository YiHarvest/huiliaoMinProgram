import urllib.request
import json

def test_local_api():
    """测试本地接口"""
    print("=" * 80)
    print("[TEST] 测试本地 GET /api/user/profile?userId=1")
    print("=" * 80)

    try:
        url = "http://127.0.0.1:3161/api/user/profile?userId=1"
        
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            print("\n[RESULT] 本地接口返回：")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            if data.get('success') and data.get('data'):
                profile = data['data']
                print("\n" + "=" * 80)
                print("[CHECK] 关键字段验证")
                print("=" * 80)
                
                checks = [
                    ('hasPhone', profile.get('hasPhone')),
                    ('phoneMasked', profile.get('phoneMasked')),
                    ('hasIdCard', profile.get('hasIdCard')),
                    ('idCardMasked', profile.get('idCardMasked')),
                ]
                
                all_ok = True
                for field, value in checks:
                    is_valid = bool(value)
                    status = "[OK]" if is_valid else "[FAIL]"
                    print(f"{status} {field}: {value}")
                    if not is_valid and field in ['hasPhone', 'hasIdCard']:
                        all_ok = False
                
                print("\n" + "-" * 80)
                if all_ok:
                    print("[PASS] 所有关键字段都存在且有效！")
                    print("  前端应该能正确显示 100% 进度")
                else:
                    print("[FAIL] 存在关键字段缺失！")
            else:
                print("\n[FAIL] 接口返回失败或无数据")
                
    except Exception as e:
        print(f"[ERROR] 请求失败: {e}")
        print("  可能原因：")
        print("  1. 后端服务未启动（需要先启动 chat_proxy_server.py）")
        print("  2. 端口 3161 未监听")
        print("  3. 网络连接问题")

def test_public_api():
    """测试公网接口"""
    print("\n\n" + "=" * 80)
    print("[TEST] 测试公网 GET /api/user/profile?userId=1")
    print("=" * 80)

    try:
        url = "https://miniprogram.huiliaoyiyuan.com/api/user/profile?userId=1"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            print("\n[RESULT] 公网接口返回：")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            if data.get('success') and data.get('data'):
                profile = data['data']
                print("\n" + "=" * 80)
                print("[CHECK] 关键字段验证")
                print("=" * 80)
                
                checks = [
                    ('hasPhone', profile.get('hasPhone')),
                    ('phoneMasked', profile.get('phoneMasked')),
                    ('hasIdCard', profile.get('hasIdCard')),
                    ('idCardMasked', profile.get('idCardMasked')),
                ]
                
                all_ok = True
                for field, value in checks:
                    is_valid = bool(value)
                    status = "[OK]" if is_valid else "[FAIL]"
                    print(f"{status} {field}: {value}")
                    if not is_valid and field in ['hasPhone', 'hasIdCard']:
                        all_ok = False
                
                print("\n" + "-" * 80)
                if all_ok:
                    print("[PASS] 公网接口也包含完整字段！")
                    print("  清除缓存后重新登录应该能显示 100%")
                else:
                    print("[WARN] 公网接口可能还未部署最新代码")
                    print("  需要重启公网服务或等待部署完成")
            else:
                print("\n[FAIL] 接口返回失败或无数据")
                
    except Exception as e:
        print(f"[ERROR] 请求失败: {e}")
        print("  可能原因：")
        print("  1. 公网服务未部署最新代码")
        print("  2. 网络连接问题")
        print("  3. DNS 解析问题")

if __name__ == '__main__':
    test_local_api()
    test_public_api()
