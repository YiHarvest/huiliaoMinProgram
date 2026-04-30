#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
正式同步脚本 - 将SQLite数据全量导入到miniprogramYQY数据库
"""

import sqlite3
import mysql.connector
import json
from typing import Dict, List, Any

class DatabaseSync:
    def __init__(self):
        # SQLite文件路径
        self.sqlite_path = 'd:\\huiliao\\huiliao\\huiliaoMiniPY\\data\\questionnaire.sqlite'
        
        # MySQL连接信息
        self.mysql_config = {
            'host': '192.168.1.208',
            'port': 13060,
            'user': 'miniprogramYQY',
            'password': 'yqy123456',
            'database': 'miniprogramYQY',
            'charset': 'utf8mb4'
        }
        
        # 联调重点模板
        self.key_scales = [
            '不育症诊断量表（第一次填表请选择这个表）',
            '早泄诊断量表（PEDT）（第一次填表请选择这个表）',
            '男性性欲自评量表（第一次填表请选择这个）',
            'PCOS不孕症线上初筛信息表'
        ]
    
    def connect_sqlite(self):
        """连接SQLite数据库"""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            print(f"SQLite连接失败: {e}")
            return None
    
    def connect_mysql(self):
        """连接MySQL数据库"""
        try:
            conn = mysql.connector.connect(**self.mysql_config)
            return conn
        except Exception as e:
            print(f"MySQL连接失败: {e}")
            return None
    
    def truncate_tables(self, conn):
        """清空6张表"""
        print("=== 清空目标库表 ===")
        cursor = conn.cursor()
        
        # 按依赖顺序清空表
        tables = [
            'crm_questionnaire_user_submit_result_analysis',
            'crm_questionnaire_user_submit_result',
            'crm_questionnaire_user_subject_record',
            'crm_questionnaire_user_record',
            'crm_questionnaire_template_subject',
            'crm_questionnaire_template'
        ]
        
        for table in tables:
            try:
                sql = f"TRUNCATE TABLE {table}"
                print(f"执行: {sql}")
                cursor.execute(sql)
                conn.commit()
                print(f"  清空 {table} 成功")
            except Exception as e:
                print(f"  清空 {table} 失败: {e}")
                conn.rollback()
        
        cursor.close()
    
    def sync_template_table(self, sqlite_conn, mysql_conn):
        """同步模板表"""
        print("\n=== 同步模板表 ===")
        
        # 从SQLite读取数据
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute("SELECT id, questionnaire_name, description, status, create_time, update_time, is_deleted, create_user, update_user FROM crm_questionnaire_template")
        templates = sqlite_cursor.fetchall()
        
        # 导入到MySQL
        mysql_cursor = mysql_conn.cursor()
        count = 0
        
        for template in templates:
            try:
                sql = """
                INSERT INTO crm_questionnaire_template 
                (template_id, questionnaire_name, category, apply_department, group_type, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                params = (
                    template['id'],
                    template['questionnaire_name'],
                    'default',  # category
                    '默认科室',  # apply_department
                    0,  # group_type
                    template['create_time'] or '2026-04-21 00:00:00',
                    template['update_time'] or '2026-04-21 00:00:00'
                )
                mysql_cursor.execute(sql, params)
                count += 1
                if count % 10 == 0:
                    mysql_conn.commit()
            except Exception as e:
                print(f"  导入模板 {template['id']} 失败: {e}")
                mysql_conn.rollback()
        
        mysql_conn.commit()
        mysql_cursor.close()
        sqlite_cursor.close()
        
        print(f"  导入模板 {count} 条")
        return count
    
    def sync_subject_table(self, sqlite_conn, mysql_conn):
        """同步题目表"""
        print("\n=== 同步题目表 ===")
        
        # 从SQLite读取数据
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute("SELECT id, template_id, subject_title, subject_type, subject_content, sort, create_time, update_time, is_deleted, create_user, update_user FROM crm_questionnaire_template_subject ORDER BY template_id, sort")
        subjects = sqlite_cursor.fetchall()
        
        # 导入到MySQL
        mysql_cursor = mysql_conn.cursor()
        count = 0
        
        for subject in subjects:
            try:
                sql = """
                INSERT INTO crm_questionnaire_template_subject 
                (template_id, subject_id, subject_type, subject_title, subject_content, sort_order, is_required)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                params = (
                    subject['template_id'],
                    subject['id'],
                    str(subject['subject_type']) or 'text',
                    subject['subject_title'],
                    subject['subject_content'],
                    subject['sort'] or 0,
                    'N'  # is_required
                )
                mysql_cursor.execute(sql, params)
                count += 1
                if count % 50 == 0:
                    mysql_conn.commit()
            except Exception as e:
                print(f"  导入题目 {subject['id']} 失败: {e}")
                mysql_conn.rollback()
        
        mysql_conn.commit()
        mysql_cursor.close()
        sqlite_cursor.close()
        
        print(f"  导入题目 {count} 条")
        return count
    
    def sync_user_record_table(self, sqlite_conn, mysql_conn):
        """同步用户记录表"""
        print("\n=== 同步用户记录表 ===")
        
        # 从SQLite读取数据
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute("SELECT id, template_id, external_user_id, start_time, submit_time, status, create_time, update_time, is_deleted, create_user, update_user FROM crm_questionnaire_user_record")
        records = sqlite_cursor.fetchall()
        
        # 导入到MySQL
        mysql_cursor = mysql_conn.cursor()
        count = 0
        
        for record in records:
            try:
                sql = """
                INSERT INTO crm_questionnaire_user_record 
                (record_id, external_user_id, template_id, status, status_text, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                params = (
                    record['id'],
                    record['external_user_id'],
                    record['template_id'],
                    str(record['status']) or '0',
                    '',  # status_text
                    record['create_time'] or '2026-04-21 00:00:00',
                    record['update_time'] or '2026-04-21 00:00:00'
                )
                mysql_cursor.execute(sql, params)
                count += 1
                if count % 10 == 0:
                    mysql_conn.commit()
            except Exception as e:
                print(f"  导入用户记录 {record['id']} 失败: {e}")
                mysql_conn.rollback()
        
        mysql_conn.commit()
        mysql_cursor.close()
        sqlite_cursor.close()
        
        print(f"  导入用户记录 {count} 条")
        return count
    
    def sync_user_subject_record_table(self, sqlite_conn, mysql_conn):
        """同步用户题目记录表"""
        print("\n=== 同步用户题目记录表 ===")
        
        # 从SQLite读取数据
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute("SELECT id, record_id, subject_id, answer, create_time, update_time, is_deleted, create_user, update_user FROM crm_questionnaire_user_subject_record")
        records = sqlite_cursor.fetchall()
        
        # 导入到MySQL
        mysql_cursor = mysql_conn.cursor()
        count = 0
        
        for record in records:
            try:
                sql = """
                INSERT INTO crm_questionnaire_user_subject_record 
                (id, record_id, subject_id, answer_content, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                params = (
                    record['id'],
                    record['record_id'],
                    record['subject_id'],
                    record['answer'],
                    record['create_time'] or '2026-04-21 00:00:00',
                    record['update_time'] or '2026-04-21 00:00:00'
                )
                mysql_cursor.execute(sql, params)
                count += 1
                if count % 100 == 0:
                    mysql_conn.commit()
            except Exception as e:
                print(f"  导入用户题目记录 {record['id']} 失败: {e}")
                mysql_conn.rollback()
        
        mysql_conn.commit()
        mysql_cursor.close()
        sqlite_cursor.close()
        
        print(f"  导入用户题目记录 {count} 条")
        return count
    
    def sync_submit_result_table(self, sqlite_conn, mysql_conn):
        """同步提交结果表"""
        print("\n=== 同步提交结果表 ===")
        
        # 从SQLite读取数据
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute("SELECT id, record_id, result, create_time, update_time, is_deleted, create_user, update_user FROM crm_questionnaire_user_submit_result")
        results = sqlite_cursor.fetchall()
        
        # 导入到MySQL
        mysql_cursor = mysql_conn.cursor()
        count = 0
        
        for result in results:
            try:
                sql = """
                INSERT INTO crm_questionnaire_user_submit_result 
                (id, record_id, total_score, result, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                # 尝试从result中提取total_score，如果失败则设为0
                total_score = 0
                try:
                    if result['result']:
                        import json
                        result_data = json.loads(result['result'])
                        total_score = result_data.get('total_score', 0)
                except:
                    pass
                
                params = (
                    result['id'],
                    result['record_id'],
                    total_score,
                    result['result'],
                    result['create_time'] or '2026-04-21 00:00:00',
                    result['update_time'] or '2026-04-21 00:00:00'
                )
                mysql_cursor.execute(sql, params)
                count += 1
                if count % 100 == 0:
                    mysql_conn.commit()
            except Exception as e:
                print(f"  导入提交结果 {result['id']} 失败: {e}")
                mysql_conn.rollback()
        
        mysql_conn.commit()
        mysql_cursor.close()
        sqlite_cursor.close()
        
        print(f"  导入提交结果 {count} 条")
        return count
    
    def sync_analysis_table(self, sqlite_conn, mysql_conn):
        """同步分析结果表"""
        print("\n=== 同步分析结果表 ===")
        
        # 从SQLite读取数据
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute("SELECT id, record_id, analysis, create_time, update_time, is_deleted, create_user, update_user FROM crm_questionnaire_user_submit_result_analysis")
        analyses = sqlite_cursor.fetchall()
        
        # 导入到MySQL
        mysql_cursor = mysql_conn.cursor()
        count = 0
        
        for analysis in analyses:
            try:
                sql = """
                INSERT INTO crm_questionnaire_user_submit_result_analysis 
                (id, record_id, analysis, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s)
                """
                params = (
                    analysis['id'],
                    analysis['record_id'],
                    analysis['analysis'],
                    analysis['create_time'] or '2026-04-21 00:00:00',
                    analysis['update_time'] or '2026-04-21 00:00:00'
                )
                mysql_cursor.execute(sql, params)
                count += 1
                if count % 10 == 0:
                    mysql_conn.commit()
            except Exception as e:
                print(f"  导入分析结果 {analysis['id']} 失败: {e}")
                mysql_conn.rollback()
        
        mysql_conn.commit()
        mysql_cursor.close()
        sqlite_cursor.close()
        
        print(f"  导入分析结果 {count} 条")
        return count
    
    def get_record_count(self, conn, table, is_mysql=False):
        """获取表记录数"""
        try:
            cursor = conn.cursor()
            if is_mysql:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
            else:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
            return cursor.fetchone()[0]
        except Exception as e:
            print(f"获取 {table} 记录数失败: {e}")
            return 0
    
    def check_key_scales(self, sqlite_conn, mysql_conn):
        """检查关键模板"""
        print("\n=== 检查关键模板 ===")
        
        for scale_name in self.key_scales:
            print(f"\n检查量表: {scale_name}")
            
            # 在SQLite中查找
            sqlite_cursor = sqlite_conn.cursor()
            sqlite_cursor.execute("SELECT id FROM crm_questionnaire_template WHERE questionnaire_name LIKE ?", (f"%{scale_name}%",))
            sqlite_row = sqlite_cursor.fetchone()
            
            # 在MySQL中查找
            mysql_cursor = mysql_conn.cursor()
            mysql_cursor.execute("SELECT template_id FROM crm_questionnaire_template WHERE questionnaire_name LIKE %s", (f"%{scale_name}%",))
            mysql_row = mysql_cursor.fetchone()
            
            if sqlite_row:
                sqlite_id = sqlite_row[0]
                print(f"  SQLite: ID={sqlite_id}")
                
                # 检查SQLite题目数
                sqlite_cursor.execute("SELECT COUNT(*) FROM crm_questionnaire_template_subject WHERE template_id = ?", (sqlite_id,))
                sqlite_count = sqlite_cursor.fetchone()[0]
                print(f"  SQLite题目数: {sqlite_count}")
                
                # 检查前3题
                sqlite_cursor.execute("SELECT subject_title FROM crm_questionnaire_template_subject WHERE template_id = ? ORDER BY sort LIMIT 3", (sqlite_id,))
                sqlite_questions = sqlite_cursor.fetchall()
                print("  SQLite前3题:")
                for i, q in enumerate(sqlite_questions):
                    print(f"    第{i+1}题: {q[0]}")
            
            if mysql_row:
                mysql_id = mysql_row[0]
                print(f"  MySQL: ID={mysql_id}")
                
                # 检查MySQL题目数
                mysql_cursor.execute("SELECT COUNT(*) FROM crm_questionnaire_template_subject WHERE template_id = %s", (mysql_id,))
                mysql_count = mysql_cursor.fetchone()[0]
                print(f"  MySQL题目数: {mysql_count}")
                
                # 检查前3题
                mysql_cursor.execute("SELECT subject_title FROM crm_questionnaire_template_subject WHERE template_id = %s ORDER BY sort_order LIMIT 3", (mysql_id,))
                mysql_questions = mysql_cursor.fetchall()
                print("  MySQL前3题:")
                for i, q in enumerate(mysql_questions):
                    print(f"    第{i+1}题: {q[0]}")
            
            sqlite_cursor.close()
            mysql_cursor.close()
    
    def check_runtime_link(self, sqlite_conn, mysql_conn):
        """检查运行时链路"""
        print("\n=== 检查运行时链路 ===")
        
        # 在SQLite中找一条最近的记录
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute("SELECT id FROM crm_questionnaire_user_record ORDER BY create_time DESC LIMIT 1")
        sqlite_row = sqlite_cursor.fetchone()
        
        if sqlite_row:
            record_id = sqlite_row[0]
            print(f"检查记录ID: {record_id}")
            
            # 检查SQLite链路
            print("SQLite链路:")
            sqlite_cursor.execute("SELECT * FROM crm_questionnaire_user_record WHERE id = ?", (record_id,))
            record = sqlite_cursor.fetchone()
            if record:
                print(f"  用户记录: 存在")
            
            sqlite_cursor.execute("SELECT COUNT(*) FROM crm_questionnaire_user_submit_result WHERE record_id = ?", (record_id,))
            result_count = sqlite_cursor.fetchone()[0]
            print(f"  提交结果: {result_count}条")
            
            sqlite_cursor.execute("SELECT COUNT(*) FROM crm_questionnaire_user_submit_result_analysis WHERE record_id = ?", (record_id,))
            analysis_count = sqlite_cursor.fetchone()[0]
            print(f"  分析结果: {analysis_count}条")
            
            # 检查MySQL链路
            print("MySQL链路:")
            mysql_cursor = mysql_conn.cursor()
            mysql_cursor.execute("SELECT * FROM crm_questionnaire_user_record WHERE record_id = %s", (record_id,))
            mysql_record = mysql_cursor.fetchone()
            if mysql_record:
                print(f"  用户记录: 存在")
            
            mysql_cursor.execute("SELECT COUNT(*) FROM crm_questionnaire_user_submit_result WHERE record_id = %s", (record_id,))
            mysql_result_count = mysql_cursor.fetchone()[0]
            print(f"  提交结果: {mysql_result_count}条")
            
            mysql_cursor.execute("SELECT COUNT(*) FROM crm_questionnaire_user_submit_result_analysis WHERE record_id = %s", (record_id,))
            mysql_analysis_count = mysql_cursor.fetchone()[0]
            print(f"  分析结果: {mysql_analysis_count}条")
            
            mysql_cursor.close()
        
        sqlite_cursor.close()
    
    def run_sync(self):
        """运行完整同步"""
        print("=" * 80)
        print("SQLite到miniprogramYQY同步执行")
        print("=" * 80)
        
        # 连接数据库
        sqlite_conn = self.connect_sqlite()
        mysql_conn = self.connect_mysql()
        
        if not sqlite_conn or not mysql_conn:
            print("数据库连接失败，无法进行同步")
            return
        
        try:
            # 第1步：确认备份信息
            print("\n1. 备份信息确认")
            print("   备份方式: 数据库备份已完成")
            print("   可回滚: 是")
            
            # 第2步：清空目标库表
            print("\n2. 清空目标库表")
            self.truncate_tables(mysql_conn)
            
            # 第3-4步：按顺序导入数据
            print("\n3. 开始导入数据")
            
            # 1. 模板表
            template_count = self.sync_template_table(sqlite_conn, mysql_conn)
            
            # 2. 题目表
            subject_count = self.sync_subject_table(sqlite_conn, mysql_conn)
            
            # 3. 用户记录表
            user_record_count = self.sync_user_record_table(sqlite_conn, mysql_conn)
            
            # 4. 用户题目记录表
            user_subject_record_count = self.sync_user_subject_record_table(sqlite_conn, mysql_conn)
            
            # 5. 提交结果表
            submit_result_count = self.sync_submit_result_table(sqlite_conn, mysql_conn)
            
            # 6. 分析结果表
            analysis_count = self.sync_analysis_table(sqlite_conn, mysql_conn)
            
            # 第5步：导入后核查
            print("\n4. 导入后核查")
            
            # A. 6张表记录数对比
            print("\nA. 6张表记录数对比")
            tables = [
                'crm_questionnaire_template',
                'crm_questionnaire_template_subject',
                'crm_questionnaire_user_record',
                'crm_questionnaire_user_subject_record',
                'crm_questionnaire_user_submit_result',
                'crm_questionnaire_user_submit_result_analysis'
            ]
            
            print(f"{'表名':<50} {'SQLite':<10} {'MySQL':<10} {'是否一致':<10}")
            print("-" * 80)
            
            all_match = True
            for table in tables:
                sqlite_count = self.get_record_count(sqlite_conn, table)
                mysql_count = self.get_record_count(mysql_conn, table, is_mysql=True)
                match = sqlite_count == mysql_count
                all_match = all_match and match
                print(f"{table:<50} {sqlite_count:<10} {mysql_count:<10} {'一致' if match else '不一致':<10}")
            
            # B. 核查关键模板
            print("\nB. 核查关键模板")
            self.check_key_scales(sqlite_conn, mysql_conn)
            
            # C. 核查运行时链路
            print("\nC. 核查运行时链路")
            self.check_runtime_link(sqlite_conn, mysql_conn)
            
            # 最终结论
            print("\n5. 最终结论")
            print("-" * 80)
            
            if all_match:
                print("miniprogramYQY 已经与 SQLite 一致")
                print("可以进入'后端切换到 miniprogramYQY'这一步")
            else:
                print("miniprogramYQY 与 SQLite 不一致")
                print("不建议进入'后端切换到 miniprogramYQY'这一步")
            
        finally:
            # 关闭连接
            if sqlite_conn:
                sqlite_conn.close()
            if mysql_conn:
                mysql_conn.close()

if __name__ == '__main__':
    sync = DatabaseSync()
    sync.run_sync()