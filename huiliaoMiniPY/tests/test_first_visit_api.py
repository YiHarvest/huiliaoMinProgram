#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟小程序前端API调用测试
"""

import sys
import json
sys.path.insert(0, 'huiliaoMiniPY')
from mysql_storage import get_doctor_questionnaires_by_doctor_mysql

def test_api_call():
    print('\n【模拟前端API调用测试】')
    print('=' * 80)
    
    # 测试参数：患者1，医生1
    patient_id = 1
    doctor_id = 1
    
    print(f'\n调用: /api/questionnaires/by-doctor')
    print(f'参数: patientId={patient_id}, doctorId={doctor_id}')
    print('-' * 80)
    
    try:
        result = get_doctor_questionnaires_by_doctor_mysql(doctor_id=doctor_id, patient_id=patient_id)
        
        # 显示响应数据
        print(f'\n【返回数据】')
        print(f'doctorId: {result["doctorId"]}')
        print(f'doctorName: {result["doctorName"]}')
        print(f'isFirstVisit: {result["isFirstVisit"]}')  # ← 关键！
        
        questionnaires = result['questionnaires']
        print(f'\n【问卷列表】(共 {len(questionnaires)} 个)')
        print('-' * 80)
        
        first_only_count = 0
        all_visits_count = 0
        
        for q in questionnaires:
            visit_stage = q.get('visitStage', 'unknown')
            if visit_stage == 'first_only':
                first_only_count += 1
                marker = '⭐ 首诊必填'
            elif visit_stage == 'all_visits':
                all_visits_count += 1
                marker = '   常规'
            else:
                marker = f'? ({visit_stage})'
                
            q_name = q['questionnaireName'][:45].ljust(45)
            print(f'{marker} | {q_name}')
        
        print('\n' + '=' * 80)
        print(f'统计: {first_only_count} 个首诊必填 + {all_visits_count} 个常规 = {len(questionnaires)} 个总计')
        first_visit_status = "✓ 首诊未完成" if result["isFirstVisit"] else "✗ 已完成首诊"
        print(f'首诊状态: {first_visit_status}')
        
        return result
        
    except Exception as e:
        print(f'✗ 错误: {e}')
        import traceback
        traceback.print_exc()
        return None


def test_front_end_logic(api_response):
    """模拟前端的问卷过滤逻辑"""
    if not api_response:
        return
    
    print('\n\n【模拟前端过滤逻辑】')
    print('=' * 80)
    
    # 前端状态
    selected_visit_type = 'first'  # 用户选择了"初诊"
    is_first_visit = api_response['isFirstVisit']
    all_scales = api_response['questionnaires']
    
    print(f'\n前端状态:')
    print(f'  选择的就诊类型: {selected_visit_type}')
    print(f'  isFirstVisit: {is_first_visit}')
    print(f'  总问卷数: {len(all_scales)}')
    
    # 前端过滤逻辑（来自scale-form.ts）
    visible_scales = []
    
    for item in all_scales:
        visit_stage = item.get('visitStage', '')
        
        # 规则1: 检查visit_stage是否匹配
        if selected_visit_type == 'first':
            # 初诊时显示所有问卷
            match_visit_stage = True
        else:
            # 复诊时只显示非first_only的问卷
            match_visit_stage = (visit_stage != 'first_only')
        
        if not match_visit_stage:
            continue
        
        # 规则2: 首诊专用问卷需要isFirstVisit为true
        if visit_stage == 'first_only':
            if is_first_visit:
                # 首诊且是first_only问卷，显示
                visible_scales.append(item)
        else:
            # all_visits问卷，无条件显示
            visible_scales.append(item)
    
    print(f'\n【前端显示的问卷】(共 {len(visible_scales)} 个)')
    print('-' * 80)
    
    first_only_visible = []
    all_visits_visible = []
    
    for q in visible_scales:
        visit_stage = q.get('visitStage', '')
        q_name = q['questionnaireName'][:45].ljust(45)
        
        if visit_stage == 'first_only':
            marker = '⭐ 首诊必填'
            first_only_visible.append(q)
        else:
            marker = '   常规'
            all_visits_visible.append(q)
        
        print(f'{marker} | {q_name}')
    
    print('\n' + '=' * 80)
    print(f'显示统计: {len(first_only_visible)} 个首诊必填 + {len(all_visits_visible)} 个常规 = {len(visible_scales)} 个总计')
    
    if len(first_only_visible) > 0:
        print('✓ 首诊必填问卷已正常显示！问题已解决！')
    else:
        print('✗ 首诊必填问卷未显示')


if __name__ == '__main__':
    api_response = test_api_call()
    test_front_end_logic(api_response)
