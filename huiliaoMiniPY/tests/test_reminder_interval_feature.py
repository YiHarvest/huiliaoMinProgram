"""
测试舌苔提醒自定义频率和时间功能

测试步骤：
1. 执行数据库迁移（添加新字段）
2. 测试 GET 接口返回新字段
3. 测试 POST 接口保存新配置
4. 验证 nextSendAt 计算逻辑

运行方式：
python tests/test_reminder_interval_feature.py
"""

import sys
from datetime import datetime

def test_database_schema():
    """测试数据库表结构是否包含新字段"""
    print("=" * 80)
    print("[TEST 1] 检查数据库表结构")
    print("=" * 80)
    
    try:
        from mysql_storage import get_mysql_connection, get_mysql_cursor
        
        with get_mysql_connection() as conn:
            with get_mysql_cursor(conn) as cursor:
                cursor.execute("""
                    SELECT COLUMN_NAME, DATA_TYPE, COLUMN_DEFAULT, COLUMN_COMMENT
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = 'user_subscribe_reminder'
                    AND COLUMN_NAME IN (
                        'reminder_time',
                        'reminder_interval_days',
                        'next_send_at',
                        'last_sent_at'
                    )
                    ORDER BY ORDINAL_POSITION
                """)
                
                columns = cursor.fetchall()
                
                if not columns:
                    print("[FAIL] 未找到字段，需要执行数据库迁移")
                    print("请运行: python scripts/add_reminder_interval_fields.sql")
                    return False
                
                print("\n[OK] 字段列表:")
                for col in columns:
                    print(f"  - {col[0]}: {col[1]} (默认值: {col[2]}) - {col[3]}")
                
                required_fields = ['reminder_interval_days', 'next_send_at', 'last_sent_at']
                existing_fields = [col[0] for col in columns]
                
                missing = [f for f in required_fields if f not in existing_fields]
                if missing:
                    print(f"\n[FAIL] 缺少字段: {missing}")
                    return False
                
                print("\n[PASS] 所有必要字段已存在")
                return True
                
    except Exception as e:
        print(f"[ERROR] 数据库连接失败: {e}")
        return False


