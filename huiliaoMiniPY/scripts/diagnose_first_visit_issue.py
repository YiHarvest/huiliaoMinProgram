#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脚本名称: diagnose_first_visit_issue.py
功能: 诊断首诊必填问卷未显示的问题
说明: 详细检查系统配置和数据状态
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'huiliaoMiniPY'))

try:
    from mysql_storage import get_mysql_connection, get_mysql_cursor
except ImportError as e:
    print(f"导入错误: {e}")
    print(f"Python路径: {sys.path}")
    sys.exit(1)


def diagnose():
    """诊断问题"""
    
    print("\n" + "="*80)
    print("首诊必填问卷显示问题 - 诊断报告")
    print("="*80)
    
    try:
        with get_mysql_connection() as connection:
            with get_mysql_cursor(connection) as cursor:
                
                # 1. 检查 crm_questionnaire_template 表
                print("\n【诊断1】检查问卷模板表...")
                cursor.execute('''
                    SELECT COUNT(*) as total, 
                           SUM(CASE WHEN questionnaire_name LIKE '%第一次填表%' 
                                    OR questionnaire_name LIKE '%初诊%'
                                    OR questionnaire_name LIKE '%首诊%'
                                    THEN 1 ELSE 0 END) as first_visit_related
                    FROM crm_questionnaire_template
                    WHERE (del_flag = '0' OR del_flag IS NULL)
                      AND (status = '0' OR status IS NULL)
                ''')
                
                result = cursor.fetchone()
                total, first_visit_count = result if result else (0, 0)
                print(f"  总问卷数: {total}")
                print(f"  首诊相关问卷: {first_visit_count}")
                
                if total == 0:
                    print("  ✗ 问卷模板表为空!")
                    return False
                
                # 2. 检查 doctor_profile 表
                print("\n【诊断2】检查医生信息表...")
                cursor.execute('''
                    SELECT COUNT(*) as total,
                           SUM(CASE WHEN status = '1' THEN 1 ELSE 0 END) as active
                    FROM doctor_profile
                ''')
                
                result = cursor.fetchone()
                total_doctors, active_doctors = result if result else (0, 0)
                print(f"  总医生数: {total_doctors}")
                print(f"  启用医生数: {active_doctors}")
                
                if active_doctors == 0:
                    print("  ✗ 没有启用的医生!")
                    return False
                
                # 3. 检查 doctor_questionnaire_bind 表
                print("\n【诊断3】检查医生-问卷绑定表...")
                cursor.execute('''
                    SELECT COUNT(*) as total,
                           SUM(CASE WHEN visit_stage = 'first_only' THEN 1 ELSE 0 END) as first_only_count,
                           SUM(CASE WHEN visit_stage = 'all_visits' THEN 1 ELSE 0 END) as all_visits_count,
                           SUM(CASE WHEN visit_stage IS NULL OR visit_stage = '' THEN 1 ELSE 0 END) as unset_count
                    FROM doctor_questionnaire_bind
                    WHERE status = 1
                ''')
                
                result = cursor.fetchone()
                if result:
                    total, first_only, all_visits, unset = result
                    print(f"  总绑定数 (status=1): {total}")
                    print(f"    ├─ visit_stage='first_only': {first_only or 0}")
                    print(f"    ├─ visit_stage='all_visits': {all_visits or 0}")
                    print(f"    └─ visit_stage未设置: {unset or 0}")
                    
                    if (first_only or 0) == 0:
                        print("  ⚠️ 没有问卷被标记为 'first_only'")
                        print("  这是问题的根本原因！需要执行配置脚本。")
                
                # 4. 详细列出医生及其绑定的问卷
                print("\n【诊断4】医生-问卷绑定详情...")
                cursor.execute('''
                    SELECT 
                        d.id as doctor_id,
                        d.doctor_name,
                        COUNT(DISTINCT CASE WHEN b.visit_stage = 'first_only' THEN b.id END) as first_only_count,
                        COUNT(DISTINCT CASE WHEN b.visit_stage = 'all_visits' THEN b.id END) as all_visits_count,
                        COUNT(*) as total_bindings
                    FROM doctor_profile d
                    LEFT JOIN doctor_questionnaire_bind b ON d.id = b.doctor_id AND b.status = 1
                    WHERE d.status = '1'
                    GROUP BY d.id, d.doctor_name
                    ORDER BY total_bindings DESC
                    LIMIT 5
                ''')
                
                doctors = cursor.fetchall()
                print(f"  前5个医生的绑定情况:")
                for doctor_id, doctor_name, first_only_count, all_visits_count, total in doctors:
                    print(f"    - {doctor_name} (ID:{doctor_id})")
                    print(f"        ├─ first_only: {first_only_count or 0}")
                    print(f"        ├─ all_visits: {all_visits_count or 0}")
                    print(f"        └─ 总计: {total or 0}")
                
                # 5. 检查 patient_doctor_visit_state 表
                print("\n【诊断5】患者-医生首诊状态...")
                cursor.execute('''
                    SELECT COUNT(*) as total,
                           SUM(CASE WHEN first_visit_completed = 0 THEN 1 ELSE 0 END) as first_visit_pending,
                           SUM(CASE WHEN first_visit_completed = 1 THEN 1 ELSE 0 END) as first_visit_completed
                    FROM patient_doctor_visit_state
                ''')
                
                result = cursor.fetchone()
                if result:
                    total, pending, completed = result
                    print(f"  总记录数: {total or 0}")
                    print(f"    ├─ 首诊未完成: {pending or 0}")
                    print(f"    └─ 首诊已完成: {completed or 0}")
                else:
                    print("  表为空")
                
                # 6. 显示首诊相关的具体问卷名称
                print("\n【诊断6】首诊相关问卷详情...")
                cursor.execute('''
                    SELECT id, questionnaire_name
                    FROM crm_questionnaire_template
                    WHERE (questionnaire_name LIKE '%第一次填表%'
                       OR questionnaire_name LIKE '%初诊%'
                       OR questionnaire_name LIKE '%首诊%'
                       OR questionnaire_name LIKE '%初筛%')
                    AND (del_flag = '0' OR del_flag IS NULL)
                    LIMIT 10
                ''')
                
                questionnaires = cursor.fetchall()
                if questionnaires:
                    print(f"  找到 {len(questionnaires)} 个首诊相关问卷:")
                    for qid, qname in questionnaires:
                        print(f"    - [{qid}] {qname}")
                else:
                    print("  ✗ 没有找到首诊相关问卷")
                
                # 7. 检查数据库表结构
                print("\n【诊断7】表结构检查...")
                cursor.execute("SHOW COLUMNS FROM doctor_questionnaire_bind")
                columns = cursor.fetchall()
                
                visit_stage_exists = any('visit_stage' in str(col[0]) for col in columns)
                if visit_stage_exists:
                    print("  ✓ doctor_questionnaire_bind 表包含 'visit_stage' 字段")
                else:
                    print("  ✗ doctor_questionnaire_bind 表不包含 'visit_stage' 字段!")
                    print("  需要先添加该字段：")
                    print("  ALTER TABLE doctor_questionnaire_bind ADD COLUMN visit_stage VARCHAR(50);")
                
    except Exception as e:
        print(f"\n✗ 诊断过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "="*80)
    print("诊断完成")
    print("="*80)
    
    print("\n【建议】")
    print("1. 如果 first_only 问卷数为0，执行: python configure_first_visit_questionnaires.py")
    print("2. 检查医生是否正确启用 (status = '1')")
    print("3. 检查问卷是否正确启用 (del_flag = '0')")
    print("4. 确认 patient_doctor_visit_state 中首诊状态正确")
    
    return True


if __name__ == '__main__':
    diagnose()
