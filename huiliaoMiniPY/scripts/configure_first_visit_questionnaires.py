#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脚本名称: configure_first_visit_questionnaires.py
功能: 配置首诊必填问卷
说明: 
  1. 识别包含"第一次填表"、"初诊"等关键词的问卷
  2. 将这些问卷在 doctor_questionnaire_bind 中标记为 visit_stage = 'first_only'
  3. 验证配置结果
  4. 检查 patient_doctor_visit_state 表的状态
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


def configure_first_visit_questionnaires():
    """配置首诊必填问卷"""
    
    print("="*80)
    print("首诊必填问卷配置工具")
    print("="*80)
    
    try:
        with get_mysql_connection() as connection:
            with get_mysql_cursor(connection) as cursor:
                
                # 第一步：查询有哪些问卷包含首诊关键词
                print("\n[第一步] 检查包含首诊关键词的问卷...")
                cursor.execute('''
                    SELECT id, questionnaire_name
                    FROM crm_questionnaire_template
                    WHERE (questionnaire_name LIKE '%第一次填表%'
                       OR questionnaire_name LIKE '%初诊%'
                       OR questionnaire_name LIKE '%首诊%'
                       OR questionnaire_name LIKE '%初筛%')
                    AND (del_flag = '0' OR del_flag IS NULL)
                    AND status = '0'
                ''')
                
                first_visit_questionnaires = cursor.fetchall()
                if not first_visit_questionnaires:
                    print("  ⚠️ 没有找到包含首诊关键词的问卷")
                    return False
                
                print(f"  ✓ 找到 {len(first_visit_questionnaires)} 个首诊相关问卷:")
                for qid, qname in first_visit_questionnaires:
                    print(f"    - [{qid}] {qname}")
                
                # 第二步：更新 doctor_questionnaire_bind 表
                print("\n[第二步] 更新医生-问卷绑定配置...")
                affected_rows = cursor.execute('''
                    UPDATE doctor_questionnaire_bind b
                    SET b.visit_stage = 'first_only'
                    WHERE b.status = 1
                      AND b.questionnaire_id IN (
                        SELECT id FROM crm_questionnaire_template
                        WHERE (questionnaire_name LIKE '%第一次填表%'
                           OR questionnaire_name LIKE '%初诊%'
                           OR questionnaire_name LIKE '%首诊%'
                           OR questionnaire_name LIKE '%初筛%')
                        AND (del_flag = '0' OR del_flag IS NULL)
                      )
                ''')
                
                connection.commit()
                print(f"  ✓ 更新了 {affected_rows} 条记录")
                
                # 第三步：验证配置结果
                print("\n[第三步] 验证配置结果...")
                cursor.execute('''
                    SELECT 
                        b.id,
                        d.id as doctor_id,
                        d.doctor_name,
                        qt.id as questionnaire_id,
                        qt.questionnaire_name,
                        b.visit_stage
                    FROM doctor_questionnaire_bind b
                    JOIN doctor_profile d ON d.id = b.doctor_id
                    JOIN crm_questionnaire_template qt ON qt.id = b.questionnaire_id
                    WHERE b.status = 1 
                      AND d.status = 1
                      AND b.visit_stage = 'first_only'
                    ORDER BY d.doctor_id, b.sort_order
                ''')
                
                results = cursor.fetchall()
                if not results:
                    print("  ⚠️ 配置后没有找到 visit_stage = 'first_only' 的记录")
                    print("  这可能是因为医生或问卷不存在，或状态不为1")
                else:
                    print(f"  ✓ 成功配置 {len(results)} 个医生-问卷组合:")
                    current_doctor = None
                    for bind_id, doctor_id, doctor_name, q_id, q_name, visit_stage in results:
                        if current_doctor != doctor_id:
                            print(f"\n    【医生】 {doctor_name} (ID: {doctor_id})")
                            current_doctor = doctor_id
                        print(f"      └─ [{q_id}] {q_name} (visit_stage={visit_stage})")
                
                # 第四步：显示未配置的问卷
                print("\n[第四步] 检查未配置为首诊必填的其他问卷...")
                cursor.execute('''
                    SELECT 
                        b.id,
                        d.doctor_name,
                        qt.questionnaire_name,
                        b.visit_stage
                    FROM doctor_questionnaire_bind b
                    JOIN doctor_profile d ON d.id = b.doctor_id
                    JOIN crm_questionnaire_template qt ON qt.id = b.questionnaire_id
                    WHERE b.status = 1 
                      AND d.status = 1
                      AND b.visit_stage != 'first_only'
                      AND b.visit_stage != 'all_visits'
                    LIMIT 10
                ''')
                
                other_bindings = cursor.fetchall()
                if other_bindings:
                    print(f"  ℹ️ 存在 {len(other_bindings)} 条其他visit_stage配置:")
                    for bind_id, doctor_name, q_name, visit_stage in other_bindings[:5]:
                        print(f"    - {doctor_name}: {q_name} (visit_stage={visit_stage})")
                
                print("\n" + "="*80)
                print("✓ 配置完成！")
                print("="*80)
                
                print("\n【后续步骤】")
                print("1. 在小程序中，选择相应的医生")
                print("2. 点击'初诊'选项")
                print("3. 应该能看到刚才配置的首诊必填问卷")
                print("4. 如果还看不到，检查patient_doctor_visit_state表中first_visit_completed的值")
                
                return True
                
    except Exception as e:
        print(f"\n✗ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def check_patient_visit_state(patient_id: int, doctor_id: int):
    """检查患者与医生的首诊状态"""
    
    print(f"\n检查患者 {patient_id} 与医生 {doctor_id} 的首诊状态...")
    
    try:
        with get_mysql_connection() as connection:
            with get_mysql_cursor(connection) as cursor:
                cursor.execute('''
                    SELECT patient_id, doctor_id, first_visit_completed, first_visit_completed_at
                    FROM patient_doctor_visit_state
                    WHERE patient_id = %s AND doctor_id = %s
                ''', (patient_id, doctor_id))
                
                result = cursor.fetchone()
                if result:
                    patient_id, doctor_id, first_visit_completed, completed_at = result
                    print(f"✓ 记录存在:")
                    print(f"  - first_visit_completed: {first_visit_completed}")
                    print(f"  - completed_at: {completed_at}")
                    
                    if first_visit_completed == 0:
                        print("  ✓ 状态正确：患者为首诊未完成")
                    else:
                        print("  ⚠️ 患者已完成首诊，需要重置才能看到首诊必填问卷")
                        print("  执行以下SQL来重置：")
                        print(f"  UPDATE patient_doctor_visit_state")
                        print(f"  SET first_visit_completed = 0, first_visit_completed_at = NULL")
                        print(f"  WHERE patient_id = {patient_id} AND doctor_id = {doctor_id};")
                else:
                    print("⚠️ 记录不存在，新建记录...")
                    cursor.execute('''
                        INSERT INTO patient_doctor_visit_state 
                        (patient_id, doctor_id, first_visit_completed)
                        VALUES (%s, %s, 0)
                    ''', (patient_id, doctor_id))
                    connection.commit()
                    print("✓ 记录已创建")
                    
    except Exception as e:
        print(f"✗ 检查出错: {str(e)}")


if __name__ == '__main__':
    # 执行主要配置
    success = configure_first_visit_questionnaires()
    
    if success and len(sys.argv) > 2:
        # 如果提供了patient_id和doctor_id，则检查其状态
        try:
            patient_id = int(sys.argv[1])
            doctor_id = int(sys.argv[2])
            check_patient_visit_state(patient_id, doctor_id)
        except (ValueError, IndexError):
            pass