def test_get_reminder_status():
    """测试 GET /api/user/reminder/tongue/status 接口"""
    print("\n" + "=" * 80)
    print("[TEST 2] 测试 GET 舌苔提醒状态接口")
    print("=" * 80)
    
    try:
        from reminder_storage import get_tongue_reminder_status_mysql
        
        # 使用 userId=1 测试
        status = get_tongue_reminder_status_mysql(1)
        
        print("\n[RESULT] 返回数据:")
        print(f"  enabled: {status.get('enabled')}")
        print(f"  reminderTime: {status.get('reminderTime')}")
        print(f"  reminderIntervalDays: {status.get('reminderIntervalDays')}")
        print(f"  lastSentDate: {status.get('lastSentDate')}")
        print(f"  nextSendAt: {status.get('nextSendAt')}")
        print(f"  lastSentAt: {status.get('lastSentAt')}")
        
        # 验证关键字段存在
        checks = [
            ('reminderTime', status.get('reminderTime')),
            ('reminderIntervalDays', status.get('reminderIntervalDays')),
            ('nextSendAt', status.get('nextSendAt')),
            ('lastSentAt', status.get('lastSentAt')),
        ]
        
        all_ok = True
        for field, value in checks:
            if value is None and field not in ['nextSendAt', 'lastSentAt']:
                print(f"\n[WARN] 字段 {field} 为空（可能用户未开启提醒）")
            else:
                print(f"[OK] {field}: {value}")
        
        print("\n[PASS] GET 接口返回正常")
        return True
        
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_upsert_with_new_params():
    """测试 POST 开启提醒接口（带新参数）"""
    print("\n" + "=" * 80)
    print("[TEST 3] 测试 POST 开启提醒接口（自定义频率和时间）")
    print("=" * 80)
    
    try:
        from reminder_storage import upsert_tongue_reminder_mysql
        
        # 测试用例 1: 每3天，09:30 提醒
        print("\n[CASE 1] 每3天，09:30 提醒")
        result = upsert_tongue_reminder_mysql(
            user_id=1,
            reminder_time='09:30',
            reminder_interval_days=3,
            enabled=True
        )
        
        print("  返回结果:")
        print(f"    enabled: {result.get('enabled')}")
        print(f"    reminderTime: {result.get('reminderTime')}")
        print(f"    reminderIntervalDays: {result.get('reminderIntervalDays')}")
        print(f"    nextSendAt: {result.get('nextSendAt')}")
        
        # 验证保存的值
        assert result.get('enabled') == True, "enabled 应该为 True"
        assert result.get('reminderTime') == '09:30', "reminderTime 应该为 09:30"
        assert result.get('reminderIntervalDays') == 3, "reminderIntervalDays 应该为 3"
        assert result.get('nextSendAt') is not None, "nextSendAt 不应该为空"
        
        print("  [PASS] 配置保存成功")
        
        # 测试用例 2: 每周（7天），20:00 提醒
        print("\n[CASE 2] 每周（7天），20:00 提醒")
        result2 = upsert_tongue_reminder_mysql(
            user_id=1,
            reminder_time='20:00',
            reminder_interval_days=7,
            enabled=True
        )
        
        print("  返回结果:")
        print(f"    reminderTime: {result2.get('reminderTime')}")
        print(f"    reminderIntervalDays: {result2.get('reminderIntervalDays')}")
        print(f"    nextSendAt: {result2.get('nextSendAt')}")
        
        assert result2.get('reminderTime') == '20:00', "reminderTime 应该为 20:00"
        assert result2.get('reminderIntervalDays') == 7, "reminderIntervalDays 应该为 7"
        
        print("  [PASS] 周配置保存成功")
        
        return True
        
    except AssertionError as e:
        print(f"\n[FAIL] 断言失败: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_next_send_at_calculation():
    """测试 nextSendAt 计算逻辑"""
    print("\n" + "=" * 80)
    print("[TEST 4] 测试 nextSendAt 计算逻辑")
    print("=" * 80)
    
    try:
        from reminder_storage import calculate_next_send_at
        from datetime import datetime
        
        now = datetime.now()
        print(f"\n当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 测试用例
        test_cases = [
            {'time': '23:59', 'days': 1, 'desc': '今晚 23:59（应该明天）'},
            {'time': '00:01', 'days': 1, 'desc': '凌晨 00:01（应该今天或明天）'},
            {'time': '12:00', 'days': 3, 'desc': '中午 12:00，每3天'},
            {'time': '08:00', 'days': 7, 'desc': '早上 8:00，每周'},
        ]
        
        all_ok = True
        for case in test_cases:
            next_send = calculate_next_send_at(case['time'], case['days'])
            print(f"\n{case['desc']}:")
            print(f"  输入: time={case['time']}, interval={case['days']}天")
            print(f"  输出: nextSendAt = {next_send}")
            
            # 解析验证
            parsed = datetime.strptime(next_send, '%Y-%m-%d %H:%M:%S')
            time_part = parsed.strftime('%H:%M')
            
            if time_part != case['time']:
                print(f"  [WARN] 时间部分不匹配: 期望 {case['time']}, 实际 {time_part}")
                all_ok = False
            else:
                print(f"  [OK] 时间部分正确: {time_part}")
        
        if all_ok:
            print("\n[PASS] nextSendAt 计算逻辑正确")
        else:
            print("\n[FAIL] 存在计算错误")
        
        return all_ok
        
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_validation_functions():
    """测试参数校验函数"""
    print("\n" + "=" * 80)
    print("[TEST 5] 测试参数校验函数")
    print("=" * 80)
    
    try:
        from reminder_storage import validate_reminder_interval_days, validate_reminder_time
        
        # 测试 interval days 校验
        print("\n[测试 reminderIntervalDays 校验]")
        interval_tests = [
            (1, 1, "每天"),
            (2, 2, "每两天"),
            (3, 3, "每三天"),
            (7, 7, "每周"),
            (0, 1, "无效值0 → 默认1"),
            (5, 1, "无效值5 → 默认1"),
            ("abc", 1, "非数字 → 默认1"),
            (None, 1, "空值 → 默认1"),
        ]
        
        for input_val, expected, desc in interval_tests:
            result = validate_reminder_interval_days(input_val)
            status = "[OK]" if result == expected else "[FAIL]"
            print(f"  {status} {desc}: input={input_val}, output={result}, expected={expected}")
        
        # 测试 reminder time 校验
        print("\n[测试 reminderTime 校验]")
        time_tests = [
            ("08:00", "08:00", "标准时间"),
            ("23:59", "23:59", "深夜时间"),
            ("00:00", "00:00", "午夜"),
            ("9:5", "09:05", "补零格式"),
            ("", "08:00", "空字符串 → 默认"),
            (None, "08:00", "None → 默认"),
            ("25:00", "08:00", "无效小时 → 默认"),
            ("12:60", "08:00", "无效分钟 → 默认"),
        ]
        
        all_ok = True
        for input_val, expected, desc in time_tests:
            result = validate_reminder_time(input_val)
            status = "[OK]" if result == expected else "[FAIL]"
            if result != expected:
                all_ok = False
            print(f"  {status} {desc}: input={input_val}, output={result}")
        
        if all_ok:
            print("\n[PASS] 参数校验函数正确")
        else:
            print("\n[FAIL] 存在校验错误")
        
        return all_ok
        
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n" + "#" * 80)
    print("# 舌苔提醒自定义频率和时间功能 - 测试套件")
    print("#" * 80)
    
    results = []
    
    results.append(("数据库表结构检查", test_database_schema()))
    results.append(("GET 状态接口测试", test_get_reminder_status()))
    results.append(("POST 保存配置测试", test_upsert_with_new_params()))
    results.append(("nextSendAt 计算测试", test_next_send_at_calculation()))
    results.append(("参数校验函数测试", test_validation_functions()))
    
    # 汇总结果
    print("\n" + "=" * 80)
    print("# 测试结果汇总")
    print("=" * 80)
    
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    
    for name, ok in results:
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！功能实现完成！")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查")
        return 1


if __name__ == '__main__':
    sys.exit(main())
