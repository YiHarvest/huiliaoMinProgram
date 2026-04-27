import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator, Optional

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / 'data'
DB_PATH = DATA_DIR / 'mini_program.db'

DATA_DIR.mkdir(exist_ok=True)


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat(sep=' ')


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_db() -> None:
    with get_connection() as connection:
        connection.executescript(
            '''
            CREATE TABLE IF NOT EXISTS app_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS mini_program_users (
                user_id TEXT PRIMARY KEY,
                openid TEXT NOT NULL UNIQUE,
                session_key TEXT,
                unionid TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS subscription_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                openid TEXT NOT NULL,
                template_id TEXT NOT NULL,
                scene TEXT NOT NULL,
                subscribe_status TEXT NOT NULL,
                accepted_at TEXT,
                last_sent_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(openid, template_id, scene)
            );

            CREATE TABLE IF NOT EXISTS subscription_send_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                openid TEXT NOT NULL,
                template_id TEXT NOT NULL,
                scene TEXT NOT NULL,
                biz_id TEXT,
                page_path TEXT,
                payload TEXT NOT NULL,
                send_status TEXT NOT NULL,
                errcode TEXT,
                errmsg TEXT,
                sent_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS ai_reply_records (
                reply_id TEXT PRIMARY KEY,
                user_id TEXT,
                openid TEXT,
                assistant_id TEXT NOT NULL,
                question TEXT NOT NULL,
                content TEXT NOT NULL,
                chat_id TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS tongue_report_records (
                analysis_id TEXT PRIMARY KEY,
                user_id TEXT,
                openid TEXT,
                report_json TEXT NOT NULL,
                tips TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS appointment_reminders (
                appointment_id TEXT PRIMARY KEY,
                user_id TEXT,
                openid TEXT NOT NULL,
                doctor_name TEXT NOT NULL,
                clinic_time TEXT NOT NULL,
                clinic_location TEXT NOT NULL,
                remark TEXT,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS crm_questionnaire_template (
                template_id INTEGER PRIMARY KEY AUTOINCREMENT,
                questionnaire_name TEXT NOT NULL,
                category TEXT NOT NULL,
                apply_department TEXT NOT NULL,
                group_type INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS crm_questionnaire_user_record (
                record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                external_user_id TEXT NOT NULL,
                template_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                status_text TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (template_id) REFERENCES crm_questionnaire_template(template_id)
            );

            CREATE TABLE IF NOT EXISTS crm_questionnaire_template_subject (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id INTEGER NOT NULL,
                subject_id INTEGER NOT NULL,
                subject_type VARCHAR(32) NOT NULL,
                subject_title VARCHAR(255) NOT NULL,
                subject_content TEXT NOT NULL,
                sort_order INTEGER NOT NULL,
                is_required CHAR(1) NOT NULL DEFAULT 'Y',
                FOREIGN KEY (template_id) REFERENCES crm_questionnaire_template(template_id)
            );

            CREATE TABLE IF NOT EXISTS crm_questionnaire_user_subject_record (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_id INTEGER NOT NULL,
                subject_id INTEGER NOT NULL,
                answer_content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (record_id) REFERENCES crm_questionnaire_user_record(record_id)
            );

            CREATE TABLE IF NOT EXISTS crm_questionnaire_user_submit_result (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_id INTEGER NOT NULL,
                total_score INTEGER,
                result TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (record_id) REFERENCES crm_questionnaire_user_record(record_id)
            );

            CREATE TABLE IF NOT EXISTS crm_questionnaire_user_submit_result_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_id INTEGER NOT NULL,
                analysis TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (record_id) REFERENCES crm_questionnaire_user_record(record_id)
            );

            CREATE INDEX IF NOT EXISTS idx_questionnaire_user_record ON crm_questionnaire_user_record(external_user_id, template_id);
            CREATE INDEX IF NOT EXISTS idx_template_subject ON crm_questionnaire_template_subject(template_id);
            CREATE INDEX IF NOT EXISTS idx_user_subject_record ON crm_questionnaire_user_subject_record(record_id, subject_id);
            CREATE INDEX IF NOT EXISTS idx_submit_result ON crm_questionnaire_user_submit_result(record_id);
            CREATE INDEX IF NOT EXISTS idx_submit_result_analysis ON crm_questionnaire_user_submit_result_analysis(record_id);
            '''
        )


