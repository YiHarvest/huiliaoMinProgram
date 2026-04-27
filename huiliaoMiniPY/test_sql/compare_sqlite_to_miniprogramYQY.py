#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
只读核对脚本 - 对比SQLite和miniprogramYQY数据库
"""

import sqlite3
import mysql.connector
from typing import Dict, List, Any, Tuple

class DatabaseComparator:
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
    
    def get_subject_data(self, conn, template_id, is_mysql=False):
        """获取题目数据"""
        try:
            cursor = conn.cursor(dictionary=True) if is_mysql else conn.cursor()
            
            if is_mysql:
                cursor.execute(
                    "SELECT subject_id, subject_title, sort_order, subject_content FROM crm_questionnaire_template_subject WHERE template_id = %s ORDER BY sort_order",
                    (template_id,)
                )
                return cursor.fetchall()
            else:
                cursor.execute(
                    "SELECT id as subject_id, subject_title, sort as sort_order, subject_content FROM crm_questionnaire_template_subject WHERE template_id = ? ORDER BY sort",
                    (template_id,)
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"获取题目数据失败: {e}")
            return []
    
    def get_subject_count(self, conn, template_id, is_mysql=False):
        """获取题目数量"""
        try:
            cursor = conn.cursor()
            
            if is_mysql:
                cursor.execute("SELECT COUNT(*) FROM crm_questionnaire_template_subject WHERE template_id = %s", (template_id,))
            else:
                cursor.execute("SELECT COUNT(*) FROM crm_questionnaire_template_subject WHERE template_id = ?", (template_id,))
            return cursor.fetchone()[0]
        except Exception as e:
            print(f"获取题目数量失败: {e}")
            return 0
    
    def find_scale_by_name(self, conn, scale_name, is_mysql=False):
        """根据名称查找量表"""
        try:
            cursor = conn.cursor(dictionary=True) if is_mysql else conn.cursor()
            
            if is_mysql:
                cursor.execute(
                    "SELECT template_id as id, questionnaire_name FROM crm_questionnaire_template WHERE questionnaire_name LIKE %s",
                    (f"%{scale_name}%",)
                )
                return cursor.fetchone()
            else:
                cursor.execute(
                    "SELECT id, questionnaire_name FROM crm_questionnaire_template WHERE questionnaire_name LIKE ?",
                    (f"%{scale_name}%",)
                )
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            print(f"查找量表失败: {e}")
            return None
    
    def run_comparison(self):
        """运行完整的对比"""
        print("=" * 80)
        print("SQLite与miniprogramYQY数据库核对报告")
        print("=" * 80)
        
        # 连接数据库
        sqlite_conn = self.connect_sqlite()
        mysql_conn = self.connect_mysql()
        
        if not sqlite_conn or not mysql_conn:
            print("数据库连接失败，无法进行对比")
            return
        
        try:
            # 1. 模板表差异核对
            print("\n1. 模板表差异核对")
            print("-" * 80)
            
            sqlite_templates = self.get_template_data(sqlite_conn)
            mysql_templates = self.get_template_data(mysql_conn, is_mysql=True)
            
            # 只在SQLite中存在的模板
            sqlite_only = [id for id in sqlite_templates if id not in mysql_templates]
            print(f"只在SQLite中存在的模板数量: {len(sqlite_only)}")
            if sqlite_only:
                print("前10个只在SQLite中存在的模板:")
                for id in sqlite_only[:10]:
                    template = sqlite_templates[id]
                    print(f"  ID: {id}, 名称: {template.get('questionnaire_name', '未知')}")
            
            # 只在MySQL中存在的模板
            mysql_only = [id for id in mysql_templates if id not in sqlite_templates]
            print(f"\n只在miniprogramYQY中存在的模板数量: {len(mysql_only)}")
            if mysql_only:
                print("前10个只在miniprogramYQY中存在的模板:")
                for id in mysql_only[:10]:
                    template = mysql_templates[id]
                    print(f"  ID: {id}, 名称: {template.get('questionnaire_name', '未知')}")
            
            # 同ID不同内容的模板
            diff_templates = []
            for id in set(sqlite_templates.keys()) & set(mysql_templates.keys()):
                sqlite_template = sqlite_templates[id]
                mysql_template = mysql_templates[id]
                
                if sqlite_template.get('questionnaire_name') != mysql_template.get('questionnaire_name'):
                    diff_templates.append(id)
            
            print(f"\n同ID不同名称的模板数量: {len(diff_templates)}")
            if diff_templates:
                print("同ID不同名称的模板:")
                for id in diff_templates[:10]:
                    sqlite_template = sqlite_templates[id]
                    mysql_template = mysql_templates[id]
                    print(f"  ID: {id}")
                    print(f"    SQLite: {sqlite_template.get('questionnaire_name')}")
                    print(f"    MySQL: {mysql_template.get('questionnaire_name')}")
            
            # 2. 题目表差异核对
            print("\n2. 题目表差异核对")
            print("-" * 80)
            
            common_templates = set(sqlite_templates.keys()) & set(mysql_templates.keys())
            print(f"共有 {len(common_templates)} 个共同模板")
            
            zero_questions = []
            diff_questions = []
            
            for template_id in list(common_templates)[:20]:  # 只检查前20个模板
                sqlite_count = self.get_subject_count(sqlite_conn, template_id)
                mysql_count = self.get_subject_count(mysql_conn, template_id, is_mysql=True)
                
                if mysql_count == 0:
                    zero_questions.append((template_id, sqlite_count))
                elif sqlite_count != mysql_count:
                    diff_questions.append((template_id, sqlite_count, mysql_count))
            
            print(f"\nminiprogramYQY中题目数为0的模板数量: {len(zero_questions)}")
            if zero_questions:
                print("题目数为0的模板:")
                for template_id, sqlite_count in zero_questions[:10]:
                    template_name = sqlite_templates.get(template_id, {}).get('questionnaire_name', '未知')
                    print(f"  模板ID: {template_id}, 名称: {template_name}, SQLite题目数: {sqlite_count}")
            
            print(f"\n题目数不一致的模板数量: {len(diff_questions)}")
            if diff_questions:
                print("题目数不一致的模板:")
                for template_id, sqlite_count, mysql_count in diff_questions[:10]:
                    template_name = sqlite_templates.get(template_id, {}).get('questionnaire_name', '未知')
                    print(f"  模板ID: {template_id}, 名称: {template_name}, SQLite: {sqlite_count}, MySQL: {mysql_count}")
            
            # 3. 联调重点模板核对
            print("\n3. 联调重点模板核对")
            print("-" * 80)
            
            for scale_name in self.key_scales:
                print(f"\n核对量表: {scale_name}")
                
                # 在SQLite中查找
                sqlite_scale = self.find_scale_by_name(sqlite_conn, scale_name)
                # 在MySQL中查找
                mysql_scale = self.find_scale_by_name(mysql_conn, scale_name, is_mysql=True)
                
                print(f"  SQLite: ID={sqlite_scale.get('id', '未找到') if sqlite_scale else '未找到'}")
                print(f"  miniprogramYQY: ID={mysql_scale.get('id', '未找到') if mysql_scale else '未找到'}")
                
                if sqlite_scale and mysql_scale:
                    # 获取题目数
                    sqlite_count = self.get_subject_count(sqlite_conn, sqlite_scale['id'])
                    mysql_count = self.get_subject_count(mysql_conn, mysql_scale['id'], is_mysql=True)
                    
                    print(f"  SQLite题目数: {sqlite_count}")
                    print(f"  miniprogramYQY题目数: {mysql_count}")
                    
                    # 对比前5题
                    print("  前5题对比:")
                    sqlite_subjects = self.get_subject_data(sqlite_conn, sqlite_scale['id'])
                    mysql_subjects = self.get_subject_data(mysql_conn, mysql_scale['id'], is_mysql=True)
                    
                    for i in range(min(5, len(sqlite_subjects), len(mysql_subjects))):
                        sqlite_subject = sqlite_subjects[i]
                        mysql_subject = mysql_subjects[i]
                        
                        title_match = sqlite_subject.get('subject_title') == mysql_subject.get('subject_title')
                        print(f"    第{i+1}题: {'一致' if title_match else '不一致'}")
                        print(f"      SQLite: subject_id={sqlite_subject.get('subject_id')}, title={sqlite_subject.get('subject_title')}, sort={sqlite_subject.get('sort_order')}")
                        print(f"      MySQL: subject_id={mysql_subject.get('subject_id')}, title={mysql_subject.get('subject_title')}, sort={mysql_subject.get('sort_order')}")
            
            # 4. 问题总结
            print("\n4. miniprogramYQY当前问题总结")
            print("-" * 80)
            
            print(f"模板总数对比:")
            print(f"  SQLite: {len(sqlite_templates)} 个")
            print(f"  miniprogramYQY: {len(mysql_templates)} 个")
            print(f"  差异: {abs(len(sqlite_templates) - len(mysql_templates))} 个")
            
            print(f"\n题目数为0的模板: {len(zero_questions)} 个")
            print(f"题目数不一致的模板: {len(diff_questions)} 个")
            print(f"同ID不同名称的模板: {len(diff_templates)} 个")
            
            # 5. 清洗方案
            print("\n5. 清洗方案")
            print("-" * 80)
            print("步骤1: 处理模板")
            print("  - 删除miniprogramYQY中SQLite没有的模板")
            print("  - 修复同ID不同名称的模板，以SQLite为准")
            print("  - 忽略没有题目的空壳模板")
            
            print("\n步骤2: 处理题目")
            print("  - 以SQLite的题目明细为基准")
            print("  - 对每个模板，先删除MySQL中的现有题目")
            print("  - 从SQLite导入题目到MySQL")
            print("  - 确保subject_title、sort_order、subject_content与SQLite一致")
            
            # 6. 同步方案
            print("\n6. 同步方案")
            print("-" * 80)
            print("推荐方案: 模板和题目全量覆盖，运行时表保留")
            print("\n原因:")
            print("  1. 模板和题目是静态数据，需要与SQLite完全一致")
            print("  2. 运行时表包含用户提交数据，应保留以避免数据丢失")
            print("  3. 这种方案风险最小，不会影响现有联调数据")
            
            # 7. 最终建议
            print("\n7. 最终建议")
            print("-" * 80)
            
            if len(zero_questions) > 0 or len(diff_questions) > 0:
                print("当前不适合把小程序切到miniprogramYQY")
                print("还差的步骤:")
                print("  1. 清洗模板表，删除多余模板")
                print("  2. 按SQLite基准同步题目数据")
                print("  3. 验证同步后的题目数量和内容")
            else:
                print("当前可以考虑把小程序切到miniprogramYQY")
            
            print("\n最稳的下一步执行方案:")
            print("  1. 备份miniprogramYQY数据库")
            print("  2. 按SQLite基准同步模板和题目表")
            print("  3. 验证同步结果")
            print("  4. 逐步切换小程序到miniprogramYQY")
            
        finally:
            # 关闭连接
            if sqlite_conn:
                sqlite_conn.close()
            if mysql_conn:
                mysql_conn.close()

if __name__ == '__main__':
    comparator = DatabaseComparator()
    comparator.run_comparison()