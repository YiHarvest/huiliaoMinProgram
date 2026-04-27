from typing import Any, Optional
from datetime import datetime
import mysql.connector
from mysql.connector import Error
from config import config

def get_mysql_connection():
    mysql_config = config['database']['mysql']
    return mysql.connector.connect(
        host=mysql_config['host'],
        port=mysql_config['port'],
        user=mysql_config['user'],
        password=mysql_config['password'],
        database=mysql_config['database']
    )

def get_mysql_cursor(connection):
    return connection.cursor()

def now_iso() -> str:
    return datetime.now().isoformat()

# 问卷相关操作
def get_questionnaire_detail_mysql(questionnaire_id: str) -> Optional[dict[str, Any]]:
    """
    获取问卷详情
    """
    with get_mysql_connection() as connection:
        with get_mysql_cursor(connection) as cursor:
            # 从 crm_questionnaire_user_record 表获取记录信息
            cursor.execute('''
                SELECT 
                    u.id, u.external_user_id, u.questionnaire_name, 
                    u.group_type, u.apply_department, u.status, 
                    u.create_time, u.update_time, t.id as template_id
                FROM crm_questionnaire_user_record u
                LEFT JOIN crm_questionnaire_template t ON u.questionnaire_name = t.questionnaire_name
                WHERE u.id = %s AND u.del_flag = '0'
            ''', (questionnaire_id,))
            
            result = cursor.fetchone()
            if not result:
                return None
            
            # 解析结果
            record_id, external_user_id, questionnaire_name, group_type, apply_department, status, create_time, update_time, template_id = result
            
            # 获取题目信息
            questions = []
            if template_id:
                cursor.execute('''
                    SELECT 
                        id, subject_type, subject_title, subject_content, 
                        is_required, sort_order
                    FROM crm_questionnaire_template_subject
                    WHERE template_id = %s AND del_flag = '0'
                    ORDER BY sort_order
                ''', (template_id,))
                
                for subject in cursor.fetchall():
                    subject_id, subject_type, subject_title, subject_content, is_required, sort_order = subject
                    
                    # 解析题目内容（JSON 格式）
                    import json
                    try:
                        content = json.loads(subject_content) if subject_content else []
                    except:
                        content = []
                    
                    # 构建题目对象
                    question = {
                        "id": str(subject_id),
                        "type": subject_type,
                        "title": subject_title,
                        "options": content,
                        "required": is_required == 'Y',
                        "order": sort_order
                    }
                    questions.append(question)
            
            # 构建返回结果
            detail = {
                "recordId": str(record_id),
                "templateId": str(template_id) if template_id else "",
                "questionnaireName": questionnaire_name,
                "status": status,
                "questions": questions
            }
            
            return detail

def get_questionnaire_options_mysql(external_user_id=None) -> dict[str, Any]:
    with get_mysql_connection() as connection:
        with get_mysql_cursor(connection) as cursor:
            # 获取所有有效的量表模板
            cursor.execute('''
                SELECT id, group_type, questionnaire_name, apply_department, status
                FROM crm_questionnaire_template
                WHERE del_flag = '0'
                ORDER BY id
            ''')
            
            # 动态生成分类列表，基于 apply_department
            categories = []
            scales = []
            
            for row in cursor.fetchall():
                template_id, group_type, questionnaire_name, apply_department, status = row
                
                # 添加到分类列表（去重）
                if apply_department and not any(cat['name'] == apply_department for cat in categories):
                    categories.append({
                        'id': apply_department,
                        'name': apply_department,
                        'description': apply_department
                    })
                
                # 查询用户记录
                record_id = None
                if external_user_id:
                    cursor.execute('''
                        SELECT id
                        FROM crm_questionnaire_user_record
                        WHERE external_user_id = %s
                          AND questionnaire_name = %s
                          AND del_flag = '0'
                        LIMIT 1
                    ''', (external_user_id, questionnaire_name))
                    record_result = cursor.fetchone()
                    if record_result:
                        record_id = str(record_result[0])
                
                # 构建量表信息
                scale_data = {
                    'templateId': str(template_id),
                    'questionnaireName': questionnaire_name,
                    'category': apply_department,
                    'applyDepartment': apply_department,
                    'groupType': group_type,
                    'recordId': record_id,
                    'status': status,
                    'statusText': '已启用' if status == '1' else '未启用'
                }
                
                scales.append(scale_data)
            
            return {
                'categories': categories,
                'scales': scales
            }

