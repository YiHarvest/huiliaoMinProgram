#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验收脚本 - 确认miniprogramYQY与SQLite一致性
"""

import sqlite3
import mysql.connector
from typing import Dict, List, Any

class DatabaseVerifier:
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
        
        # 6张表
        self.tables = [
            'crm_questionnaire_template',
            'crm_questionnaire_template_subject',
            'crm_questionnaire_user_record',
            'crm_questionnaire_user_subject_record',
            'crm_questionnaire_user_submit_result',
            'crm_questionnaire_user_submit_result_analysis'
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
    
    def check_tables_exist(self, conn):
        """检查表是否存在"""
        print("=== 检查表是否存在 ===")
        cursor = conn.cursor()
        
        for table in self.tables:
            try:
                cursor.execute(f"SHOW TABLES LIKE '{table}'")
                result = cursor.fetchone()
                if result:
                    print(f"  {table} 存在")
                else:
                    print(f"  {table} 不存在")
            except Exception as e:
                print(f"  检查 {table} 失败: {e}")
        
        cursor.close()
    
    def get_record_count(self, conn, table, is_mysql=False):
        """获取表记录数"""
        try:
            cursor = conn.cursor()
            if is_mysql:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
            else:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            cursor.close()
            return count
        except Exception as e:
            print(f"获取 {table} 记录数失败: {e}")
            return -1
    
    def check_record_counts(self, sqlite_conn, mysql_conn):
        """检查记录数"""
        print("\n=== 表级记录数核对 ===")
        print(f"{'表名':<50} {'SQLite':<10} {'miniprogramYQY':<15} {'是否一致':<10}")
        print("-" * 90)
        
        all_match = True
        for table in self.tables:
            sqlite_count = self.get_record_count(sqlite_conn, table)
            mysql_count = self.get_record_count(mysql_conn, table, is_mysql=True)
            match = sqlite_count == mysql_count
            all_match = all_match and match
            print(f"{table:<50} {sqlite_count:<10} {mysql_count:<15} {'一致' if match else '不一致':<10}")
        
        return all_match
    
    def get_template_data(self, conn, is_mysql=False):
        """获取模板数据"""
        try:
            cursor = conn.cursor(dictionary=True) if is_mysql else conn.cursor()
            
            if is_mysql:
                cursor.execute("SELECT template_id as id, questionnaire_name, apply_department, group_type FROM crm_questionnaire_template")
                return {str(row['id']): row for row in cursor.fetchall()}
            else:
                cursor.execute("SELECT id, questionnaire_name FROM crm_questionnaire_template")
                return {str(row['id']): {'id': row['id'], 'questionnaire_name': row['questionnaire_name'], 'apply_department': None, 'group_type': None} for row in cursor.fetchall()}
        except Exception as e:
            print(f"获取模板数据失败: {e}")
            return {}
    
    def check_templates(self, sqlite_conn, mysql_conn):
        """检查模板"""
        print("\n=== 模板层核对 ===")
        
        sqlite_templates = self.get_template_data(sqlite_conn)
        mysql_templates = self.get_template_data(mysql_conn, is_mysql=True)
        
        # 检查重复模板
        print("1. 检查重复模板:")
        mysql_names = [t['questionnaire_name'] for t in mysql_templates.values()]
        duplicates = set([name for name in mysql_names if mysql_names.count(name) > 1])
        if duplicates:
            print(f"   存在重复模板: {duplicates}")
        else:
            print("   无重复模板")
        
        # 检查SQLite有、MySQL没有的模板
        print("2. 检查SQLite有、MySQL没有的模板:")
        sqlite_only = [id for id in sqlite_templates if id not in mysql_templates]
        if sqlite_only:
            print(f"   存在 {len(sqlite_only)} 个SQLite独有模板")
            for id in sqlite_only[:5]:
                print(f"     - {sqlite_templates[id]['questionnaire_name']}")
        else:
            print("   所有SQLite模板都在MySQL中存在")
        
        # 检查MySQL有、SQLite没有的模板
        print("3. 检查MySQL有、SQLite没有的模板:")
        mysql_only = [id for id in mysql_templates if id not in sqlite_templates]
        if mysql_only:
            print(f"   存在 {len(mysql_only)} 个MySQL独有模板")
            for id in mysql_only[:5]:
                print(f"     - {mysql_templates[id]['questionnaire_name']}")
        else:
            print("   所有MySQL模板都在SQLite中存在")
        
        # 检查同名不同id的模板
        print("4. 检查同名不同id的模板:")
        sqlite_name_to_ids = {}
        for id, template in sqlite_templates.items():
            name = template['questionnaire_name']
            if name not in sqlite_name_to_ids:
                sqlite_name_to_ids[name] = []
            sqlite_name_to_ids[name].append(id)
        
        mysql_name_to_ids = {}
        for id, template in mysql_templates.items():
            name = template['questionnaire_name']
            if name not in mysql_name_to_ids:
                mysql_name_to_ids[name] = []
            mysql_name_to_ids[name].append(id)
        
        name_conflicts = []
        for name in set(sqlite_name_to_ids.keys()) & set(mysql_name_to_ids.keys()):
            if sqlite_name_to_ids[name] != mysql_name_to_ids[name]:
                name_conflicts.append(name)
        
        if name_conflicts:
            print(f"   存在 {len(name_conflicts)} 个同名不同id的模板")
            for name in name_conflicts[:5]:
                print(f"     - {name}")
        else:
            print("   无同名不同id的模板")
        
        return len(sqlite_only) == 0 and len(mysql_only) == 0 and len(name_conflicts) == 0
    
    def get_subject_count(self, conn, template_id, is_mysql=False):
        """获取题目数量"""
        try:
            cursor = conn.cursor()
            
            if is_mysql:
                cursor.execute("SELECT COUNT(*) FROM crm_questionnaire_template_subject WHERE template_id = %s", (template_id,))
            else:
                cursor.execute("SELECT COUNT(*) FROM crm_questionnaire_template_subject WHERE template_id = ?", (template_id,))
            count = cursor.fetchone()[0]
            cursor.close()
            return count
        except Exception as e:
            print(f"获取题目数量失败: {e}")
            return 0
    
    def check_subjects(self, sqlite_conn, mysql_conn):
        """检查题目"""
        print("\n=== 题目层核对 ===")
        
        sqlite_templates = self.get_template_data(sqlite_conn)
        mysql_templates = self.get_template_data(mysql_conn, is_mysql=True)
        
        # 检查每个模板的题目数
        print("1. 检查每个模板题目数:")
        empty_templates = []
        diff_templates = []
        
        for template_id in sqlite_templates:
            if template_id in mysql_templates:
                sqlite_count = self.get_subject_count(sqlite_conn, template_id)
                mysql_count = self.get_subject_count(mysql_conn, template_id, is_mysql=True)
                
                if mysql_count == 0:
                    empty_templates.append((template_id, sqlite_templates[template_id]['questionnaire_name']))
                elif sqlite_count != mysql_count:
                    diff_templates.append((template_id, sqlite_templates[template_id]['questionnaire_name'], sqlite_count, mysql_count))
        
        # 检查空壳模板
        print("2. 检查空壳模板:")
        if empty_templates:
            print(f"   存在 {len(empty_templates)} 个空壳模板")
            for template_id, name in empty_templates[:5]:
                print(f"     - {name}")
        else:
            print("   无空壳模板")
        
        # 检查题目数不一致的模板
        print("3. 检查题目数不一致的模板:")
        if diff_templates:
            print(f"   存在 {len(diff_templates)} 个题目数不一致的模板")
            for template_id, name, sqlite_count, mysql_count in diff_templates[:5]:
                print(f"     - {name}: SQLite={sqlite_count}, MySQL={mysql_count}")
        else:
            print("   所有模板题目数一致")
        
        return len(empty_templates) == 0 and len(diff_templates) == 0
    
    def check_key_scales(self, sqlite_conn, mysql_conn):
        """检查关键量表"""
        print("\n=== 重点抽查当前联调量表 ===")
        
        all_consistent = True
        
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
            
            sqlite_id = None
            mysql_id = None
            sqlite_count = 0
            mysql_count = 0
            
            if sqlite_row:
                sqlite_id = sqlite_row[0]
                print(f"  SQLite: ID={sqlite_id}")
                
                # 检查SQLite题目数
                sqlite_cursor.execute("SELECT COUNT(*) FROM crm_questionnaire_template_subject WHERE template_id = ?", (sqlite_id,))
                sqlite_count = sqlite_cursor.fetchone()[0]
                print(f"  SQLite题目数: {sqlite_count}")
                
                # 检查SQLite前5题
                sqlite_cursor.execute("SELECT id as subject_id, subject_title, sort as sort_order FROM crm_questionnaire_template_subject WHERE template_id = ? ORDER BY id", (sqlite_id,))
                sqlite_questions = sqlite_cursor.fetchall()
                print("  SQLite前5题:")
                for i, q in enumerate(sqlite_questions):
                    print(f"    第{i+1}题: subject_id={q[0]}, title={q[1]}, sort={q[2]}")
            
            if mysql_row:
                mysql_id = mysql_row[0]
                print(f"  MySQL: ID={mysql_id}")
                
                # 检查MySQL题目数
                mysql_cursor.execute("SELECT COUNT(*) FROM crm_questionnaire_template_subject WHERE template_id = %s", (mysql_id,))
                mysql_count = mysql_cursor.fetchone()[0]
                print(f"  MySQL题目数: {mysql_count}")
                
                # 检查前5题
                mysql_cursor.execute("SELECT subject_id, subject_title, sort_order FROM crm_questionnaire_template_subject WHERE template_id = %s ORDER BY subject_id", (mysql_id,))
                mysql_questions = mysql_cursor.fetchall()
                print("  MySQL前5题:")
                for i, q in enumerate(mysql_questions):
                    print(f"    第{i+1}题: subject_id={q[0]}, title={q[1]}, sort={q[2]}")
            
            # 检查是否一致
            consistent = (sqlite_id == mysql_id) and (sqlite_count == mysql_count) and (len(sqlite_questions) == len(mysql_questions))
            if consistent:
                # 按subject_id排序后比较
                sqlite_questions_sorted = sorted(sqlite_questions, key=lambda x: x[0])
                mysql_questions_sorted = sorted(mysql_questions, key=lambda x: x[0])
                for i, (sq, mq) in enumerate(zip(sqlite_questions_sorted, mysql_questions_sorted)):
                    if sq[0] != mq[0] or sq[1] != mq[1]:
                        consistent = False
                        break
            
            print(f"  结论: {'完全一致' if consistent else '不一致'}")
            all_consistent = all_consistent and consistent
            
            sqlite_cursor.close()
            mysql_cursor.close()
        
        return all_consistent
    
    def run_verification(self):
        """运行完整验证"""
        print("=" * 80)
        print("miniprogramYQY与SQLite一致性验收")
        print("=" * 80)
        
        # 连接数据库
        sqlite_conn = self.connect_sqlite()
        mysql_conn = self.connect_mysql()
        
        if not sqlite_conn or not mysql_conn:
            print("数据库连接失败，无法进行验证")
            return
        
        try:
            # 1. 确认表存在
            print("1. 确认表存在")
            self.check_tables_exist(mysql_conn)
            
            # 2. 表级记录数核对
            print("\n2. 表级记录数核对")
            count_match = self.check_record_counts(sqlite_conn, mysql_conn)
            
            # 3. 模板层核对
            print("\n3. 模板层核对")
            template_match = self.check_templates(sqlite_conn, mysql_conn)
            
            # 4. 题目层核对
            print("\n4. 题目层核对")
            subject_match = self.check_subjects(sqlite_conn, mysql_conn)
            
            # 5. 重点抽查
            print("\n5. 重点抽查当前联调量表")
            key_scale_match = self.check_key_scales(sqlite_conn, mysql_conn)
            
            # 6. 最终结论
            print("\n6. 最终结论")
            print("-" * 80)
            
            all_match = count_match and template_match and subject_match and key_scale_match
            
            if all_match:
                print("miniprogramYQY 已经与 SQLite 一致")
                print("可以让小程序正式切到 miniprogramYQY")
            else:
                print("miniprogramYQY 与 SQLite 不一致")
                print("不建议让小程序切到 miniprogramYQY")
                print("差异点:")
                if not count_match:
                    print("  - 表级记录数不一致")
                if not template_match:
                    print("  - 模板层不一致")
                if not subject_match:
                    print("  - 题目层不一致")
                if not key_scale_match:
                    print("  - 关键量表不一致")
            
        finally:
            # 关闭连接
            if sqlite_conn:
                sqlite_conn.close()
            if mysql_conn:
                mysql_conn.close()

if __name__ == '__main__':
    verifier = DatabaseVerifier()
    verifier.run_verification()