import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from chat_proxy_server import run_server
    print("导入chat_proxy_server成功")
    print("开始启动服务器...")
    run_server()
except Exception as e:
    print(f"启动服务器失败: {e}")
    import traceback
    traceback.print_exc()