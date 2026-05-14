#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查 MySQL 数据库表结构
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mysql_storage import get_mysql_connection

def check_tables():
    """检查当前数据库中的所有表"""
    try:
        with get_mysql_connection() as connection:
            with connection.cursor() as cursor:
                # 获取所有表
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                
                print("=" * 60)
                print("当前数据库中的所有表：")
                print("=" * 60)
                
                for (table_name,) in tables:
                    print(f"\n表名: {table_name}")
                    print("-" * 40)
                    
                    # 获取表结构
                    cursor.execute(f"DESC {table_name}")
                    columns = cursor.fetchall()
                    
                    print("字段结构：")
                    for col in columns:
                        field, type_, null, key, default, extra = col
                        key_info = f" [{key}]" if key else ""
                        default_info = f" DEFAULT {default}" if default else ""
                        print(f"  - {field}: {type_}{null}{key_info}{default_info}")
                    
                    # 获取索引
                    cursor.execute(f"SHOW INDEX FROM {table_name}")
                    indexes = cursor.fetchall()
                    if indexes:
                        print("索引：")
                        for idx in indexes:
                            idx_name = idx[2]
                            idx_col = idx[4]
                            print(f"  - {idx_name}: {idx_col}")
                
                # 检查检查报告相关表是否存在
                print("\n" + "=" * 60)
                print("检查报告相关表检查：")
                print("=" * 60)
                
                report_tables = [
                    'checkup_reports',
                    'checkup_report_files',
                    'reports',
                    'report',
                    'medical_report',
                    'user_reports',
                    'upload_reports',
                    'inspection_reports',
                    'exam_reports'
                ]
                
                cursor.execute("SHOW TABLES")
                existing_tables = [t[0] for t in cursor.fetchall()]
                
                for table in report_tables:
                    if table in existing_tables:
                        print(f"  [存在] {table}")
                    else:
                        print(f"  [不存在] {table}")
                
                print("\n" + "=" * 60)
                print("检查完成")
                print("=" * 60)
                
    except Exception as e:
        print(f"检查失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_tables()