def upsert_user(
    *,
    user_id: str,
    openid: str,
    session_key: Optional[str],
    unionid: Optional[str]
) -> None:
    timestamp = now_iso()
    with get_connection() as connection:
        connection.execute(
            '''
            INSERT INTO mini_program_users (
                user_id, openid, session_key, unionid, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                openid = excluded.openid,
                session_key = excluded.session_key,
                unionid = excluded.unionid,
                updated_at = excluded.updated_at
            ''',
            (user_id, openid, session_key, unionid, timestamp, timestamp)
        )


def upsert_subscription_record(
    *,
    user_id: str,
    openid: str,
    template_id: str,
    scene: str,
    subscribe_status: str,
    accepted_at: Optional[str]
) -> None:
    timestamp = now_iso()
    with get_connection() as connection:
        existing = connection.execute(
            '''
            SELECT last_sent_at FROM subscription_records
            WHERE openid = ? AND template_id = ? AND scene = ?
            ''',
            (openid, template_id, scene)
        ).fetchone()

        last_sent_at = existing['last_sent_at'] if existing else None

        connection.execute(
            '''
            INSERT INTO subscription_records (
                user_id, openid, template_id, scene, subscribe_status,
                accepted_at, last_sent_at, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(openid, template_id, scene) DO UPDATE SET
                user_id = excluded.user_id,
                subscribe_status = excluded.subscribe_status,
                accepted_at = excluded.accepted_at,
                updated_at = excluded.updated_at
            ''',
            (
                user_id,
                openid,
                template_id,
                scene,
                subscribe_status,
                accepted_at,
                last_sent_at,
                timestamp,
                timestamp
            )
        )


def list_subscription_records(openid: str) -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            '''
            SELECT
                user_id,
                openid,
                template_id,
                scene,
                subscribe_status,
                accepted_at,
                last_sent_at,
                updated_at
            FROM subscription_records
            WHERE openid = ?
            ORDER BY updated_at DESC
            ''',
            (openid,)
        ).fetchall()

    return [dict(row) for row in rows]


def find_sendable_subscription(openid: str, template_id: str, scene: str) -> Optional[dict[str, Any]]:
    with get_connection() as connection:
        row = connection.execute(
            '''
            SELECT
                user_id,
                openid,
                template_id,
                scene,
                subscribe_status,
                accepted_at,
                last_sent_at
            FROM subscription_records
            WHERE openid = ?
              AND template_id = ?
              AND scene = ?
              AND subscribe_status = 'accept'
              AND accepted_at IS NOT NULL
              AND (last_sent_at IS NULL OR accepted_at > last_sent_at)
            LIMIT 1
            ''',
            (openid, template_id, scene)
        ).fetchone()

    return dict(row) if row else None


def mark_subscription_sent(openid: str, template_id: str, scene: str, sent_at: Optional[str] = None) -> None:
    timestamp = sent_at or now_iso()
    with get_connection() as connection:
        connection.execute(
            '''
            UPDATE subscription_records
            SET last_sent_at = ?, updated_at = ?
            WHERE openid = ? AND template_id = ? AND scene = ?
            ''',
            (timestamp, timestamp, openid, template_id, scene)
        )