def start_questionnaire_mysql(external_user_id=None, template_id=None) -> str:
    """
    开始填写量表
    返回 recordId
    """
    import uuid
    
    with get_mysql_connection() as connection:
        with get_mysql_cursor(connection) as cursor:
            # 获取模板信息
            cursor.execute('''
                SELECT questionnaire_name, group_type, apply_department
                FROM crm_questionnaire_template
                WHERE id = %s AND del_flag = '0'
            ''', (template_id,))
            template = cursor.fetchone()
            
            if not template:
                raise ValueError(f"模板不存在: {template_id}")
            
            questionnaire_name, group_type, apply_department = template
            
            # 生成记录ID（使用雪花算法风格的ID）
            import time
            import random
            record_id = str(int(time.time() * 1000) + random.randint(1000, 9999))
            
            # 插入或更新用户记录
            cursor.execute('''
                INSERT INTO crm_questionnaire_user_record (
                    id, external_user_id, questionnaire_name, 
                    group_type, apply_department, status, 
                    del_flag, create_time, update_time
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    status = '1',
                    update_time = VALUES(update_time)
            ''', (
                record_id, external_user_id, questionnaire_name,
                group_type, apply_department, '1',
                '0', now_iso(), now_iso()
            ))
            
            connection.commit()
            return record_id

def submit_questionnaire_mysql(questionnaire_id: str, answers: dict[str, Any]) -> dict[str, Any]:
    """
    提交问卷
    """
    import json
    import time
    import random
    
    with get_mysql_connection() as connection:
        with get_mysql_cursor(connection) as cursor:
            # 开始事务
            connection.start_transaction()
            
            try:
                # 1. 首先检查记录是否存在
                cursor.execute('''
                    SELECT id, questionnaire_name
                    FROM crm_questionnaire_user_record
                    WHERE id = %s AND del_flag = '0'
                ''', (questionnaire_id,))
                
                record = cursor.fetchone()
                if not record:
                    raise ValueError(f"记录不存在: {questionnaire_id}")
                
                record_id, questionnaire_name = record
                
                # 2. 逐题写入用户作答到 crm_questionnaire_user_subject_record
                for answer in answers:
                    subject_id = answer.get('subjectId') or answer.get('id')
                    question_answers = answer.get('answers', [])
                    
                    if not subject_id:
                        continue
                    
                    # 获取题目信息
                    cursor.execute('''
                        SELECT subject_type, subject_title, subject_content, enable_score, score_rules, 
                               score, is_required, sort_order, apply_department, tenant_id
                        FROM crm_questionnaire_template_subject
                        WHERE id = %s AND del_flag = '0'
                    ''', (subject_id,))
                    
                    subject = cursor.fetchone()
                    if not subject:
                        continue
                    
                    subject_type, subject_title, subject_content, enable_score, score_rules, score, is_required, sort_order, apply_department, tenant_id = subject
                    
                    # 计算得分
                    result_score = 0
                    if enable_score == 'Y' and score_rules:
                        try:
                            rules = json.loads(score_rules)
                            for q_answer in question_answers:
                                for rule in rules:
                                    if rule.get('label') == q_answer:
                                        result_score += rule.get('score', 0)
                                        break
                        except:
                            pass
                    
                    # 生成作答记录ID
                    subject_record_id = str(int(time.time() * 1000) + random.randint(1000, 9999))
                    
                    # 构建用户答案内容
                    user_answer_content = {
                        "original": subject_content,
                        "answers": question_answers
                    }
                    
                    # 插入或更新用户作答记录
                    cursor.execute('''
                        INSERT INTO crm_questionnaire_user_subject_record (
                            id, record_id, subject_id, subject_type, subject_title, 
                            file_num, subject_content, field_props, enable_score, score_rules, 
                            score, is_base_subject, is_required, sort_order, apply_department, 
                            del_flag, create_time, update_time, version, tenant_id
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            subject_content = VALUES(subject_content),
                            score = VALUES(score),
                            update_time = VALUES(update_time)
                    ''', (
                        subject_record_id, record_id, subject_id, subject_type, subject_title,
                        0, json.dumps(user_answer_content), None, enable_score, score_rules,
                        result_score, '0', is_required, sort_order, apply_department,
                        '0', now_iso(), now_iso(), 1, tenant_id or 0
                    ))
                
                # 3. 更新用户记录状态
                cursor.execute('''
                    UPDATE crm_questionnaire_user_record
                    SET status = '2', update_time = %s
                    WHERE id = %s AND del_flag = '0'
                ''', (now_iso(), record_id))
                
                # 4. 提交事务
                connection.commit()
                
                # 5. 返回结果
                return {
                    "success": True,
                    "recordId": record_id
                }
                
            except Exception as e:
                # 回滚事务
                connection.rollback()
                raise e

