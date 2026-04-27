import sqlite3
import json
import os
from typing import Dict, Any, List
from datetime import datetime

# SQLite文件路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_PATH = os.path.join(BASE_DIR, 'data', 'questionnaire.sqlite')

def connect_sqlite():
    """连接SQLite数据库"""
    conn = sqlite3.connect(SQLITE_PATH)
    conn.execute('PRAGMA foreign_keys = ON')
    return conn

def get_questionnaire_options_sqlite(external_user_id: str) -> Dict[str, Any]:
    """获取问卷选项"""
    try:
        conn = connect_sqlite()
        cursor = conn.cursor()
        
        # 打印调试信息
        print(f"[DEBUG] 外部用户ID: {external_user_id}")
        
        # 查询有有效题目的模板
        cursor.execute('''
        SELECT t.id, t.questionnaire_name, t.description 
        FROM crm_questionnaire_template t
        WHERE t.id IN (
            SELECT DISTINCT template_id 
            FROM crm_questionnaire_template_subject s
            WHERE s.subject_title IS NOT NULL AND s.subject_title != ''
            AND s.subject_content IS NOT NULL AND s.subject_content != '{}' AND s.subject_content != '[]'
        )
        ORDER BY t.id DESC
        ''')
        
        results = cursor.fetchall()
        print(f"[DEBUG] 查询结果数量: {len(results)}")
        
        templates = []
        for row in results:
            template_id, questionnaire_name, description = row
            templates.append({
                'id': str(template_id),
                'name': questionnaire_name,
                'description': description or ''
            })
        
        print(f"[DEBUG] 模板列表: {templates}")
        
        return {
            'success': True,
            'data': {
                'templates': templates
            }
        }
    except Exception as e:
        print(f"[ERROR] 获取问卷选项失败: {str(e)}")
        return {
            'success': False,
            'message': f'获取问卷选项失败: {str(e)}'
        }
    finally:
        if 'conn' in locals():
            conn.close()

def start_questionnaire_sqlite(external_user_id: str, template_id: int) -> int:
    """开始问卷"""
    conn = connect_sqlite()
    cursor = conn.cursor()
    
    try:
        # 检查模板是否存在
        cursor.execute('''
        SELECT id FROM crm_questionnaire_template 
        WHERE id = ?
        AND id IN (
            SELECT DISTINCT template_id 
            FROM crm_questionnaire_template_subject s
            WHERE s.subject_title IS NOT NULL AND s.subject_title != ''
            AND s.subject_content IS NOT NULL AND s.subject_content != '{}' AND s.subject_content != '[]'
        )
        ''', (template_id,))
        if not cursor.fetchone():
            raise ValueError(f'未找到模板: {template_id}')
        
        # 生成唯一记录ID
        cursor.execute('''
        SELECT MAX(id) FROM crm_questionnaire_user_record
        ''')
        max_id = cursor.fetchone()[0]
        record_id = (max_id + 1) if max_id else 1
        
        # 插入用户记录
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
        INSERT INTO crm_questionnaire_user_record 
        (id, template_id, external_user_id, start_time, status, create_time, update_time, is_deleted)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (record_id, template_id, external_user_id, now, 1, now, now, 0))
        
        conn.commit()
        return str(record_id)
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_questionnaire_detail_sqlite(record_id: int) -> Dict[str, Any]:
    """获取问卷详情"""
    try:
        conn = connect_sqlite()
        cursor = conn.cursor()
        
        # 打印调试信息
        print(f"[DEBUG] 记录ID: {record_id}")
        
        # 查询用户记录
        cursor.execute('''
        SELECT r.id, r.template_id, t.questionnaire_name, t.description
        FROM crm_questionnaire_user_record r
        JOIN crm_questionnaire_template t ON r.template_id = t.id
        WHERE r.id = ?
        ''', (record_id,))
        template_info = cursor.fetchone()
        
        print(f"[DEBUG] 模板信息: {template_info}")
        
        if not template_info:
            return {
                'success': False,
                'message': '问卷记录不存在'
            }
        
        record_id, template_id, questionnaire_name, description = template_info
        
        print(f"[DEBUG] 模板ID: {template_id}")
        
        # 查询题目
        cursor.execute('''
        SELECT s.id, s.subject_title, s.subject_type, s.subject_content, s.sort
        FROM crm_questionnaire_template_subject s
        WHERE s.template_id = ?
        ''', (template_id,))
        
        results = cursor.fetchall()
        print(f"[DEBUG] 题目查询结果数量: {len(results)}")
        
        subjects = []
        for row in results:
            subject_id, subject_title, subject_type, subject_content, sort = row
            print(f"[DEBUG] 题目: {subject_id}, {subject_title}")
            try:
                content = json.loads(subject_content)
            except Exception as e:
                print(f"[DEBUG] JSON解析失败: {e}")
                content = subject_content
            
            subjects.append({
                'id': str(subject_id),
                'title': subject_title,
                'type': subject_type,
                'content': content,
                'sort': sort
            })
        
        print(f"[DEBUG] 题目列表: {subjects}")
        
        return {
            'success': True,
            'data': {
                'recordId': str(record_id),
                'templateId': str(template_id),
                'questionnaireName': questionnaire_name,
                'description': description,
                'subjects': subjects
            }
        }
    except Exception as e:
        print(f"[ERROR] 获取问卷详情失败: {str(e)}")
        return {
            'success': False,
            'message': f'获取问卷详情失败: {str(e)}'
        }
    finally:
        if 'conn' in locals():
            conn.close()

