import json
import json
import re
from typing import Any, Optional
from datetime import datetime, timezone, timedelta
import mysql.connector
from mysql.connector import Error
from config import config
from urllib import error as urllib_error
from urllib import request as urllib_request

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


def now_mysql() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')


CHINA_TZ = timezone(timedelta(hours=8))


def _to_int_or_none(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        value_str = str(value).strip()
        if value_str == '':
            return None
        return int(value_str)
    except Exception:
        return None


def _format_datetime_shanghai(value: Any) -> str:
    if value is None or value == '':
        return ''

    dt: Optional[datetime] = None
    if isinstance(value, datetime):
      dt = value
    else:
        text = str(value).strip()
        if not text:
            return ''

        parsed_formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%f'
        ]
        for fmt in parsed_formats:
            try:
                dt = datetime.strptime(text, fmt)
                break
            except Exception:
                continue

        if dt is None:
            try:
                dt = datetime.fromisoformat(text.replace('Z', '+00:00'))
            except Exception:
                return text

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(CHINA_TZ).strftime('%Y-%m-%d %H:%M:%S')


def _sanitize_questionnaire_text(text: Any) -> str:
    normalized = str(text or '')
    normalized = normalized.replace('**', '')
    normalized = normalized.replace('```', '')
    normalized = re.sub(r'(?m)^\s*#+\s*', '', normalized)
    return normalized.strip()