def get_questionnaire_report_mysql(questionnaire_id: str) -> Optional[dict[str, Any]]:
    with get_mysql_connection() as connection:
        with get_mysql_cursor(connection) as cursor:
            cursor.execute(
                '''
                SELECT report
                FROM questionnaires
                WHERE id = %s AND status = 'completed'
                ''',
                (questionnaire_id,)
            )
            result = cursor.fetchone()
            if result and result[0]:
                import json
                return json.loads(result[0])
            return None

# 预约提醒相关操作
def save_appointment_reminder_mysql(
    *, 
    appointment_id: str, 
    user_id: Optional[str], 
    openid: Optional[str], 
    doctor_name: str, 
    clinic_time: str, 
    clinic_location: str, 
    remark: Optional[str] = None,
    status: str = 'pending'
) -> None:
    with get_mysql_connection() as connection:
        with get_mysql_cursor(connection) as cursor:
            cursor.execute(
                '''
                INSERT INTO appointment_reminders (
                    id, user_id, openid, doctor_name, clinic_time, clinic_location, remark, status, created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    user_id = VALUES(user_id),
                    openid = VALUES(openid),
                    doctor_name = VALUES(doctor_name),
                    clinic_time = VALUES(clinic_time),
                    clinic_location = VALUES(clinic_location),
                    remark = VALUES(remark),
                    status = VALUES(status),
                    updated_at = VALUES(updated_at)
                ''',
                (
                    appointment_id, user_id, openid, doctor_name, clinic_time, clinic_location, 
                    remark, status, now_iso(), now_iso()
                )
            )
            connection.commit()

def get_appointment_reminder_mysql(appointment_id: str) -> Optional[dict[str, Any]]:
    with get_mysql_connection() as connection:
        with get_mysql_cursor(connection) as cursor:
            cursor.execute(
                '''
                SELECT id, user_id, openid, doctor_name, clinic_time, clinic_location, remark, status, created_at, updated_at
                FROM appointment_reminders
                WHERE id = %s
                ''',
                (appointment_id,)
            )
            result = cursor.fetchone()
            if result:
                return {
                    'id': result[0],
                    'userId': result[1],
                    'openid': result[2],
                    'doctorName': result[3],
                    'clinicTime': result[4],
                    'clinicLocation': result[5],
                    'remark': result[6],
                    'status': result[7],
                    'createdAt': result[8],
                    'updatedAt': result[9]
                }
            return None

# 订阅记录相关操作
def list_subscription_records_mysql(openid: str) -> list[dict[str, Any]]:
    with get_mysql_connection() as connection:
        with get_mysql_cursor(connection) as cursor:
            cursor.execute(
                '''
                SELECT id, openid, template_id, status, created_at, updated_at
                FROM subscription_records
                WHERE openid = %s
                ORDER BY created_at DESC
                ''',
                (openid,)
            )
            return [
                {
                    'id': row[0],
                    'openid': row[1],
                    'templateId': row[2],
                    'status': row[3],
                    'createdAt': row[4],
                    'updatedAt': row[5]
                }
                for row in cursor.fetchall()
            ]

# 用户相关操作
def upsert_user_mysql(*args, **kwargs):
    try:
        with get_mysql_connection() as connection:
            with get_mysql_cursor(connection) as cursor:
                # 简化实现，实际项目中需要根据具体表结构调整
                pass
    except Exception as e:
        print(f'upsert_user_mysql 失败（非致命错误）: {e}')

# 订阅相关操作
def upsert_subscription_record_mysql(*args, **kwargs):
    try:
        with get_mysql_connection() as connection:
            with get_mysql_cursor(connection) as cursor:
                # 简化实现，实际项目中需要根据具体表结构调整
                pass
    except Exception as e:
        print(f'upsert_subscription_record_mysql 失败（非致命错误）: {e}')

