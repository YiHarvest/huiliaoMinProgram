import sys
import traceback

sys.path.insert(0, 'd:/huiliao/huiliao/huiliaoMiniPY')

try:
    from wechat_subscription import get_wechat_mini_program_config, exchange_code_for_session
    
    # 检查配置
    config = get_wechat_mini_program_config()
    print('=== WeChat Config ===')
    print(f"app_id: '{config['app_id']}'")
    print(f"app_secret: '{config['app_secret']}'")
    print(f"app_id starts with TODO_: {config['app_id'].startswith('TODO_')}")
    print(f"app_secret starts with TODO_: {config['app_secret'].startswith('TODO_')}")
    
    # 测试 exchange_code_for_session
    print('\n=== Testing exchange_code_for_session ===')
    try:
        result = exchange_code_for_session('test_code')
        print('Result:', result)
    except Exception as e:
        print('Error:', type(e).__name__, str(e))
        traceback.print_exc()
        
except Exception as e:
    print('Initialization Error:', type(e).__name__, str(e))
    traceback.print_exc()