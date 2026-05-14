import json
import sys
sys.path.insert(0, '.')

from mysql_storage import get_user_profile_mysql, get_user_sensitive_info_mysql

def simulate_get_api_response():
    """模拟 GET /api/user/profile?userId=1 的完整响应"""
    
    print("=" * 80)
    print("[TEST] 模拟 GET /api/user/profile?userId=1 的完整响应")
    print("=" * 80)
    
    user_id = 1
    
    # Step 1: 调用 get_user_profile_mysql
    print("\n[Step 1] 调用 get_user_profile_mysql(user_id=1)")
    profile = get_user_profile_mysql(user_id)
    
    if not profile:
        print("[FAIL] 未找到用户资料！")
        return
    
    print("[OK] 用户基本资料：")
    print(f"  userId: {profile.get('userId')}")
    print(f"  nickname: {profile.get('nickname')}")
    print(f"  avatarUrl: {profile.get('avatarUrl')}")
    print(f"  gender: {profile.get('gender')}")
    print(f"  birthday: {profile.get('birthday')}")
    print(f"  updatedAt: {profile.get('updatedAt')}")
    
    # Step 2: 调用 get_user_sensitive_info_mysql
    print("\n[Step 2] 调用 get_user_sensitive_info_mysql(user_id=1)")
    sensitive_info = get_user_sensitive_info_mysql(user_id)
    
    if not sensitive_info:
        print("[WARN] 未找到敏感信息！")
        print("   这会导致前端 phone/phoneMasked/idCardMasked 全部为空")
        sensitive_info = {}
    else:
        print("[OK] 敏感信息：")
        print(f"  phone (脱敏): {sensitive_info.get('phone')}")
        print(f"  phoneMasked (脱敏): {sensitive_info.get('phoneMasked')}")
        print(f"  idCardMasked (脱敏): {sensitive_info.get('idCardMasked')}")
    
    # Step 3: 构建完整的 API 响应（与 chat_proxy_server.py 一致）
    print("\n[Step 3] 构建完整 API 响应（模拟 chat_proxy_server.py 逻辑）")
    
    api_response = {
        'success': True,
        'data': {
            'nickname': profile.get('nickname'),
            'avatarUrl': profile.get('avatarUrl'),
            'gender': profile.get('gender'),
            'birthday': profile.get('birthday'),
            'updatedAt': profile.get('updatedAt'),
            # 添加敏感信息（脱敏）
            'phone': sensitive_info.get('phone'),
            'phoneMasked': sensitive_info.get('phoneMasked'),
            'idCardMasked': sensitive_info.get('idCardMasked'),
        }
    }
    
    print("\n[RESULT] 完整 API 响应：")
    print(json.dumps(api_response, indent=2, ensure_ascii=False))
    
    # Step 4: 验证关键字段是否存在
    print("\n" + "=" * 80)
    print("[CHECK] 关键字段存在性检查")
    print("=" * 80)
    
    data = api_response['data']
    
    checks = [
        ('nickname', data.get('nickname')),
        ('avatarUrl', data.get('avatarUrl')),
        ('gender', data.get('gender')),
        ('birthday', data.get('birthday')),
        ('phone', data.get('phone')),
        ('phoneMasked', data.get('phoneMasked')),
        ('idCardMasked', data.get('idCardMasked')),
    ]
    
    all_ok = True
    for field_name, value in checks:
        is_valid = bool(value)
        status = "[OK]" if is_valid else "[FAIL]"
        print(f"{status} {field_name}: {value or '(empty)'}")
        if not is_valid and field_name in ['phone', 'phoneMasked', 'idCardMasked']:
            all_ok = False
    
    print("\n" + "-" * 80)
    if all_ok:
        print("[CONCLUSION] 所有关键字段都存在且有效！")
        print("  如果前端仍然显示 75%，问题可能在于：")
        print("  1. 前端缓存了旧的空值，没有正确合并后端返回的新值")
        print("  2. 前端 computeProfileProgress 判断逻辑有问题")
        print("  3. 网络请求失败或被拦截")
    else:
        print("[CONCLUSION] 存在关键字段为空的情况！")
        print("  这将导致前端完成度计算时这些字段为 false")

if __name__ == '__main__':
    simulate_get_api_response()