# 元数据相关操作
def get_meta_mysql(*args, **kwargs):
    try:
        with get_mysql_connection() as connection:
            with get_mysql_cursor(connection) as cursor:
                # 简化实现，实际项目中需要根据具体表结构调整
                pass
    except Exception as e:
        print(f'get_meta_mysql 失败（非致命错误）: {e}')


def set_meta_mysql(*args, **kwargs):
    try:
        with get_mysql_connection() as connection:
            with get_mysql_cursor(connection) as cursor:
                # 简化实现，实际项目中需要根据具体表结构调整
                pass
    except Exception as e:
        print(f'set_meta_mysql 失败（非致命错误）: {e}')

# 发送日志相关操作
def insert_send_log_mysql(*args, **kwargs):
    try:
        with get_mysql_connection() as connection:
            with get_mysql_cursor(connection) as cursor:
                # 简化实现，实际项目中需要根据具体表结构调整
                pass
    except Exception as e:
        print(f'insert_send_log_mysql 失败（非致命错误）: {e}')


def mark_subscription_sent_mysql(*args, **kwargs):
    try:
        with get_mysql_connection() as connection:
            with get_mysql_cursor(connection) as cursor:
                # 简化实现，实际项目中需要根据具体表结构调整
                pass
    except Exception as e:
        print(f'mark_subscription_sent_mysql 失败（非致命错误）: {e}')

# 舌诊报告相关操作
def save_tongue_report_mysql(*args, **kwargs):
    try:
        with get_mysql_connection() as connection:
            with get_mysql_cursor(connection) as cursor:
                # 简化实现，实际项目中需要根据具体表结构调整
                pass
    except Exception as e:
        print(f'save_tongue_report_mysql 失败（非致命错误）: {e}')


def get_tongue_report_mysql(*args, **kwargs):
    try:
        with get_mysql_connection() as connection:
            with get_mysql_cursor(connection) as cursor:
                # 简化实现，实际项目中需要根据具体表结构调整
                pass
    except Exception as e:
        print(f'get_tongue_report_mysql 失败（非致命错误）: {e}')

# 订阅相关操作
def find_sendable_subscription_mysql(*args, **kwargs):
    try:
        with get_mysql_connection() as connection:
            with get_mysql_cursor(connection) as cursor:
                # 简化实现，实际项目中需要根据具体表结构调整
                pass
    except Exception as e:
        print(f'find_sendable_subscription_mysql 失败（非致命错误）: {e}')

# AI回复记录相关操作
def save_ai_reply_mysql(
    *, 
    reply_id: str, 
    user_id: Optional[str], 
    openid: Optional[str], 
    assistant_id: str, 
    question: str, 
    content: str, 
    chat_id: Optional[str]
) -> None:
    try:
        with get_mysql_connection() as connection:
            with get_mysql_cursor(connection) as cursor:
                cursor.execute(
                    '''
                    INSERT INTO ai_reply_records (
                        reply_id, user_id, openid, assistant_id, question, content, chat_id, created_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        user_id = VALUES(user_id),
                        openid = VALUES(openid),
                        assistant_id = VALUES(assistant_id),
                        question = VALUES(question),
                        content = VALUES(content),
                        chat_id = VALUES(chat_id),
                        created_at = VALUES(created_at)
                    ''',
                    (reply_id, user_id, openid, assistant_id, question, content, chat_id, now_iso())
                )
                connection.commit()
    except Exception as e:
        print(f'保存 AI 回复记录失败（非致命错误）: {e}')


def get_ai_reply_mysql(reply_id: str) -> Optional[dict[str, Any]]:
    try:
        with get_mysql_connection() as connection:
            with get_mysql_cursor(connection) as cursor:
                cursor.execute(
                    '''
                    SELECT reply_id, user_id, openid, assistant_id, question, content, chat_id, created_at
                    FROM ai_reply_records
                    WHERE reply_id = %s
                    ''',
                    (reply_id,)
                )
                result = cursor.fetchone()
                if result:
                    return {
                        'reply_id': result[0],
                        'user_id': result[1],
                        'openid': result[2],
                        'assistant_id': result[3],
                        'question': result[4],
                        'content': result[5],
                        'chat_id': result[6],
                        'created_at': result[7]
                    }
                return None
    except Exception as e:
        print(f'获取 AI 回复记录失败（非致命错误）: {e}')
        return None