def submit_questionnaire_sqlite(record_id: int, answers: List[Dict[str, Any]]) -> Dict[str, Any]:
    """提交问卷"""
    conn = connect_sqlite()
    cursor = conn.cursor()
    
    try:
        # 检查记录是否存在
        cursor.execute('''
        SELECT id FROM crm_questionnaire_user_record 
        WHERE id = ? AND is_deleted = 0
        ''', (record_id,))
        if not cursor.fetchone():
            return {
                'success': False,
                'message': '问卷记录不存在'
            }
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 插入用户题目记录
        for answer in answers:
            subject_id = answer.get('subjectId')
            answer_content = answer.get('answer')
            
            # 尝试将subjectId转换为整数
            try:
                subject_id = int(str(subject_id))
            except (ValueError, TypeError):
                continue
            
            # 生成唯一ID
            cursor.execute('''
            SELECT MAX(id) FROM crm_questionnaire_user_subject_record
            ''')
            max_id = cursor.fetchone()[0]
            subject_record_id = (max_id + 1) if max_id else 1
            
            cursor.execute('''
            INSERT INTO crm_questionnaire_user_subject_record 
            (id, record_id, subject_id, answer, create_time, update_time, is_deleted)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (subject_record_id, record_id, subject_id, json.dumps(answer_content, ensure_ascii=False), now, now, 0))
        
        # 生成结果
        result = {
            'answers': answers,
            'submitTime': now
        }
        
        # 插入提交结果
        cursor.execute('''
        SELECT MAX(id) FROM crm_questionnaire_user_submit_result
        ''')
        max_id = cursor.fetchone()[0]
        submit_result_id = (max_id + 1) if max_id else 1
        
        cursor.execute('''
        INSERT INTO crm_questionnaire_user_submit_result 
        (id, record_id, result, create_time, update_time, is_deleted)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (submit_result_id, record_id, json.dumps(result, ensure_ascii=False), now, now, 0))
        
        # 简单的分析
        analysis = {
            'summary': '问卷提交成功',
            'totalQuestions': len(answers),
            'submitTime': now
        }
        
        # 插入分析结果
        cursor.execute('''
        SELECT MAX(id) FROM crm_questionnaire_user_submit_result_analysis
        ''')
        max_id = cursor.fetchone()[0]
        analysis_id = (max_id + 1) if max_id else 1
        
        cursor.execute('''
        INSERT INTO crm_questionnaire_user_submit_result_analysis 
        (id, submit_result_id, analysis_type, analysis, create_time, update_time, is_deleted)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (analysis_id, submit_result_id, 'summary', json.dumps(analysis, ensure_ascii=False), now, now, 0))
        
        # 更新用户记录状态
        cursor.execute('''
        UPDATE crm_questionnaire_user_record 
        SET status = 2, submit_time = ?, update_time = ?
        WHERE id = ?
        ''', (now, now, record_id))
        
        conn.commit()
        
        return {
            'success': True,
            'data': {
                'recordId': record_id,
                'submitTime': now
            }
        }
    except Exception as e:
        conn.rollback()
        return {
            'success': False,
            'message': f'提交问卷失败: {str(e)}'
        }
    finally:
        conn.close()

def get_questionnaire_report_sqlite(record_id: int) -> Dict[str, Any]:
    """获取问卷报告"""
    conn = connect_sqlite()
    cursor = conn.cursor()
    
    try:
        # 查询用户记录
        cursor.execute('''
        SELECT t.questionnaire_name, r.start_time, r.submit_time
        FROM crm_questionnaire_user_record r
        JOIN crm_questionnaire_template t ON r.template_id = t.id
        WHERE r.id = ? AND r.is_deleted = 0
        ''', (record_id,))
        record_info = cursor.fetchone()
        
        if not record_info:
            return {
                'success': False,
                'message': '问卷记录不存在'
            }
        
        questionnaire_name, start_time, submit_time = record_info
        
        # 查询提交结果
        cursor.execute('''
        SELECT s.result
        FROM crm_questionnaire_user_submit_result s
        WHERE s.record_id = ? AND s.is_deleted = 0
        ''', (record_id,))
        result_row = cursor.fetchone()
        
        if not result_row:
            return {
                'success': False,
                'message': '问卷未提交'
            }
        
        result = json.loads(result_row[0])
        
        # 查询分析结果
        cursor.execute('''
        SELECT a.analysis_type, a.analysis
        FROM crm_questionnaire_user_submit_result_analysis a
        JOIN crm_questionnaire_user_submit_result s ON a.submit_result_id = s.id
        WHERE s.record_id = ? AND a.is_deleted = 0
        ''', (record_id,))
        
        analyses = {}
        for row in cursor.fetchall():
            analysis_type, analysis_content = row
            try:
                analyses[analysis_type] = json.loads(analysis_content)
            except:
                analyses[analysis_type] = analysis_content
        
        # 查询用户答案
        cursor.execute('''
        SELECT s.subject_id, s.answer
        FROM crm_questionnaire_user_subject_record s
        WHERE s.record_id = ? AND s.is_deleted = 0
        ''', (record_id,))
        
        answers = []
        for row in cursor.fetchall():
            subject_id, answer_content = row
            try:
                answer = json.loads(answer_content)
            except:
                answer = answer_content
            
            answers.append({
                'subjectId': subject_id,
                'answer': answer
            })
        
        return {
            'success': True,
            'data': {
                'questionnaireName': questionnaire_name,
                'startTime': start_time,
                'submitTime': submit_time,
                'answers': answers,
                'analysis': analyses
            }
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'获取问卷报告失败: {str(e)}'
        }
    finally:
        conn.close()
