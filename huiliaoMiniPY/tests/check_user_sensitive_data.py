import json
import sys
sys.path.insert(0, '.')

from mysql_storage import get_mysql_connection, get_mysql_cursor

def check_user_sensitive_data():
    """检查用户敏感信息表中的实际数据"""
    
    # 查询 user_sensitive_info 表中所有记录
    print("=" * 80)
    print("[第一步] 查询 user_sensitive_info 表全部记录")
    print("=" * 80)
    
    try:
        with get_mysql_connection() as connection:
            with get_mysql_cursor(connection) as cursor:
                # 查询所有记录
                cursor.execute('''
                    SELECT id, user_id, phone, id_card, phone_masked, id_card_masked, created_at, updated_at
                    FROM user_sensitive_info
                    ORDER BY id DESC
                    LIMIT 20
                ''')
                rows = cursor.fetchall()
                
                if not rows:
                    print("[FAIL] user_sensitive_info 表为空！没有任何记录")
                    print("   这说明 POST 保存从未成功写入过敏感信息")
                else:
                    print(f"[OK] 找到 {len(rows)} 条记录：\n")
                    for row in rows:
                        print(f"  ID: {row[0]}")
                        print(f"  user_id: {row[1]}")
                        print(f"  phone (完整): {'***' if row[2] else 'NULL'}")
                        print(f"  id_card (完整): {'***' if row[3] else 'NULL'}")
                        print(f"  phone_masked (脱敏): {row[4] or 'NULL'}")
                        print(f"  id_card_masked (脱敏): {row[5] or 'NULL'}")
                        print(f"  created_at: {row[6]}")
                        print(f"  updated_at: {row[7]}")
                        print("-" * 60)
                
                # 统计总数
                cursor.execute('SELECT COUNT(*) FROM user_sensitive_info')
                total = cursor.fetchone()[0]
                print(f"\n[STAT] 总计: {total} 条记录\n")
                
    except Exception as e:
        print(f"[ERROR] 查询失败: {e}")
        return
    
    # 查询 user_profiles 表，确认 userId=1 或 userCode 对应的记录
    print("\n" + "=" * 80)
    print("[第二步] 查询 user_profiles 表，找到当前用户的 ID")
    print("=" * 80)
    
    try:
        with get_mysql_connection() as connection:
            with get_mysql_cursor(connection) as cursor:
                # 查找 userId=1 的用户
                cursor.execute('''
                    SELECT id, user_id, nickname, gender, birthday, updated_at
                    FROM user_profiles 
                    WHERE id = 1 OR user_id = 1
                    ORDER BY id DESC
                    LIMIT 5
                ''')
                rows = cursor.fetchall()
                
                if rows:
                    print(f"\n[OK] 找到 ID=1 或 user_id=1 的用户：\n")
                    for row in rows:
                        print(f"  数据库ID: {row[0]}, 系统user_id: {row[1]}")
                        print(f"  昵称: {row[2]}, 性别: {row[3]}, 生日: {row[4]}")
                        print(f"  更新时间: {row[5]}\n")
                else:
                    print("\n[WARN] 未找到 ID=1 或 user_id=1 的用户")
                
                # 查找 userCode=HLA30753B7 的用户
                cursor.execute('''
                    SELECT up.id, up.user_id, up.nickname, u.user_code
                    FROM user_profiles up
                    LEFT JOIN users u ON up.user_id = u.id
                    WHERE u.user_code = 'HLA30753B7'
                    LIMIT 5
                ''')
                rows = cursor.fetchall()
                
                if rows:
                    print(f"[OK] 找到 userCode=HLA30753B7 的用户：\n")
                    for row in rows:
                        print(f"  profiles表ID: {row[0]}, user_id: {row[1]}")
                        print(f"  昵称: {row[2]}, 用户编码: {row[3]}\n")
                else:
                    print("[WARN] 未找到 userCode=HLA30753B7 的用户（可能 users 表不存在该字段）")
                
                # 列出最近更新的 5 个用户
                cursor.execute('''
                    SELECT up.id, up.user_id, up.nickname, up.updated_at
                    FROM user_profiles up
                    ORDER BY up.updated_at DESC
                    LIMIT 5
                ''')
                rows = cursor.fetchall()
                
                print(f"\n[LIST] 最近更新资料的 5 个用户：\n")
                for i, row in enumerate(rows, 1):
                    print(f"  {i}. profiles表ID={row[0]}, user_id={row[1]}, 昵称={row[2] or '空'}, 更新时间={row[3]}")
                
    except Exception as e:
        print(f"[ERROR] 查询失败: {e}")
        return
    
    # 针对具体用户检查敏感信息
    print("\n" + "=" * 80)
    print("[第三步] 针对具体 user_id 检查敏感信息是否存在")
    print("=" * 80)
    
    target_user_ids = [1]
    
    try:
        with get_mysql_connection() as connection:
            with get_mysql_cursor(connection) as cursor:
                for uid in target_user_ids:
                    print(f"\n[CHECK] 检查 user_id = {uid} 的敏感信息：")
                    
                    cursor.execute('''
                        SELECT phone, id_card, phone_masked, id_card_masked
                        FROM user_sensitive_info
                        WHERE user_id = %s
                    ''', (uid,))
                    
                    row = cursor.fetchone()
                    
                    if row:
                        print(f"  [OK] 记录存在！")
                        print(f"     phone (完整): {'***' if row[0] else 'NULL'}")
                        print(f"     id_card (完整): {'***' if row[1] else 'NULL'}")
                        print(f"     phone_masked: '{row[2] or 'NULL'}'")
                        print(f"     id_card_masked: '{row[3] or 'NULL'}'")
                        
                        # 判断字段是否有效
                        has_phone = bool(row[0] or row[2])
                        has_idcard = bool(row[1] or row[3])
                        
                        print(f"\n  [RESULT] 字段有效性判断：")
                        print(f"     手机号有效: {has_phone} (phone={'有' if row[0] else '无'}, phone_masked={'有' if row[2] else '无'})")
                        print(f"     身份证有效: {has_idcard} (id_card={'有' if row[1] else '无'}, id_card_masked={'有' if row[3] else '无'})")
                    else:
                        print(f"  [FAIL] user_id={uid} 在 user_sensitive_info 表中没有记录！")
                        print(f"     这说明前端保存时没有成功写入敏感信息")
                        
    except Exception as e:
        print(f"[ERROR] 查询失败: {e}")

if __name__ == '__main__':
    check_user_sensitive_data()