def _ensure_questionnaire_record_table_mysql(cursor) -> None:
    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS questionnaire_record (
            record_id VARCHAR(64) PRIMARY KEY,
            questionnaire_id VARCHAR(64) NOT NULL,
            questionnaire_name VARCHAR(255) NOT NULL,
            doctor_id BIGINT NULL,
            patient_id BIGINT NULL,
            disease_type VARCHAR(64) NULL,
            visit_type VARCHAR(32) NULL,
            answers_json LONGTEXT NOT NULL,
            analysis_text LONGTEXT NOT NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            INDEX idx_questionnaire_record_patient_created (patient_id, created_at),
            INDEX idx_questionnaire_record_doctor_created (doctor_id, created_at),
            INDEX idx_questionnaire_record_questionnaire (questionnaire_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        '''
    )


def _ensure_questionnaire_record_columns_mysql(cursor) -> None:
    for column_sql in [
        'ADD COLUMN disease_type VARCHAR(64) NULL',
        'ADD COLUMN visit_type VARCHAR(32) NULL'
    ]:
        try:
            cursor.execute(f'ALTER TABLE questionnaire_record {column_sql}')
        except Error as exc:
            if getattr(exc, 'errno', None) not in (1060, 1091):
                raise


def _json_loads_safe(raw_value: Any, default: Any = None) -> Any:
    if raw_value is None or raw_value == '':
        return default
    if isinstance(raw_value, (dict, list)):
        return raw_value
    try:
        return json.loads(raw_value)
    except Exception:
        return default


def _resolve_questionnaire_answer_text(options: Any, answer_value: Any) -> str:
    raw_answer = '' if answer_value is None else str(answer_value).strip()
    if raw_answer == '':
        return '未填写'

    parsed_options = options if isinstance(options, list) else _json_loads_safe(options, [])
    if isinstance(parsed_options, list):
        for option in parsed_options:
            if not isinstance(option, dict):
                continue
            option_value = option.get('value')
            if option_value is not None and str(option_value).strip() == raw_answer:
                return str(option.get('label') or option.get('text') or option.get('title') or raw_answer)

        if raw_answer.isdigit():
            option_index = int(raw_answer) - 1
            if 0 <= option_index < len(parsed_options):
                option = parsed_options[option_index]
                if isinstance(option, dict):
                    return str(option.get('label') or option.get('text') or option.get('title') or raw_answer)

    return raw_answer


def _build_questionnaire_analysis_text(questionnaire_name: str, questions: list[dict[str, Any]], answers: list[dict[str, Any]]) -> str:
    answers_map: dict[str, str] = {}
    for answer in answers:
        subject_id = answer.get('subjectId') or answer.get('id') or answer.get('subject_id')
        if subject_id is None:
            continue
        answers_map[str(subject_id)] = str(answer.get('value') if answer.get('value') is not None else answer.get('answer') or '')

    answered_count = 0
    summary_lines: list[str] = []
    for index, question in enumerate(questions, start=1):
        subject_id = str(question.get('subjectId') or question.get('id') or '')
        title = str(question.get('title') or '')
        answer_value = answers_map.get(subject_id, '')
        answer_text = _resolve_questionnaire_answer_text(question.get('options'), answer_value)
        if answer_text != '未填写':
            answered_count += 1
        summary_lines.append(f"{index}. {title}: {answer_text}")

    lines = [
        f"量表名称：{questionnaire_name or '量表'}",
        f"填写题数：{answered_count}/{len(questions)}",
        '',
        '答题摘要：',
        *summary_lines,
        '',
        '提示：本分析仅供医生参考，不构成诊断依据。'
    ]
    return '\n'.join(lines).strip()


def _get_doctor_name_mysql(doctor_id: Optional[int]) -> str:
    doctor_id_int = _to_int_or_none(doctor_id)
    if doctor_id_int is None:
        return ''

    with get_mysql_connection() as connection:
        with get_mysql_cursor(connection) as cursor:
            cursor.execute(
                '''
                SELECT COALESCE(display_name, doctor_name, '')
                FROM doctor_profile
                WHERE id = %s
                LIMIT 1
                ''',
                (doctor_id_int,)
            )
            row = cursor.fetchone()
            return str(row[0]) if row and row[0] is not None else ''


def _get_siliconflow_config() -> dict[str, Any]:
    return dict(config.get('siliconflow', {}) or {})


def _ensure_questionnaire_disclaimer(text: str) -> str:
    disclaimer = (
        '本量表结果仅为个人填写信息的客观呈现，不构成任何诊断依据。\n'
        '所有症状描述均为自我报告，实际临床判断需结合面诊、体检及其他专业评估工具。\n'
        '如后续需进一步沟通，请确保携带完整病史资料，并如实反馈当前身心状态。'
    )

    normalized = str(text or '').strip()
    if disclaimer in normalized:
        return normalized

    if normalized:
        return f'{normalized}\n\n{disclaimer}'

    return disclaimer


def _ensure_questionnaire_disclaimer_v2(text: str) -> str:
    disclaimer = (
        '本量表结果仅为个人填写信息的客观呈现，不构成任何诊断依据。\n'
        '所有症状描述均为自我报告，实际临床判断需结合面诊、体检及其他专业评估工具。\n'
        '如后续需进一步沟通，请确保携带完整病史资料，并如实反馈当前身心状态。'
    )

    normalized = _sanitize_questionnaire_text(text)
    if disclaimer in normalized:
        return normalized

    if normalized:
        return f'{normalized}\n\n{disclaimer}'

    return disclaimer


def generate_questionnaire_analysis_by_ai(record_data: dict[str, Any]) -> str:
    """
    调用硅基流动生成量表 AI 分析。
    返回生成内容；失败时抛出异常，由上层回退到基础分析。
    """
    siliconflow = _get_siliconflow_config()
    if not siliconflow.get('enabled', False):
        raise RuntimeError('siliconflow 未启用')

    api_key = str(siliconflow.get('api_key') or '').strip()
    if not api_key:
        raise RuntimeError('siliconflow.api_key 不能为空')

    base_url = str(siliconflow.get('base_url') or 'https://api.siliconflow.cn/v1').rstrip('/')
    chat_path = str(siliconflow.get('chat_completions_path') or '/chat/completions').strip()
    if not chat_path.startswith('/'):
        chat_path = f'/{chat_path}'
    url = f'{base_url}{chat_path}'

    model = str(siliconflow.get('model') or 'deepseek-ai/DeepSeek-V4-Flash')
    try:
        temperature = float(siliconflow.get('temperature', 0.3))
    except Exception:
        temperature = 0.3
    try:
        max_tokens = int(siliconflow.get('max_tokens', 1800))
    except Exception:
        max_tokens = 1800
    timeout_seconds = int(siliconflow.get('timeout_seconds') or 60)

    questionnaire_name = str(record_data.get('questionnaire_name') or '')
    doctor_name = str(record_data.get('doctor_name') or '')
    patient_id = str(record_data.get('patient_id') or '')
    answers_json = record_data.get('answers_json') or []
    questions = record_data.get('questions') or []
    existing_summary = str(record_data.get('existing_summary') or '')

    system_prompt = (
        '你是一名医疗量表分析助手。'
        '你只能基于用户自填内容做客观整理和健康提示，不得诊断疾病，不得给出治疗方案，不得指导用药，不得承诺疗效。'
        '请严格输出以下五个部分，且按顺序生成：'
        '一、信息整理摘要；二、总体评估；三、分项建议；四、行动指南；五、注意事项。'
        '注意事项必须原样包含以下三句免责声明：'
        '本量表结果仅为个人填写信息的客观呈现，不构成任何诊断依据。'
        '所有症状描述均为自我报告，实际临床判断需结合面诊、体检及其他专业评估工具。'
        '如后续需进一步沟通，请确保携带完整病史资料，并如实反馈当前身心状态。'
        '除了上述内容，不要输出多余的前后缀说明。'
    )

    system_prompt = (
        '你是一名医疗量表分析助手。'
        '你只能基于用户自填内容做客观整理和健康提示，不得诊断疾病，不得给出治疗方案，不得指导用药，不得承诺疗效。'
        '请严格只输出普通中文文本，不要输出 Markdown 格式，不要使用 ** 加粗，不要使用 # 标题，不要使用 ``` 代码块。'
        '输出内容必须且只能按以下五个一级标题顺序生成：'
        '一、信息整理摘要；二、总体评估；三、分项建议；四、行动指南；五、注意事项。'
        '每个一级标题下用普通中文分行描述，不要输出多余前后缀说明。'
        '注意事项必须原样包含以下三句话：'
        '本量表结果仅为个人填写信息的客观呈现，不构成任何诊断依据。'
        '所有症状描述均为自我报告，实际临床判断需结合面诊、体检及其他专业评估工具。'
        '如后续需进一步沟通，请确保携带完整病史资料，并如实反馈当前身心状态。'
    )

    user_payload = {
        'questionnaire_name': questionnaire_name,
        'doctor_name': doctor_name,
        'patient_id': patient_id,
        'existing_summary': existing_summary,
        'questions': questions,
        'answers_json': answers_json,
        'instruction': [
            '请结合量表题目、选项文本、用户答案、医生信息，生成一份结构化分析。',
            '只能基于已提供内容做客观描述与健康提示。',
            '若信息不足，请在对应部分明确说明，不要编造。',
            '注意事项必须包含三句免责声明，且原文一致。'
        ]
    }

    payload = {
        'model': model,
        'temperature': temperature,
        'max_tokens': max_tokens,
        'stream': False,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': json.dumps(user_payload, ensure_ascii=False)}
        ]
    }

    req = urllib_request.Request(
        url=url,
        data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        },
        method='POST'
    )

    try:
        with urllib_request.urlopen(req, timeout=timeout_seconds) as resp:
            raw = resp.read().decode('utf-8', errors='replace')
    except urllib_error.HTTPError as exc:
        body = exc.read().decode('utf-8', errors='replace')
        raise RuntimeError(f'SiliconFlow HTTP {exc.code}: {body[:500]}') from exc
    except Exception as exc:
        raise RuntimeError(f'SiliconFlow 调用失败: {exc}') from exc

    try:
        response_data = json.loads(raw)
    except Exception as exc:
        raise RuntimeError(f'SiliconFlow 返回不是有效 JSON: {raw[:500]}') from exc

    content = (
        response_data.get('choices', [{}])[0]
        .get('message', {})
        .get('content', '')
    )
    content = str(content or '').strip()
    if not content:
        raise RuntimeError('SiliconFlow 返回内容为空')

    return _ensure_questionnaire_disclaimer_v2(content)


def get_doctors_list_mysql() -> dict[str, Any]:
    with get_mysql_connection() as connection:
        with get_mysql_cursor(connection) as cursor:
            cursor.execute(
                '''
                SELECT
                    id,
                    doctor_name,
                    display_name,
                    department,
                    title,
                    avatar_url,
                    sort_order
                FROM doctor_profile
                WHERE status = 1
                ORDER BY sort_order, id
                '''
            )
            rows = cursor.fetchall() or []

            doctors: list[dict[str, Any]] = []
            for row in rows:
                doctor_id, doctor_name, display_name, department, title, avatar_url, sort_order = row
                doctors.append(
                    {
                        'doctorId': int(doctor_id),
                        'doctorName': display_name or doctor_name or str(doctor_id),
                        'department': department or '',
                        'title': title or '',
                        'avatarUrl': avatar_url or '',
                        'sortOrder': int(sort_order or 0),
                    }
                )

            return {
                'success': True,
                'data': doctors,
            }


def _get_patient_doctor_visit_state_mysql(cursor, patient_id: int, doctor_id: int) -> int:
    cursor.execute(
        '''
        SELECT first_visit_completed
        FROM patient_doctor_visit_state
        WHERE patient_id = %s AND doctor_id = %s
        LIMIT 1
        ''',
        (patient_id, doctor_id)
    )
    row = cursor.fetchone()
    if not row:
        return 0
    try:
        return int(row[0] or 0)
    except Exception:
        return 0


def get_doctor_questionnaires_by_doctor_mysql(*, doctor_id: int, patient_id: int) -> dict[str, Any]:
    """
    按医生和患者返回量表列表。

    规则：
    - 首诊未完成：返回 first_only + all_visits
    - 首诊已完成：仅返回 all_visits
    """
    doctor_id_int = _to_int_or_none(doctor_id)
    patient_id_int = _to_int_or_none(patient_id)
    if doctor_id_int is None:
        raise ValueError('doctorId 必须是有效整数')
    if patient_id_int is None:
        raise ValueError('patientId 必须是有效整数')

    with get_mysql_connection() as connection:
        with get_mysql_cursor(connection) as cursor:
            cursor.execute(
                '''
                SELECT id, doctor_name, display_name, department, status
                FROM doctor_profile
                WHERE id = %s
                LIMIT 1
                ''',
                (doctor_id_int,)
            )
            doctor_row = cursor.fetchone()
            if not doctor_row:
                raise ValueError(f'未找到医生ID: {doctor_id_int}')

            doctor_status = doctor_row[4]
            if str(doctor_status) != '1':
                raise ValueError('医生未启用')

            first_visit_completed = _get_patient_doctor_visit_state_mysql(cursor, patient_id_int, doctor_id_int)
            is_first_visit = int(first_visit_completed or 0) == 0

            cursor.execute(
                '''
                SELECT
                    b.id AS bind_id,
                    b.doctor_id,
                    d.doctor_name,
                    b.questionnaire_id,
                    qt.questionnaire_name,
                    b.visit_stage,
                    b.sort_order,
                    b.source_binding_id
                FROM doctor_questionnaire_bind b
                JOIN doctor_profile d ON d.id = b.doctor_id
                JOIN crm_questionnaire_template qt ON qt.id = b.questionnaire_id
                WHERE b.doctor_id = %s
                  AND b.status = 1
                  AND d.status = 1
                  AND (qt.del_flag = '0' OR qt.del_flag IS NULL)
                  AND (qt.status = '0' OR qt.status IS NULL)
                  AND (
                        %s = 0
                        OR b.visit_stage = 'all_visits'
                  )
                ORDER BY
                    CASE b.visit_stage
                        WHEN 'first_only' THEN 0
                        ELSE 1
                    END,
                    b.sort_order,
                    b.id
                ''',
                (doctor_id_int, first_visit_completed)
            )
            rows = cursor.fetchall()

            questionnaires: list[dict[str, Any]] = []
            for row in rows:
                bind_id, bind_doctor_id, doctor_name, questionnaire_id, questionnaire_name, visit_stage, sort_order, source_binding_id = row
                questionnaires.append(
                    {
                        'bindId': str(bind_id),
                        'doctorId': int(bind_doctor_id),
                        'doctorName': doctor_name,
                        'questionnaireId': str(questionnaire_id),
                        'questionnaireName': questionnaire_name,
                        'visitStage': visit_stage,
                        'sortOrder': int(sort_order or 0),
                        'sourceBindingId': str(source_binding_id) if source_binding_id is not None else '',
                        'required': visit_stage == 'first_only',
                    }
                )

            return {
                'doctorId': doctor_id_int,
                'doctorName': doctor_row[1] or doctor_row[2] or str(doctor_id_int),
                'isFirstVisit': is_first_visit,
                'questionnaires': questionnaires,
            }


def _maybe_mark_patient_doctor_visit_completed_mysql(
    cursor,
    *,
    patient_id: int,
    doctor_id: int,
    questionnaire_id: Optional[int] = None
) -> None:
    """
    根据该患者在该医生名下的提交完成情况，更新初诊状态。
    """
    questionnaire_id_int = _to_int_or_none(questionnaire_id)
    print(f"[questionnaire-submit] patientId={patient_id} doctorId={doctor_id} questionnaireId={questionnaire_id_int}")
    if questionnaire_id_int is None:
        return

    cursor.execute(
        '''
        SELECT visit_stage
        FROM doctor_questionnaire_bind
        WHERE doctor_id = %s
          AND questionnaire_id = %s
          AND status = 1
        LIMIT 1
        ''',
        (doctor_id, questionnaire_id_int)
    )
    current_bind = cursor.fetchone()
    if not current_bind:
        print(f"[questionnaire-submit] bind not found for questionnaire_id={questionnaire_id_int}")
        return

    current_visit_stage = str(current_bind[0] or '')
    print(f"[questionnaire-submit] bind.visit_stage={current_visit_stage}")

    cursor.execute(
        '''
        SELECT questionnaire_id, visit_stage
        FROM doctor_questionnaire_bind
        WHERE doctor_id = %s AND status = 1
        ''',
        (doctor_id,)
    )
    active_binds = cursor.fetchall() or []
    first_only_ids = {
        int(row[0])
        for row in active_binds
        if str(row[1]) == 'first_only'
    }

    if current_visit_stage != 'first_only':
        if first_only_ids:
            return

        cursor.execute(
            '''
            SELECT DISTINCT user_questionnaire_id
            FROM crm_questionnaire_user_record
            WHERE user_id = %s
              AND external_user_id = %s
              AND del_flag = '0'
              AND status = '2'
              AND user_questionnaire_id IS NOT NULL
            ''',
            (doctor_id, str(patient_id))
        )
        completed_rows = cursor.fetchall() or []
        completed_ids = {int(row[0]) for row in completed_rows if row and row[0] is not None}
        if len(completed_ids) == 0:
            return

        cursor.execute(
            '''
            INSERT INTO patient_doctor_visit_state
            (patient_id, doctor_id, first_visit_completed, first_visit_completed_at)
            VALUES (%s, %s, 1, NOW())
            ON DUPLICATE KEY UPDATE
                first_visit_completed = 1,
                first_visit_completed_at = COALESCE(first_visit_completed_at, VALUES(first_visit_completed_at)),
                updated_at = CURRENT_TIMESTAMP
            ''',
            (patient_id, doctor_id)
        )
        return

    cursor.execute(
        '''
        SELECT DISTINCT user_questionnaire_id
        FROM crm_questionnaire_user_record
        WHERE user_id = %s
          AND external_user_id = %s
          AND del_flag = '0'
          AND status = '2'
          AND user_questionnaire_id IS NOT NULL
        ''',
        (doctor_id, str(patient_id))
    )
    completed_rows = cursor.fetchall() or []
    completed_ids = {int(row[0]) for row in completed_rows if row and row[0] is not None}
    
    print(f"[questionnaire-submit] first_only_ids={first_only_ids}")
    print(f"[questionnaire-submit] completed_ids={completed_ids}")
    print(f"[questionnaire-submit] total_first_only={len(first_only_ids)}")
    print(f"[questionnaire-submit] completed_first_only={len(completed_ids & first_only_ids) if first_only_ids else 0}")

    if first_only_ids:
        should_complete = first_only_ids.issubset(completed_ids)
    else:
        should_complete = len(completed_ids) > 0

    if not should_complete:
        print(f"[questionnaire-submit] should_complete=False, return")
        return

    print(f"[questionnaire-submit] marking first visit as completed")
    cursor.execute(
        '''
        INSERT INTO patient_doctor_visit_state
        (patient_id, doctor_id, first_visit_completed, first_visit_completed_at)
        VALUES (%s, %s, 1, NOW())
        ON DUPLICATE KEY UPDATE
            first_visit_completed = 1,
            first_visit_completed_at = COALESCE(first_visit_completed_at, VALUES(first_visit_completed_at)),
            updated_at = CURRENT_TIMESTAMP
        ''',
        (patient_id, doctor_id)
    )


def get_questionnaire_detail_with_binding_mysql(questionnaire_id: str) -> Optional[dict[str, Any]]:
    """
    优先按 user_questionnaire_id 获取模板明细，避免同名模板串表。
    """
    with get_mysql_connection() as connection:
        with get_mysql_cursor(connection) as cursor:
            cursor.execute(
                '''
                SELECT
                    u.id,
                    u.external_user_id,
                    u.questionnaire_name,
                    u.group_type,
                    u.apply_department,
                    u.status,
                    u.create_time,
                    u.update_time,
                    u.user_questionnaire_id
                FROM crm_questionnaire_user_record u
                WHERE u.id = %s AND u.del_flag = '0'
                ''',
                (questionnaire_id,)
            )

            record = cursor.fetchone()
            if not record:
                return None

            record_id, external_user_id, questionnaire_name, group_type, apply_department, status, create_time, update_time, user_questionnaire_id = record
            template_id = user_questionnaire_id

            if not template_id and questionnaire_name:
                cursor.execute(
                    '''
                    SELECT id
                    FROM crm_questionnaire_template
                    WHERE questionnaire_name = %s
                      AND apply_department = %s
                      AND del_flag = '0'
                    ORDER BY id
                    LIMIT 1
                    ''',
                    (questionnaire_name, apply_department)
                )
                template_row = cursor.fetchone()
                if template_row:
                    template_id = template_row[0]

            questions = []
            if template_id:
                cursor.execute(
                    '''
                    SELECT
                        id, subject_type, subject_title, subject_content,
                        is_required, sort_order
                    FROM crm_questionnaire_template_subject
                    WHERE template_id = %s AND del_flag = '0'
                    ORDER BY sort_order, id
                    ''',
                    (template_id,)
                )

                import json
                for subject in cursor.fetchall():
                    subject_id, subject_type, subject_title, subject_content, is_required, sort_order = subject
                    try:
                        content = json.loads(subject_content) if subject_content else []
                    except Exception:
                        content = []
                    questions.append(
                        {
                            'id': str(subject_id),
                            'type': subject_type,
                            'title': subject_title,
                            'options': content,
                            'required': is_required == 'Y',
                            'order': sort_order
                        }
                    )

            return {
                'recordId': str(record_id),
                'templateId': str(template_id) if template_id else '',
                'questionnaireName': questionnaire_name,
                'status': status,
                'questions': questions,
                'meta': {
                    'userQuestionnaireId': str(user_questionnaire_id) if user_questionnaire_id is not None else '',
                    'externalUserId': str(external_user_id or ''),
                    'groupType': group_type,
                    'applyDepartment': apply_department,
                }
            }


def start_questionnaire_with_binding_mysql(
    external_user_id=None,
    template_id=None,
    doctor_id=None,
    patient_id=None
) -> str:
    """
    在兼容旧流程的基础上，补充医生/患者上下文。
    """
    doctor_id_int = _to_int_or_none(doctor_id)
    patient_value = str(patient_id if patient_id is not None else external_user_id or '').strip()

    # 没有医生上下文时，保持旧流程不变
    if doctor_id_int is None:
        return start_questionnaire_mysql(external_user_id=external_user_id, template_id=template_id)

    if not patient_value:
        raise ValueError('patientId / externalUserId 不能为空')

    with get_mysql_connection() as connection:
        with get_mysql_cursor(connection) as cursor:
            cursor.execute(
                '''
                SELECT questionnaire_name, group_type, apply_department
                FROM crm_questionnaire_template
                WHERE id = %s AND del_flag = '0'
                ''',
                (template_id,)
            )
            template = cursor.fetchone()
            if not template:
                raise ValueError(f'模板不存在: {template_id}')

            questionnaire_name, group_type, apply_department = template

            cursor.execute(
                '''
                SELECT id
                FROM crm_questionnaire_user_record
                WHERE external_user_id = %s
                  AND user_id = %s
                  AND user_questionnaire_id = %s
                  AND del_flag = '0'
                LIMIT 1
                ''',
                (patient_value, doctor_id_int, _to_int_or_none(template_id))
            )
            existing = cursor.fetchone()
            if existing:
                return str(existing[0])

            import time
            import random
            record_id = str(int(time.time() * 1000) + random.randint(1000, 9999))

            cursor.execute(
                '''
                INSERT INTO crm_questionnaire_user_record (
                    id, user_id, user_questionnaire_id, external_user_id, questionnaire_name,
                    group_type, apply_department, status,
                    del_flag, create_time, update_time
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    status = '1',
                    update_time = VALUES(update_time)
                ''',
                (
                    record_id,
                    doctor_id_int,
                    _to_int_or_none(template_id),
                    patient_value,
                    questionnaire_name,
                    group_type,
                    apply_department,
                    '1',
                    '0',
                    now_iso(),
                    now_iso()
                )
            )
            connection.commit()
            return record_id


def submit_questionnaire_with_binding_mysql(
    record_id: str,
    answers: dict[str, Any],
    *,
    doctor_id=None,
    patient_id=None,
    questionnaire_id=None,
    disease_type=None,
    visit_type=None
) -> dict[str, Any]:
    """
    兼容旧提交逻辑，并在成功后回写 patient_doctor_visit_state。
    """
    result = submit_questionnaire_mysql(record_id, answers)
    if not result or not result.get('success'):
        return result

    doctor_id_int = _to_int_or_none(doctor_id)
    patient_id_int = _to_int_or_none(patient_id)
    questionnaire_id_text = str(questionnaire_id or '').strip() or None

    record_summary = save_questionnaire_record_mysql(
        record_id=str(record_id),
        answers=answers,
        doctor_id=doctor_id_int,
        patient_id=patient_id_int,
        questionnaire_id=questionnaire_id_text,
        disease_type=disease_type,
        visit_type=visit_type
    )
    if record_summary:
        result['analysisText'] = record_summary.get('analysisText', '')
        result['questionnaireRecord'] = record_summary

    with get_mysql_connection() as connection:
        with get_mysql_cursor(connection) as cursor:
            cursor.execute(
                '''
                SELECT user_id, external_user_id, user_questionnaire_id
                FROM crm_questionnaire_user_record
                WHERE id = %s AND del_flag = '0'
                LIMIT 1
                ''',
                (record_id,)
            )
            record = cursor.fetchone()
            if not record:
                return result

            record_user_id, record_external_user_id, _ = record

            if doctor_id_int is None:
                doctor_id_int = _to_int_or_none(record_user_id)
            if patient_id_int is None:
                patient_id_int = _to_int_or_none(record_external_user_id)

            if doctor_id_int is None or patient_id_int is None:
                return result

            _maybe_mark_patient_doctor_visit_completed_mysql(
                cursor,
                patient_id=patient_id_int,
                doctor_id=doctor_id_int,
                questionnaire_id=questionnaire_id
            )
            connection.commit()

    return result


def save_questionnaire_record_mysql(
    *,
    record_id: str,
    answers: list[dict[str, Any]],
    doctor_id: Optional[int] = None,
    patient_id: Optional[int] = None,
    questionnaire_id: Optional[str] = None,
    disease_type: Optional[str] = None,
    visit_type: Optional[str] = None
) -> Optional[dict[str, Any]]:
    """
    保存量表原始答案和分析结果到 questionnaire_record。
    """
    with get_mysql_connection() as connection:
        with get_mysql_cursor(connection) as cursor:
            _ensure_questionnaire_record_table_mysql(cursor)
            _ensure_questionnaire_record_columns_mysql(cursor)
            _ensure_questionnaire_record_columns_mysql(cursor)

            detail = get_questionnaire_detail_with_binding_mysql(record_id)
            if not detail:
                raise ValueError(f'未找到量表记录: {record_id}')

            questions = detail.get('questions') or []
            questionnaire_name = str(detail.get('questionnaireName') or '')
            template_id = str(detail.get('templateId') or questionnaire_id or '')
            doctor_name = str(detail.get('doctorName') or '')
            if not doctor_name and doctor_id is not None:
                cursor.execute(
                    '''
                    SELECT COALESCE(display_name, doctor_name, '')
                    FROM doctor_profile
                    WHERE id = %s
                    LIMIT 1
                    ''',
                    (doctor_id,)
                )
                doctor_row = cursor.fetchone()
                doctor_name = str(doctor_row[0]) if doctor_row and doctor_row[0] is not None else ''

            record_answers = answers if isinstance(answers, list) else []
            base_analysis_text = _build_questionnaire_analysis_text(questionnaire_name, questions, record_answers)
            timestamp = now_mysql()

            cursor.execute(
                '''
                INSERT INTO questionnaire_record (
                    record_id,
                    questionnaire_id,
                    questionnaire_name,
                    doctor_id,
                    patient_id,
                    disease_type,
                    visit_type,
                    answers_json,
                    analysis_text,
                    created_at,
                    updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    questionnaire_id = VALUES(questionnaire_id),
                    questionnaire_name = VALUES(questionnaire_name),
                    doctor_id = VALUES(doctor_id),
                    patient_id = VALUES(patient_id),
                    disease_type = VALUES(disease_type),
                    visit_type = VALUES(visit_type),
                    answers_json = VALUES(answers_json),
                    analysis_text = VALUES(analysis_text),
                    updated_at = VALUES(updated_at)
                ''',
                (
                    str(record_id),
                    str(template_id),
                    questionnaire_name,
                    doctor_id,
                    patient_id,
                    str(disease_type or '').strip() or None,
                    str(visit_type or '').strip() or None,
                    json.dumps(record_answers, ensure_ascii=False),
                    base_analysis_text,
                    timestamp,
                    timestamp
                )
            )
            connection.commit()

            final_analysis_text = base_analysis_text
            ai_error: Optional[Exception] = None
            try:
                ai_analysis_text = generate_questionnaire_analysis_by_ai(
                    {
                        'questionnaire_name': questionnaire_name,
                        'doctor_name': doctor_name,
                        'patient_id': patient_id,
                        'answers_json': record_answers,
                        'questions': questions,
                        'existing_summary': base_analysis_text,
                    }
                )
                if ai_analysis_text.strip():
                    final_analysis_text = ai_analysis_text.strip()
            except Exception as exc:
                ai_error = exc
                print(f'[questionnaire-ai] record_id={record_id} 生成失败: {exc}')
                fallback_note = '分析生成中/生成失败，请稍后重试'
                final_analysis_text = f'{base_analysis_text}\n\n{fallback_note}' if base_analysis_text else fallback_note

            if ai_error is None and final_analysis_text != base_analysis_text:
                print(f'[questionnaire-ai] record_id={record_id} 生成成功')

            cursor.execute(
                '''
                UPDATE questionnaire_record
                SET analysis_text = %s,
                    updated_at = %s
                WHERE record_id = %s
                ''',
                (
                    final_analysis_text,
                    now_mysql(),
                    str(record_id)
                )
            )
            connection.commit()

            return {
                'recordId': str(record_id),
                'questionnaireId': str(template_id),
                'questionnaireName': questionnaire_name,
                'analysisText': final_analysis_text,
                'answersJson': record_answers,
                'doctorId': doctor_id,
                'patientId': patient_id,
                'createdAt': timestamp,
                'updatedAt': now_mysql()
            }


def list_questionnaire_records_mysql(
    *,
    user_id: Any,
    limit: int = 50,
    offset: int = 0
) -> dict[str, Any]:
    """
    获取用户的量表记录列表。
    """
    user_id_int = _to_int_or_none(user_id)
    if user_id_int is None:
        raise ValueError('userId 必须是有效的整数')

    safe_limit = max(1, min(int(limit or 50), 100))
    safe_offset = max(0, int(offset or 0))

    with get_mysql_connection() as connection:
        with get_mysql_cursor(connection) as cursor:
            _ensure_questionnaire_record_table_mysql(cursor)
            _ensure_questionnaire_record_columns_mysql(cursor)

            cursor.execute(
                '''
                SELECT
                    qr.record_id,
                    qr.questionnaire_id,
                    qr.questionnaire_name,
                    qr.doctor_id,
                    COALESCE(dp.display_name, dp.doctor_name, '') AS doctor_name,
                    qr.disease_type,
                    qr.visit_type,
                    qr.answers_json,
                    qr.analysis_text,
                    qr.created_at,
                    qr.updated_at
                FROM questionnaire_record qr
                LEFT JOIN doctor_profile dp ON dp.id = qr.doctor_id
                WHERE qr.patient_id = %s
                ORDER BY qr.created_at DESC, qr.record_id DESC
                LIMIT %s OFFSET %s
                ''',
                (user_id_int, safe_limit, safe_offset)
            )
            rows = cursor.fetchall() or []

            items: list[dict[str, Any]] = []
            for row in rows:
                (
                    record_id,
                    questionnaire_id,
                    questionnaire_name,
                    doctor_id,
                    doctor_name,
                    disease_type,
                    visit_type,
                    answers_json,
                    analysis_text,
                    created_at,
                    updated_at
                ) = row
                analysis_preview = str(analysis_text or '').strip().replace('\n', ' ')
                if len(analysis_preview) > 80:
                    analysis_preview = analysis_preview[:80] + '...'

                items.append(
                    {
                        'recordId': str(record_id),
                        'questionnaireId': str(questionnaire_id or ''),
                        'title': questionnaire_name or '量表记录',
                        'questionnaireName': questionnaire_name or '',
                        'doctorId': str(doctor_id) if doctor_id is not None else '',
                        'doctorName': doctor_name or '',
                        'diseaseType': disease_type or '',
                        'visitType': visit_type or '',
                        'createdAt': _format_datetime_shanghai(created_at),
                        'updatedAt': _format_datetime_shanghai(updated_at),
                        'summary': analysis_preview or '已填写完成',
                        'analysisText': analysis_text or '',
                        'answersJson': _json_loads_safe(answers_json, []),
                    }
                )

            return {
                'success': True,
                'data': {
                    'list': items,
                    'total': len(items)
                }
            }


def get_questionnaire_record_detail_mysql(
    record_id: Any,
    *,
    user_id: Any = None
) -> dict[str, Any]:
    """
    获取量表分析结果详情。
    """
    record_id_str = str(record_id or '').strip()
    if not record_id_str:
        raise ValueError('recordId 不能为空')

    user_id_int = _to_int_or_none(user_id)

    with get_mysql_connection() as connection:
        with get_mysql_cursor(connection) as cursor:
            _ensure_questionnaire_record_table_mysql(cursor)

            if user_id_int is None:
                cursor.execute(
                    '''
                    SELECT
                        qr.record_id,
                        qr.questionnaire_id,
                        qr.questionnaire_name,
                        qr.doctor_id,
                        COALESCE(dp.display_name, dp.doctor_name, '') AS doctor_name,
                        qr.patient_id,
                        qr.disease_type,
                        qr.visit_type,
                        qr.answers_json,
                        qr.analysis_text,
                        qr.created_at,
                        qr.updated_at
                    FROM questionnaire_record qr
                    LEFT JOIN doctor_profile dp ON dp.id = qr.doctor_id
                    WHERE qr.record_id = %s
                    LIMIT 1
                    ''',
                    (record_id_str,)
                )
            else:
                cursor.execute(
                    '''
                    SELECT
                        qr.record_id,
                        qr.questionnaire_id,
                        qr.questionnaire_name,
                        qr.doctor_id,
                        COALESCE(dp.display_name, dp.doctor_name, '') AS doctor_name,
                        qr.patient_id,
                        qr.disease_type,
                        qr.visit_type,
                        qr.answers_json,
                        qr.analysis_text,
                        qr.created_at,
                        qr.updated_at
                    FROM questionnaire_record qr
                    LEFT JOIN doctor_profile dp ON dp.id = qr.doctor_id
                    WHERE qr.record_id = %s
                      AND qr.patient_id = %s
                    LIMIT 1
                    ''',
                    (record_id_str, user_id_int)
                )

            row = cursor.fetchone()
            if not row:
                raise ValueError(f'未找到量表记录: {record_id_str}')

            (
                record_id_value,
                questionnaire_id,
                questionnaire_name,
                doctor_id,
                doctor_name,
                patient_id,
                disease_type,
                visit_type,
                answers_json,
                analysis_text,
                created_at,
                updated_at
            ) = row

            answers = _json_loads_safe(answers_json, [])

            return {
                'success': True,
                'data': {
                    'recordId': str(record_id_value),
                    'questionnaireId': str(questionnaire_id or ''),
                    'questionnaireName': questionnaire_name or '',
                    'doctorId': str(doctor_id) if doctor_id is not None else '',
                    'doctorName': doctor_name or '',
                    'patientId': str(patient_id) if patient_id is not None else '',
                    'diseaseType': disease_type or '',
                    'visitType': visit_type or '',
                    'answersJson': answers,
                    'analysisText': analysis_text or '',
                    'analysis': analysis_text or '',
                    'result': analysis_text or '',
                    'createdAt': _format_datetime_shanghai(created_at),
                    'updatedAt': _format_datetime_shanghai(updated_at),
                    'completedAt': _format_datetime_shanghai(created_at),
                    'status': 'completed'
                }
            }

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
    result = get_questionnaire_record_detail_mysql(questionnaire_id)
    return result.get('data') if isinstance(result, dict) else None

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
def upsert_user_mysql(
    *,
    user_id: Optional[str] = None,
    openid: str,
    session_key: Optional[str] = None,
    unionid: Optional[str] = None
) -> dict[str, Any]:
    """
    插入或更新用户
    返回用户信息（包含 id, user_code）
    """
    try:
        with get_mysql_connection() as connection:
            with get_mysql_cursor(connection) as cursor:
                # 先检查是否已存在
                cursor.execute('''
                    SELECT id, user_code FROM users WHERE openid = %s
                ''', (openid,))
                existing = cursor.fetchone()
                
                if existing:
                    # 更新现有用户
                    user_id_int, user_code = existing
                    cursor.execute('''
                        UPDATE users 
                        SET session_key = %s, unionid = %s, updated_at = NOW()
                        WHERE id = %s
                    ''', (session_key, unionid, user_id_int))
                else:
                    # 生成 user_code
                    import random
                    import string
                    user_code = 'HL' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                    
                    # 插入新用户
                    cursor.execute('''
                        INSERT INTO users (openid, user_code, session_key, unionid)
                        VALUES (%s, %s, %s, %s)
                    ''', (openid, user_code, session_key, unionid))
                    user_id_int = cursor.lastrowid
                
                connection.commit()
                
                # 获取完整用户信息
                cursor.execute('''
                    SELECT id, openid, user_code, session_key, unionid, created_at, updated_at
                    FROM users WHERE id = %s
                ''', (user_id_int,))
                row = cursor.fetchone()
                
                return {
                    'id': row[0],
                    'openid': row[1],
                    'userCode': row[2],
                    'sessionKey': row[3],
                    'unionid': row[4],
                    'createdAt': row[5],
                    'updatedAt': row[6]
                }
    except Exception as e:
        print(f'upsert_user_mysql 失败: {e}')
        raise

def get_user_by_openid_mysql(openid: str) -> Optional[dict[str, Any]]:
    """
    根据 openid 获取用户信息
    """
    try:
        with get_mysql_connection() as connection:
            with get_mysql_cursor(connection) as cursor:
                cursor.execute('''
                    SELECT id, openid, user_code, session_key, unionid, created_at, updated_at
                    FROM users WHERE openid = %s
                ''', (openid,))
                row = cursor.fetchone()
                
                if row:
                    return {
                        'id': row[0],
                        'openid': row[1],
                        'userCode': row[2],
                        'sessionKey': row[3],
                        'unionid': row[4],
                        'createdAt': row[5],
                        'updatedAt': row[6]
                    }
                return None
    except Exception as e:
        print(f'get_user_by_openid_mysql 失败: {e}')
        return None

def get_user_by_id_mysql(user_id: Any) -> Optional[dict[str, Any]]:
    """
    鏍规嵁 user_id 鑾峰彇鐢ㄦ埛淇℃伅
    """
    user_id_int = _to_int_or_none(user_id)
    if user_id_int is None:
        return None

    try:
        with get_mysql_connection() as connection:
            with get_mysql_cursor(connection) as cursor:
                cursor.execute('''
                    SELECT id, openid, user_code, session_key, unionid, created_at, updated_at
                    FROM users WHERE id = %s
                ''', (user_id_int,))
                row = cursor.fetchone()

                if row:
                    return {
                        'id': row[0],
                        'openid': row[1],
                        'userCode': row[2],
                        'sessionKey': row[3],
                        'unionid': row[4],
                        'createdAt': row[5],
                        'updatedAt': row[6]
                    }
                return None
    except Exception as e:
        print(f'get_user_by_id_mysql 澶辫触: {e}')
        return None


def get_user_by_user_code_mysql(user_code: str) -> Optional[dict[str, Any]]:
    """
    根据 user_code 获取用户信息
    """
    try:
        with get_mysql_connection() as connection:
            with get_mysql_cursor(connection) as cursor:
                cursor.execute('''
                    SELECT id, openid, user_code, session_key, unionid, created_at, updated_at
                    FROM users WHERE user_code = %s
                ''', (user_code,))
                row = cursor.fetchone()
                
                if row:
                    return {
                        'id': row[0],
                        'openid': row[1],
                        'userCode': row[2],
                        'sessionKey': row[3],
                        'unionid': row[4],
                        'createdAt': row[5],
                        'updatedAt': row[6]
                    }
                return None
    except Exception as e:
        print(f'get_user_by_user_code_mysql 失败: {e}')
        return None

def get_user_profile_mysql(user_id: int) -> Optional[dict[str, Any]]:
    """
    根据用户ID获取用户资料
    """
    try:
        with get_mysql_connection() as connection:
            with get_mysql_cursor(connection) as cursor:
                cursor.execute('''
                    SELECT id, user_id, nickname, avatar_url, gender, birthday, created_at, updated_at
                    FROM user_profiles WHERE user_id = %s
                ''', (user_id,))
                row = cursor.fetchone()
                
                if row:
                    return {
                        'id': row[0],
                        'userId': row[1],
                        'nickname': row[2],
                        'avatarUrl': row[3],
                        'gender': row[4],
                        'birthday': str(row[5]) if row[5] else None,
                        'createdAt': str(row[6]) if row[6] else None,
                        'updatedAt': str(row[7]) if row[7] else None
                    }
                return None
    except Exception as e:
        print(f'get_user_profile_mysql 失败: {e}')
        return None

def upsert_user_profile_mysql(
    *,
    user_id: int,
    nickname: Optional[str] = None,
    avatar_url: Optional[str] = None,
    gender: Optional[str] = None,
    birthday: Optional[str] = None
) -> dict[str, Any]:
    """
    插入或更新用户资料
    返回更新后的资料
    """
    try:
        with get_mysql_connection() as connection:
            with get_mysql_cursor(connection) as cursor:
                # 先检查是否已存在
                cursor.execute('''
                    SELECT id FROM user_profiles WHERE user_id = %s
                ''', (user_id,))
                existing = cursor.fetchone()
                
                if existing:
                    # 更新现有资料
                    cursor.execute('''
                        UPDATE user_profiles 
                        SET nickname = COALESCE(%s, nickname),
                            avatar_url = COALESCE(%s, avatar_url),
                            gender = COALESCE(%s, gender),
                            birthday = COALESCE(%s, birthday),
                            updated_at = NOW()
                        WHERE user_id = %s
                    ''', (nickname, avatar_url, gender, birthday, user_id))
                else:
                    # 插入新资料
                    cursor.execute('''
                        INSERT INTO user_profiles (user_id, nickname, avatar_url, gender, birthday)
                        VALUES (%s, %s, %s, %s, %s)
                    ''', (user_id, nickname, avatar_url, gender or 'unknown', birthday))
                
                connection.commit()
                
                # 返回更新后的资料
                return get_user_profile_mysql(user_id) or {}
    except Exception as e:
        print(f'upsert_user_profile_mysql 失败: {e}')
        raise

# 用户敏感信息相关操作

def mask_phone(phone: str) -> str:
    """
    手机号脱敏处理
    13812345678 -> 138****5678
    """
    if not phone or len(phone) != 11:
        return ''
    return phone[:3] + '****' + phone[-4:]


def mask_id_card(id_card: str) -> str:
    """
    身份证号脱敏处理
    410101199001011234 -> 410***********1234
    """
    if not id_card or len(id_card) != 18:
        return ''
    return id_card[:3] + '***********' + id_card[-4:]


def validate_phone(phone: str) -> bool:
    """
    校验中国大陆手机号
    格式：1开头的11位数字
    """
    if not phone:
        return True  # 允许为空
    import re
    return re.match(r'^1[3-9]\d{9}$', phone) is not None


def validate_id_card(id_card: str) -> bool:
    """
    校验18位身份证号
    最后一位可以是数字或X（统一转大写）
    """
    if not id_card:
        return True  # 允许为空
    id_card = id_card.upper()
    import re
    return re.match(r'^[1-9]\d{5}(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dX]$', id_card) is not None


def get_user_sensitive_info_mysql(user_id: int) -> Optional[dict[str, Any]]:
    """
    根据用户ID获取敏感信息（只返回脱敏数据）
    """
    try:
        with get_mysql_connection() as connection:
            with get_mysql_cursor(connection) as cursor:
                cursor.execute('''
                    SELECT phone_masked, id_card_masked
                    FROM user_sensitive_info WHERE user_id = %s
                ''', (user_id,))
                row = cursor.fetchone()

                if row:
                    return {
                        'phone': row[0],
                        'phoneMasked': row[0],
                        'idCardMasked': row[1]
                    }
                return None
    except Exception as e:
        print(f'get_user_sensitive_info_mysql 失败: {e}')
        return None


def normalize_user_profile(profile: dict, sensitive_info: Optional[dict] = None) -> dict:
    """
    统一用户资料序列化，补充 hasPhone/hasIdCard 明确状态字段
    所有返回用户资料的接口都必须经过此函数处理
    """
    if not profile:
        return {}

    phone_masked = (
        (sensitive_info or {}).get("phoneMasked")
        or (sensitive_info or {}).get("phone_masked")
        or profile.get("phoneMasked")
        or profile.get("phone_masked")
        or profile.get("phone")
        or ""
    )

    id_card_masked = (
        (sensitive_info or {}).get("idCardMasked")
        or (sensitive_info or {}).get("id_card_masked")
        or profile.get("idCardMasked")
        or profile.get("id_card_masked")
        or profile.get("idCard")
        or profile.get("id_card")
        or ""
    )

    return {
        **profile,
        "phoneMasked": phone_masked,
        "idCardMasked": id_card_masked,
        "hasPhone": bool(phone_masked),
        "hasIdCard": bool(id_card_masked),
    }


def upsert_user_sensitive_info_mysql(
    *,
    user_id: int,
    phone: Optional[str] = None,
    id_card: Optional[str] = None
) -> dict[str, Any]:
    """
    插入或更新用户敏感信息
    返回脱敏后的信息
    """
    # 校验手机号
    if phone and not validate_phone(phone):
        raise ValueError('手机号格式不正确')
    
    # 校验身份证号
    if id_card:
        id_card = id_card.upper()
        if not validate_id_card(id_card):
            raise ValueError('身份证号格式不正确')
    
    # 生成脱敏值
    phone_masked = mask_phone(phone) if phone else None
    id_card_masked = mask_id_card(id_card) if id_card else None
    
    try:
        with get_mysql_connection() as connection:
            with get_mysql_cursor(connection) as cursor:
                # 先检查是否已存在
                cursor.execute('''
                    SELECT id FROM user_sensitive_info WHERE user_id = %s
                ''', (user_id,))
                existing = cursor.fetchone()
                
                if existing:
                    # 更新现有记录
                    cursor.execute('''
                        UPDATE user_sensitive_info 
                        SET phone = COALESCE(%s, phone),
                            id_card = COALESCE(%s, id_card),
                            phone_masked = COALESCE(%s, phone_masked),
                            id_card_masked = COALESCE(%s, id_card_masked),
                            updated_at = NOW()
                        WHERE user_id = %s
                    ''', (phone, id_card, phone_masked, id_card_masked, user_id))
                else:
                    # 插入新记录
                    cursor.execute('''
                        INSERT INTO user_sensitive_info (user_id, phone, id_card, phone_masked, id_card_masked)
                        VALUES (%s, %s, %s, %s, %s)
                    ''', (user_id, phone, id_card, phone_masked, id_card_masked))
                
                connection.commit()
                
                # 返回脱敏后的信息
                return {
                    'phone': phone_masked,
                    'phoneMasked': phone_masked,
                    'idCardMasked': id_card_masked
                }
    except ValueError:
        raise
    except Exception as e:
        print(f'upsert_user_sensitive_info_mysql 失败: {e}')
        raise

# 订阅相关操作
def upsert_subscription_record_mysql(*args, **kwargs):
    pass
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
