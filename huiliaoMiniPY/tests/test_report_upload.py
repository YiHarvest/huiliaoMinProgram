#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查报告上传功能测试脚本
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import requests
from datetime import datetime

# 测试配置
BASE_URL = "http://127.0.0.1:8020"
TEST_USER_ID = 1  # 请替换为实际存在的用户ID


def test_create_report():
    """测试创建报告"""
    print("\n" + "="*60)
    print("测试 1: 创建检查报告")
    print("="*60)
    
    url = f"{BASE_URL}/api/report/create"
    data = {
        "userId": TEST_USER_ID,
        "doctorId": "doc_001",
        "doctorName": "张医生",
        "doctorDepartment": "内科",
        "reportType": "血常规",
        "remark": "年度体检报告"
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        result = response.json()
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if result.get('success') and result.get('data', {}).get('reportId'):
            print("[OK] 创建报告成功")
            return result['data']['reportId']
        else:
            print("[FAIL] 创建报告失败")
            return None
    except Exception as e:
        print(f"[FAIL] 请求异常: {e}")
        return None


def test_list_reports():
    """测试获取报告列表"""
    print("\n" + "="*60)
    print("测试 2: 获取报告列表")
    print("="*60)
    
    url = f"{BASE_URL}/api/report/list?userId={TEST_USER_ID}&limit=10&offset=0"
    
    try:
        response = requests.get(url, timeout=10)
        result = response.json()
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if result.get('success'):
            print(f"[OK] 获取列表成功，共 {result.get('data', {}).get('total', 0)} 条记录")
            return True
        else:
            print("[FAIL] 获取列表失败")
            return False
    except Exception as e:
        print(f"[FAIL] 请求异常: {e}")
        return False


def test_get_report_detail(report_id):
    """测试获取报告详情"""
    print("\n" + "="*60)
    print("测试 3: 获取报告详情")
    print("="*60)
    
    url = f"{BASE_URL}/api/report/detail?reportId={report_id}&userId={TEST_USER_ID}"
    
    try:
        response = requests.get(url, timeout=10)
        result = response.json()
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if result.get('success'):
            print("[OK] 获取详情成功")
            return True
        else:
            print("[FAIL] 获取详情失败")
            return False
    except Exception as e:
        print(f"[FAIL] 请求异常: {e}")
        return False


def test_upload_file(report_id):
    """测试上传文件（需要实际图片文件）"""
    print("\n" + "="*60)
    print("测试 4: 上传报告图片")
    print("="*60)
    print("注意: 此测试需要一个实际的图片文件")
    print("请准备一张测试图片并修改 file_path 变量")
    print("跳过此测试...")
    return True


def test_complete_report(report_id):
    """测试完成报告"""
    print("\n" + "="*60)
    print("测试 5: 完成报告")
    print("="*60)
    
    url = f"{BASE_URL}/api/report/complete"
    data = {
        "reportId": report_id,
        "userId": TEST_USER_ID
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        result = response.json()
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if result.get('success'):
            print("[OK] 完成报告成功")
            return True
        else:
            print("[FAIL] 完成报告失败")
            return False
    except Exception as e:
        print(f"[FAIL] 请求异常: {e}")
        return False


def test_delete_report(report_id):
    """测试删除报告"""
    print("\n" + "="*60)
    print("测试 6: 删除报告")
    print("="*60)
    
    url = f"{BASE_URL}/api/report/delete"
    data = {
        "reportId": report_id,
        "userId": TEST_USER_ID
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        result = response.json()
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if result.get('success'):
            print("[OK] 删除报告成功")
            return True
        else:
            print("[FAIL] 删除报告失败")
            return False
    except Exception as e:
        print(f"[FAIL] 请求异常: {e}")
        return False


def test_error_cases():
    """测试错误情况"""
    print("\n" + "="*60)
    print("测试 7: 错误情况测试")
    print("="*60)
    
    # 测试 1: 缺少 userId
    print("\n测试 7.1: 缺少 userId")
    url = f"{BASE_URL}/api/report/create"
    data = {"doctorName": "测试医生"}
    try:
        response = requests.post(url, json=data, timeout=10)
        result = response.json()
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        if not result.get('success'):
            print("[OK] 正确返回错误")
        else:
            print("[FAIL] 应该返回错误")
    except Exception as e:
        print(f"[FAIL] 请求异常: {e}")
    
    # 测试 2: 不存在的报告ID
    print("\n测试 7.2: 不存在的报告ID")
    url = f"{BASE_URL}/api/report/detail?reportId=99999&userId={TEST_USER_ID}"
    try:
        response = requests.get(url, timeout=10)
        result = response.json()
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        if not result.get('success'):
            print("[OK] 正确返回错误")
        else:
            print("[FAIL] 应该返回错误")
    except Exception as e:
        print(f"[FAIL] 请求异常: {e}")


def main():
    """主测试函数"""
    print("="*60)
    print("检查报告上传功能测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试地址: {BASE_URL}")
    print(f"测试用户ID: {TEST_USER_ID}")
    print("="*60)
    
    # 确保服务器在运行
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"\n服务器状态检查: {response.status_code}")
    except Exception as e:
        print(f"\n[WARNING] 无法连接到服务器: {e}")
        print("请确保服务器已启动: python chat_proxy_server.py")
        return
    
    # 运行测试
    report_id = test_create_report()
    
    if report_id:
        test_list_reports()
        test_get_report_detail(report_id)
        # test_upload_file(report_id)  # 跳过文件上传测试
        # test_complete_report(report_id)  # 需要先上传文件
        test_delete_report(report_id)
    
    test_error_cases()
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)


if __name__ == '__main__':
    main()