def insert_send_log(
    *,
    openid: str,
    template_id: str,
    scene: str,
    biz_id: Optional[str],
    page_path: Optional[str],
    payload: dict[str, Any],
    send_status: str,
    errcode: Optional[str],
    errmsg: Optional[str]
) -> None:
    with get_connection() as connection:
        connection.execute(
            '''
            INSERT INTO subscription_send_logs (
                openid, template_id, scene, biz_id, page_path, payload,
                send_status, errcode, errmsg, sent_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                openid,
                template_id,
                scene,
                biz_id,
                page_path,
                json.dumps(payload, ensure_ascii=False),
                send_status,
                errcode,
                errmsg,
                now_iso()
            )
        )


def save_ai_reply(
    *,
    reply_id: str,
    user_id: Optional[str],
    openid: Optional[str],
    assistant_id: str,
    question: str,
    content: str,
    chat_id: Optional[str]
) -> None:
    with get_connection() as connection:
        connection.execute(
            '''
            INSERT OR REPLACE INTO ai_reply_records (
                reply_id, user_id, openid, assistant_id, question, content, chat_id, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (reply_id, user_id, openid, assistant_id, question, content, chat_id, now_iso())
        )


def get_ai_reply(reply_id: str) -> Optional[dict[str, Any]]:
    with get_connection() as connection:
        row = connection.execute(
            '''
            SELECT reply_id, user_id, openid, assistant_id, question, content, chat_id, created_at
            FROM ai_reply_records
            WHERE reply_id = ?
            LIMIT 1
            ''',
            (reply_id,)
        ).fetchone()

    return dict(row) if row else None


def save_tongue_report(
    *,
    analysis_id: str,
    user_id: Optional[str],
    openid: Optional[str],
    report: dict[str, Any],
    tips: Optional[str]
) -> None:
    with get_connection() as connection:
        connection.execute(
            '''
            INSERT OR REPLACE INTO tongue_report_records (
                analysis_id, user_id, openid, report_json, tips, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ''',
            (
                analysis_id,
                user_id,
                openid,
                json.dumps(report, ensure_ascii=False),
                tips,
                now_iso()
            )
        )


def get_tongue_report(analysis_id: str) -> Optional[dict[str, Any]]:
    with get_connection() as connection:
        row = connection.execute(
            '''
            SELECT analysis_id, user_id, openid, report_json, tips, created_at
            FROM tongue_report_records
            WHERE analysis_id = ?
            LIMIT 1
            ''',
            (analysis_id,)
        ).fetchone()

    if not row:
        return None

    result = dict(row)
    result['report'] = json.loads(result.pop('report_json'))
    return result


def save_appointment_reminder(
    *,
    appointment_id: str,
    user_id: Optional[str],
    openid: str,
    doctor_name: str,
    clinic_time: str,
    clinic_location: str,
    remark: Optional[str],
    status: str
) -> None:
    timestamp = now_iso()
    with get_connection() as connection:
        connection.execute(
            '''
            INSERT INTO appointment_reminders (
                appointment_id, user_id, openid, doctor_name, clinic_time,
                clinic_location, remark, status, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(appointment_id) DO UPDATE SET
                user_id = excluded.user_id,
                openid = excluded.openid,
                doctor_name = excluded.doctor_name,
                clinic_time = excluded.clinic_time,
                clinic_location = excluded.clinic_location,
                remark = excluded.remark,
                status = excluded.status,
                updated_at = excluded.updated_at
            ''',
            (
                appointment_id,
                user_id,
                openid,
                doctor_name,
                clinic_time,
                clinic_location,
                remark,
                status,
                timestamp,
                timestamp
            )
        )


def get_appointment_reminder(appointment_id: str) -> Optional[dict[str, Any]]:
    with get_connection() as connection:
        row = connection.execute(
            '''
            SELECT
                appointment_id,
                user_id,
                openid,
                doctor_name,
                clinic_time,
                clinic_location,
                remark,
                status,
                created_at,
                updated_at
            FROM appointment_reminders
            WHERE appointment_id = ?
            LIMIT 1
            ''',
            (appointment_id,)
        ).fetchone()

    return dict(row) if row else None


def get_meta(key: str) -> Optional[str]:
    with get_connection() as connection:
        row = connection.execute(
            'SELECT value FROM app_meta WHERE key = ? LIMIT 1',
            (key,)
        ).fetchone()

    return row['value'] if row else None


def set_meta(key: str, value: str) -> None:
    timestamp = now_iso()
    with get_connection() as connection:
        connection.execute(
            '''
            INSERT INTO app_meta (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
            ''',
            (key, value, timestamp)
        )


def init_questionnaire_templates() -> None:
    """初始化量表模板数据"""
    templates = [
        {
            'questionnaire_name': '焦虑自评量表(SAS)',
            'category': 'psychology',
            'apply_department': '心理科',
            'group_type': 0
        },
        {
            'questionnaire_name': '抑郁自评量表(SDS)',
            'category': 'psychology',
            'apply_department': '心理科',
            'group_type': 0
        },
        {
            'questionnaire_name': '简明精神状态检查表(MMSE)',
            'category': 'neuro',
            'apply_department': '神经内科',
            'group_type': 1
        },
        {
            'questionnaire_name': '日常生活活动能力量表(ADL)',
            'category': 'neuro',
            'apply_department': '神经内科',
            'group_type': 1
        },
        {
            'questionnaire_name': '匹兹堡睡眠质量指数(PSQI)',
            'category': 'psychology',
            'apply_department': '心理科',
            'group_type': 0
        }
    ]
    
    timestamp = now_iso()
    with get_connection() as connection:
        for template in templates:
            connection.execute(
                '''
                INSERT OR IGNORE INTO crm_questionnaire_template (
                    questionnaire_name, category, apply_department, group_type, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ''',
                (
                    template['questionnaire_name'],
                    template['category'],
                    template['apply_department'],
                    template['group_type'],
                    timestamp,
                    timestamp
                )
            )


def init_questionnaire_subjects() -> None:
    """初始化题目数据"""
    subjects = [
        # 焦虑自评量表(SAS)题目
        {
            'template_id': 1,
            'subject_id': 101,
            'subject_type': '1',  # 单选
            'subject_title': '我觉得比平时容易紧张和着急',
            'subject_content': json.dumps([
                {'label': '没有或很少时间', 'value': '1'},
                {'label': '小部分时间', 'value': '2'},
                {'label': '相当多时间', 'value': '3'},
                {'label': '绝大部分或全部时间', 'value': '4'}
            ]),
            'sort_order': 1
        },
        {
            'template_id': 1,
            'subject_id': 102,
            'subject_type': '1',
            'subject_title': '我无缘无故地感到害怕',
            'subject_content': json.dumps([
                {'label': '没有或很少时间', 'value': '1'},
                {'label': '小部分时间', 'value': '2'},
                {'label': '相当多时间', 'value': '3'},
                {'label': '绝大部分或全部时间', 'value': '4'}
            ]),
            'sort_order': 2
        },
        {
            'template_id': 1,
            'subject_id': 103,
            'subject_type': '1',
            'subject_title': '我容易心里烦乱或觉得惊恐',
            'subject_content': json.dumps([
                {'label': '没有或很少时间', 'value': '1'},
                {'label': '小部分时间', 'value': '2'},
                {'label': '相当多时间', 'value': '3'},
                {'label': '绝大部分或全部时间', 'value': '4'}
            ]),
            'sort_order': 3
        },
        # 抑郁自评量表(SDS)题目
        {
            'template_id': 2,
            'subject_id': 201,
            'subject_type': '1',
            'subject_title': '我觉得闷闷不乐，情绪低沉',
            'subject_content': json.dumps([
                {'label': '没有或很少时间', 'value': '1'},
                {'label': '小部分时间', 'value': '2'},
                {'label': '相当多时间', 'value': '3'},
                {'label': '绝大部分或全部时间', 'value': '4'}
            ]),
            'sort_order': 1
        },
        {
            'template_id': 2,
            'subject_id': 202,
            'subject_type': '1',
            'subject_title': '我觉得一天之中早晨最好',
            'subject_content': json.dumps([
                {'label': '没有或很少时间', 'value': '4'},
                {'label': '小部分时间', 'value': '3'},
                {'label': '相当多时间', 'value': '2'},
                {'label': '绝大部分或全部时间', 'value': '1'}
            ]),
            'sort_order': 2
        }
    ]
    
    timestamp = now_iso()
    with get_connection() as connection:
        for subject in subjects:
            connection.execute(
                '''
                INSERT OR IGNORE INTO crm_questionnaire_template_subject (
                    template_id, subject_id, subject_type, subject_title, 
                    subject_content, sort_order, is_required
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    subject['template_id'],
                    subject['subject_id'],
                    subject['subject_type'],
                    subject['subject_title'],
                    subject['subject_content'],
                    subject['sort_order'],
                    'Y'
                )
            )


def get_questionnaire_options(external_user_id: str) -> dict[str, Any]:
    """获取量表选项"""
    with get_connection() as connection:
        # 获取所有模板
        templates = connection.execute(
            '''
            SELECT template_id, questionnaire_name, category, apply_department, group_type
            FROM crm_questionnaire_template
            ORDER BY template_id
            '''
        ).fetchall()
        
        # 获取用户记录
        user_records = connection.execute(
            '''
            SELECT template_id, record_id, status, status_text
            FROM crm_questionnaire_user_record
            WHERE external_user_id = ?
            ''',
            (external_user_id,)
        ).fetchall()
    
    # 构建用户记录映射
    record_map = {record['template_id']: record for record in user_records}
    
    # 构建量表列表
    scales = []
    departments = set()
    
    for template in templates:
        record = record_map.get(template['template_id'])
        scales.append({
            'templateId': template['template_id'],
            'questionnaireName': template['questionnaire_name'],
            'category': template['category'],
            'applyDepartment': template['apply_department'],
            'groupType': template['group_type'],
            'recordId': record['record_id'] if record else None,
            'status': record['status'] if record else 'unfinished',
            'statusText': record['status_text'] if record else '未填写'
        })
        departments.add(template['apply_department'])
    
    # 构建分类列表 - key 使用 department 字段，与量表的 category 保持一致
    categories = [{'key': 'all', 'name': '全部'}]
    category_keys = set()
    for template in templates:
        category_keys.add((template['category'], template['apply_department']))
    
    for category_key, department_name in sorted(category_keys, key=lambda x: x[1]):
        categories.append({'key': category_key, 'name': department_name})
    
    return {
        'categories': categories,
        'scales': scales
    }


def start_questionnaire(external_user_id: str, template_id: int) -> int:
    """开始填写量表"""
    with get_connection() as connection:
        # 检查是否已有记录
        existing = connection.execute(
            '''
            SELECT record_id
            FROM crm_questionnaire_user_record
            WHERE external_user_id = ? AND template_id = ?
            LIMIT 1
            ''',
            (external_user_id, template_id)
        ).fetchone()
        
        if existing:
            return existing['record_id']
        
        # 插入新记录
        timestamp = now_iso()
        cursor = connection.execute(
            '''
            INSERT INTO crm_questionnaire_user_record (
                external_user_id, template_id, status, status_text, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ''',
            (
                external_user_id,
                template_id,
                'unfinished',
                '未填写',
                timestamp,
                timestamp
            )
        )
        return cursor.lastrowid


def get_questionnaire_detail(record_id: int) -> dict[str, Any]:
    """获取问卷详情"""
    with get_connection() as connection:
        # 获取记录信息
        record = connection.execute(
            '''
            SELECT r.*, t.questionnaire_name
            FROM crm_questionnaire_user_record r
            JOIN crm_questionnaire_template t ON r.template_id = t.template_id
            WHERE r.record_id = ?
            LIMIT 1
            ''',
            (record_id,)
        ).fetchone()
        
        if not record:
            raise ValueError(f'未找到记录: {record_id}')
        
        # 获取题目列表
        subjects = connection.execute(
            '''
            SELECT *
            FROM crm_questionnaire_template_subject
            WHERE template_id = ?
            ORDER BY sort_order
            ''',
            (record['template_id'],)
        ).fetchall()
    
    # 构建返回数据
    questions = []
    for subject in subjects:
        questions.append({
            'subjectId': subject['subject_id'],
            'title': subject['subject_title'],
            'type': subject['subject_type'],
            'options': json.loads(subject['subject_content']),
            'isRequired': subject['is_required'] == 'Y',
            'sortOrder': subject['sort_order']
        })
    
    return {
        'recordId': record['record_id'],
        'templateId': record['template_id'],
        'questionnaireName': record['questionnaire_name'],
        'status': record['status'],
        'questions': questions
    }


def submit_questionnaire(record_id: int, answers: list[dict[str, Any]]) -> dict[str, Any]:
    """提交问卷"""
    timestamp = now_iso()
    
    with get_connection() as connection:
        # 保存答案
        for answer in answers:
            connection.execute(
                '''
                INSERT OR REPLACE INTO crm_questionnaire_user_subject_record (
                    record_id, subject_id, answer_content, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?)
                ''',
                (
                    record_id,
                    answer['subjectId'],
                    json.dumps(answer['value']),
                    timestamp,
                    timestamp
                )
            )
        
        # 计算总分（简单示例，实际需要根据具体量表规则计算）
        total_score = 0
        for answer in answers:
            if isinstance(answer['value'], str) and answer['value'].isdigit():
                total_score += int(answer['value'])
        
        # 保存提交结果
        connection.execute(
            '''
            INSERT OR REPLACE INTO crm_questionnaire_user_submit_result (
                record_id, total_score, result, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?)
            ''',
            (
                record_id,
                total_score,
                f'总分: {total_score}',
                timestamp,
                timestamp
            )
        )
        
        # 保存分析报告
        analysis = f'您的问卷得分为 {total_score} 分，感谢您的参与！'
        connection.execute(
            '''
            INSERT OR REPLACE INTO crm_questionnaire_user_submit_result_analysis (
                record_id, analysis, created_at, updated_at
            )
            VALUES (?, ?, ?, ?)
            ''',
            (
                record_id,
                analysis,
                timestamp,
                timestamp
            )
        )
        
        # 更新记录状态
        connection.execute(
            '''
            UPDATE crm_questionnaire_user_record
            SET status = ?, status_text = ?, updated_at = ?
            WHERE record_id = ?
            ''',
            (
                'completed',
                '已完成',
                timestamp,
                record_id
            )
        )
    
    return {
        'success': True,
        'recordId': record_id,
        'totalScore': total_score
    }


def get_questionnaire_report(record_id: int) -> dict[str, Any]:
    """获取问卷报告"""
    with get_connection() as connection:
        # 获取结果
        result = connection.execute(
            '''
            SELECT *
            FROM crm_questionnaire_user_submit_result
            WHERE record_id = ?
            LIMIT 1
            ''',
            (record_id,)
        ).fetchone()
        
        # 获取分析
        analysis = connection.execute(
            '''
            SELECT analysis
            FROM crm_questionnaire_user_submit_result_analysis
            WHERE record_id = ?
            LIMIT 1
            ''',
            (record_id,)
        ).fetchone()
        
        # 获取记录信息
        record = connection.execute(
            '''
            SELECT *
            FROM crm_questionnaire_user_record
            WHERE record_id = ?
            LIMIT 1
            ''',
            (record_id,)
        ).fetchone()
    
    if not result or not record:
        raise ValueError(f'未找到报告: {record_id}')
    
    return {
        'recordId': record_id,
        'status': record['status'],
        'statusText': record['status_text'],
        'totalScore': result['total_score'],
        'result': result['result'],
        'analysis': analysis['analysis'] if analysis else '无分析报告'
    }


init_db()
init_questionnaire_templates()
init_questionnaire_subjects()
