#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建检查报告相关数据库表
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mysql_storage import get_mysql_connection

def create_tables():
    """创建检查报告相关表"""
    
    # 检查报告主表
    create_reports_table = """
    CREATE TABLE IF NOT EXISTS checkup_reports (
        id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '报告ID',
        user_id BIGINT NOT NULL COMMENT '用户ID',
        doctor_id VARCHAR(64) NULL COMMENT '医生ID',
        doctor_name VARCHAR(128) NULL COMMENT '医生姓名',
        doctor_department VARCHAR(128) NULL COMMENT '医生科室',
        report_type VARCHAR(64) NULL COMMENT '报告类型',
        status VARCHAR(32) DEFAULT 'created' COMMENT '状态: created/uploaded/completed',
        remark TEXT NULL COMMENT '备注',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
        deleted_at DATETIME NULL COMMENT '软删除时间',
        INDEX idx_reports_user_id (user_id),
        INDEX idx_reports_created_at (created_at),
        INDEX idx_reports_status (status),
        INDEX idx_reports_deleted_at (deleted_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='检查报告主表'
    """
    
    # 检查报告文件表
    create_files_table = """
    CREATE TABLE IF NOT EXISTS checkup_report_files (
        id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '文件ID',
        report_id BIGINT NOT NULL COMMENT '关联的报告ID',
        user_id BIGINT NOT NULL COMMENT '用户ID',
        file_path VARCHAR(512) NOT NULL COMMENT '文件存储路径',
        file_url VARCHAR(512) NOT NULL COMMENT '文件访问URL',
        original_name VARCHAR(255) NULL COMMENT '原始文件名',
        file_size BIGINT NULL COMMENT '文件大小(字节)',
        mime_type VARCHAR(64) NULL COMMENT '文件MIME类型',
        sort_order INT DEFAULT 0 COMMENT '排序顺序',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        INDEX idx_files_report_id (report_id),
        INDEX idx_files_user_id (user_id),
        INDEX idx_files_created_at (created_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='检查报告文件表'
    """
    
    try:
        with get_mysql_connection() as connection:
            with connection.cursor() as cursor:
                print("正在创建 checkup_reports 表...")
                cursor.execute(create_reports_table)
                print("[OK] checkup_reports 表创建成功")
                
                print("\n正在创建 checkup_report_files 表...")
                cursor.execute(create_files_table)
                print("[OK] checkup_report_files 表创建成功")
                
                connection.commit()
                
                # 验证表创建
                print("\n验证表创建结果：")
                cursor.execute("SHOW TABLES LIKE 'checkup%'")
                tables = cursor.fetchall()
                for (table_name,) in tables:
                    print(f"  [OK] {table_name}")
                
                print("\n" + "=" * 50)
                print("所有表创建完成！")
                print("=" * 50)
                
    except Exception as e:
        print(f"[FAIL] 创建表失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    create_tables()
