#!/usr/bin/env python3
"""
测试 chat_proxy_server 是否能正常启动
"""
import sys
import traceback

print("开始测试 chat_proxy_server...")

try:
    import chat_proxy_server
    print("成功导入 chat_proxy_server 模块")
    
    # 尝试启动服务器
    print("尝试启动服务器...")
    chat_proxy_server.run_server()
    
except Exception as e:
    print(f"启动失败: {e}")
    traceback.print_exc()
    sys.exit(1)
