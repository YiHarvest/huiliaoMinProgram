"""
测试订阅消息发送接口 - POST /api/subscription/test-send

使用方法：
1. 启动后端服务
2. 运行此脚本：python tests/test_subscription_send.py
3. 查看返回结果和日志

示例：
    python tests/test_subscription_send.py --user-id 1
    python tests/test_subscription_send.py --user-id 1 --scene tongue_reminder
"""

import argparse
import json
import sys
import time
from datetime import datetime

try:
    import requests
except ImportError:
    print("错误: 需要安装 requests 库")
    print("运行: pip install requests")
    sys.exit(1)


def test_send_subscription(
    user_id: str,
    scene: str = "tongue_reminder",
    base_url: str = "http://localhost:8000"
) -> dict:
    """
    测试发送订阅消息接口

    Args:
        user_id: 用户ID
        scene: 场景（默认 tongue_reminder）
        base_url: 后端服务地址

    Returns:
        接口响应数据
    """
    url = f"{base_url}/api/subscription/test-send"

    payload = {
        "userId": user_id,
        "scene": scene
    }

    print("\n" + "=" * 80)
    print(f"📤 发送测试请求")
    print("=" * 80)
    print(f"URL: {url}")
    print(f"Method: POST")
    print(f"Payload:")
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    start_time = time.time()

    try:
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        end_time = time.time()
        duration_ms = round((end_time - start_time) * 1000, 2)

        print(f"\n⏱️  请求耗时: {duration_ms}ms")
        print(f"📥 响应状态码: {response.status_code}")

        try:
            result = response.json()
        except ValueError:
            print(f"\n❌ 错误: 无法解析 JSON 响应")
            print(f"原始响应内容: {response.text[:500]}")
            return {"success": False, "error": "Invalid JSON response"}

        print(f"\n📋 响应数据:")
        print(json.dumps(result, ensure_ascii=False, indent=2))

        # 分析结果
        print("\n" + "-" * 80)
        print("📊 结果分析")
        print("-" * 80)

        if result.get("success"):
            print("✅ 发送成功!")
            data = result.get("data", {})
            print(f"   - 用户ID: {data.get('userId')}")
            print(f"   - OpenID: {data.get('openid')}")
            print(f"   - 场景: {data.get('scene')}")
            print(f"   - 模板ID: {data.get('templateId')}")
            print(f"   - 跳转页面: {data.get('page')}")
            print(f"   - API耗时: {data.get('durationMs')}ms")
            print(f"   - 发送时间: {data.get('sentAt')}")

            wechat_result = data.get("wechatResult", {})
            errcode = wechat_result.get("errcode", -1)
            if errcode == 0:
                print(f"   - 微信状态: ✅ 成功 (errcode={errcode})")
            else:
                errmsg = wechat_result.get("errmsg", "未知")
                print(f"   - 微信状态: ❌ 失败 (errcode={errcode}, errmsg={errmsg})")
        else:
            print("❌ 发送失败!")
            error_info = result.get("error", {})
            if isinstance(error_info, dict):
                print(f"   - 错误类型: {error_info.get('type', 'Unknown')}")
                print(f"   - 错误代码: {error_info.get('errcode', 'N/A')}")
                print(f"   - 错误消息: {error_info.get('errmsg', error_info.get('message', 'Unknown'))}")
            else:
                print(f"   - 错误信息: {error_info}")

        return result

    except requests.exceptions.ConnectionError:
        print(f"\n❌ 连接失败: 无法连接到后端服务 ({base_url})")
        print("请确认后端服务已启动，并检查地址是否正确")
        return {"success": False, "error": "Connection failed"}

    except requests.exceptions.Timeout:
        print(f"\n❌ 请求超时: 后端服务响应时间超过30秒")
        return {"success": False, "error": "Request timeout"}

    except requests.exceptions.RequestException as e:
        print(f"\n❌ 请求异常: {str(e)}")
        return {"success": False, "error": str(e)}

    except Exception as e:
        print(f"\n❌ 未知错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(
        description="测试订阅消息发送接口",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python test_subscription_send.py --user-id 1
  python test_subscription_send.py --user-id 1 --scene tongue_reminder
  python test_subscription_send.py --user-id 1 --base-url http://localhost:8000

注意:
  - 此接口仅用于测试，不会影响正常的提醒配置和定时任务
  - 即使未开启提醒，也会尝试发送测试消息
  - 请确保用户已在微信中授权订阅消息
        """
    )

    parser.add_argument(
        "--user-id",
        required=True,
        help="用户ID（必填）"
    )

    parser.add_argument(
        "--scene",
        default="tongue_reminder",
        choices=["tongue_reminder"],
        help="场景（默认: tongue_reminder）"
    )

    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="后端服务地址（默认: http://localhost:8000）"
    )

    args = parser.parse_args()

    print("\n" + "#" * 80)
    print("# 订阅消息发送测试工具")
    print("#" * 80)
    print(f"# 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"# 用户ID: {args.user_id}")
    print(f"# 场景: {args.scene}")
    print(f"# 服务地址: {args.base_url}")
    print("#" * 80)

    result = test_send_subscription(
        user_id=args.user_id,
        scene=args.scene,
        base_url=args.base_url
    )

    # 返回退出码
    if result.get("success"):
        data = result.get("data", {})
        wechat_result = data.get("wechatResult", {})
        errcode = wechat_result.get("errcode", -1) if isinstance(wechat_result, dict) else -1

        if errcode == 0:
            print("\n" + "🎉" * 20)
            print("测试完成: 微信消息发送成功！")
            print("请在微信中查看是否收到订阅消息")
            print("🎉" * 20)
            return 0
        else:
            print("\n⚠️  测试完成: 微信返回错误，请查看上方错误信息")
            return 2
    else:
        print("\n❌ 测试失败: 请查看上方错误信息")
        return 1


if __name__ == "__main__":
    sys.exit(main())
