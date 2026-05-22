import json
import uuid
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from urllib import error, parse, request
from zoneinfo import ZoneInfo

from config import config
from db import (
    delete_chat_session,
    get_chat_session,
    get_ai_reply,
    get_appointment_reminder,
    get_doctors_list,
    get_questionnaire_detail,
    get_questionnaire_options,
    get_comprehensive_report_source_preview,
    generate_comprehensive_report,
    list_comprehensive_reports,
    get_comprehensive_report_detail,
    get_questionnaire_record_detail,
    get_doctor_questionnaires_by_doctor,
    get_questionnaire_report,
    get_tongue_reminder_status,
    list_questionnaire_records,
    list_chat_messages,
    list_chat_sessions,
    list_subscription_records,
    list_due_tongue_reminders,
    save_ai_reply,
    save_chat_message,
    save_appointment_reminder,
    start_questionnaire,
    submit_questionnaire,
    upsert_chat_session,
    upsert_tongue_reminder,
    disable_tongue_reminder,
    mark_tongue_reminder_sent,
)
from wechat_subscription import (
    exchange_code_for_session,
    get_frontend_subscribe_config,
    record_subscription_result,
    send_subscribe_message,
    send_tongue_reminder,
)

# 检查报告模块导入
from modules.report.handlers import ReportHandlers
from modules.tongue.handlers import TongueHandlers

SUPPORTED_ASSISTANTS = {'xiaohui', 'chen'}


def extract_reply_content(response_data: dict[str, Any]) -> tuple[str, str]:
    """
    兼容提取上游返回的回复内容。
    依次尝试多个可能的字段路径，返回 (content, source_field)。
    """
    candidates = [
        ('content', lambda d: d.get('content')),
        ('answer', lambda d: d.get('answer')),
        ('text', lambda d: d.get('text')),
        ('response', lambda d: d.get('response')),
        ('data.content', lambda d: d.get('data', {}).get('content') if isinstance(d.get('data'), dict) else None),
        ('data.answer', lambda d: d.get('data', {}).get('answer') if isinstance(d.get('data'), dict) else None),
        ('responseData.content', lambda d: d.get('responseData', {}).get('content') if isinstance(d.get('responseData'), dict) else None),
        ('responseData.answer', lambda d: d.get('responseData', {}).get('answer') if isinstance(d.get('responseData'), dict) else None),
        ('choices[0].message.content', lambda d: (
            d.get('choices', [{}])[0].get('message', {}).get('content')
            if isinstance(d.get('choices'), list) and len(d.get('choices', [])) > 0
            else None
        )),
    ]

    for field_name, extractor in candidates:
        try:
            content = extractor(response_data)
            if content and str(content).strip():
                return str(content).strip(), field_name
        except (KeyError, IndexError, TypeError, AttributeError):
            continue

    return '', ''


def call_fastgpt(question: str, chat_id: Optional[str] = None) -> dict[str, Any]:
    print('=' * 80)
    print('[FASTGPT-INPUT] call_fastgpt 被调用')
    print(f'[FASTGPT-INPUT] question = {repr(question)}')
    print(f'[FASTGPT-INPUT] question type = {type(question).__name__}')
    print(f'[FASTGPT-INPUT] question 长度 = {len(question) if question else 0}')
    print(f'[FASTGPT-INPUT] chatId = {repr(chat_id)}')
    print('=' * 80)

    base_url = config['fastgpt']['base_url'].rstrip('/')
    url = f"{base_url}/v1/chat/completions"

    payload = {
        'chatId': chat_id or 'test',
        'stream': False,
        'variables': {
            'question': question,
            'input': question,
            'query': question,
            'userInput': question,
            'userChatInput': question,
        },
        'messages': [
            {
                'role': 'user',
                'content': question
            }
        ]
    }

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f"Bearer {config['fastgpt']['api_key']}"
    }

    data = json.dumps(payload, ensure_ascii=False).encode('utf-8')

    print('DEBUG upstream url:', url)
    print('DEBUG upstream payload:', json.dumps(payload, ensure_ascii=False))
    print('DEBUG upstream auth prefix:', headers['Authorization'][:20] + '...')

    req = request.Request(
        url=url,
        data=data,
        headers=headers,
        method='POST'
    )

    try:
        with request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode('utf-8', errors='replace')
            print('DEBUG upstream status:', resp.status)
            print('DEBUG upstream body:', raw[:1000])
            response_data = json.loads(raw)
    except error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        print('DEBUG upstream HTTPError:', e.code, body[:2000])
        raise Exception(f'upstream http error {e.code}: {body[:500]}')
    except Exception as e:
        print('DEBUG upstream Exception:', repr(e))
        raise

    print('=' * 80)
    print('[CHAT-DEBUG] 上游返回完整信息:')
    print(f'[CHAT-DEBUG] response_data type: {type(response_data).__name__}')
    print(f'[CHAT-DEBUG] response_data (前3000字符): {json.dumps(response_data, ensure_ascii=False)[:3000]}')

    reply_content, source_field = extract_reply_content(response_data)

    print(f'[CHAT-DEBUG] 兼容提取结果: content长度={len(reply_content)}, 来源字段={source_field}')
    print(f'[CHAT-DEBUG] reply_content (前200字符): {reply_content[:200]}')
    print('=' * 80)

    if not reply_content:
        all_keys = list(response_data.keys()) if isinstance(response_data, dict) else 'N/A (非dict类型)'
        print(f'[CHAT-ERROR] 无法从上游返回中提取回复内容!')
        print(f'[CHAT-ERROR] response_data 的顶层 keys: {all_keys}')
        print(f'[CHAT-ERROR] 完整 response_data (前3000字符): {json.dumps(response_data, ensure_ascii=False)[:3000]}')
        raise RuntimeError(f'上游接口返回成功，但没有有效回复内容 (尝试的字段路径均未找到内容, 顶层keys={all_keys})')

    return {
        'content': reply_content,
        'chatId': response_data.get('id') or chat_id,
    }


def parse_json_body(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    content_length = int(handler.headers.get('Content-Length', '0') or 0)
    raw_body = handler.rfile.read(content_length)

    if not raw_body:
        return {}

    try:
        return json.loads(raw_body.decode('utf-8'))
    except json.JSONDecodeError as exc:
        raise ValueError('请求体必须是 JSON') from exc


def safe_summary(value: str, limit: int = 20) -> str:
    content = str(value or '').strip().replace('\n', ' ')
    if len(content) <= limit:
        return content
    return f"{content[:max(limit - 3, 1)]}..."


def current_user_identity(payload: dict[str, Any]) -> dict[str, Optional[str]]:
    user_id = str(payload.get('userId') or payload.get('user_id') or '').strip() or None
    openid = str(payload.get('openid') or '').strip() or None
    return {
        'userId': user_id,
        'openid': openid,
    }


def resolve_subscription_openid(user_id: Optional[str], openid: Optional[str]) -> str:
    openid_value = str(openid or '').strip()
    if openid_value:
        return openid_value

    user_id_value = str(user_id or '').strip()
    if not user_id_value:
        raise ValueError('userId 不能为空')

    from reminder_storage import get_user_openid_by_user_id_mysql

    resolved_openid = get_user_openid_by_user_id_mysql(user_id_value)
    if not resolved_openid:
        raise ValueError('未找到用户openid，请重新登录')

    return resolved_openid


def resolve_subscription_identity(
    user_id: Optional[str],
    openid: Optional[str],
) -> tuple[Optional[str], Optional[str]]:
    user_id_value = str(user_id or '').strip() or None
    openid_value = str(openid or '').strip() or None

    if openid_value and not user_id_value:
        from reminder_storage import get_user_id_by_openid_mysql

        resolved_user_id = get_user_id_by_openid_mysql(openid_value)
        return (str(resolved_user_id) if resolved_user_id is not None else None, openid_value)

    if user_id_value and not openid_value:
        openid_value = resolve_subscription_openid(user_id_value, None)

    return (user_id_value, openid_value)


def normalize_tongue_subscription_status(status: dict[str, Any]) -> dict[str, Any]:
    interval_days = int(status.get('intervalDays') or status.get('reminderIntervalDays') or 1)
    remind_time = str(
        status.get('remindTime')
        or status.get('reminderTime')
        or '08:00'
    ).strip() or '08:00'
    next_remind_at = status.get('nextRemindAt') or status.get('nextSendAt') or None
    last_sent_at = status.get('lastSentAt') or None
    last_sent_date = status.get('lastSentDate') or None
    enabled = bool(status.get('enabled'))
    configured = bool(status.get('configured'))

    return {
        'scene': 'tongue_reminder',
        'userId': status.get('userId'),
        'configured': configured,
        'enabled': enabled,
        'intervalDays': interval_days,
        'remindTime': remind_time,
        'reminderIntervalDays': interval_days,
        'reminderTime': remind_time,
        'lastSentAt': last_sent_at,
        'lastSentDate': last_sent_date,
        'nextRemindAt': next_remind_at,
        'nextSendAt': next_remind_at,
        'templateId': status.get('templateId'),
    }


def build_session_title(question: str) -> str:
    title = safe_summary(question, 16)
    return title or '新对话'


def build_message_preview(content: str) -> str:
    preview = safe_summary(content, 40)
    return preview or ''



def now_iso() -> str:
    # now_iso helper
    """返回 MySQL DATETIME 兼容的当前时间字符串。"""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


SHANGHAI_TZ = ZoneInfo('Asia/Shanghai')
_TONGUE_REMINDER_SCHEDULER_STARTED = False
_TONGUE_REMINDER_SCAN_INTERVAL_SECONDS = 30


def china_now() -> datetime:
    return datetime.now(SHANGHAI_TZ)


def run_tongue_reminder_dispatch() -> None:
    scan_time = china_now()
    try:
        due_records = list_due_tongue_reminders(target_time=scan_time)
    except Exception as exc:
        print(f'[tongue-reminder] 查询待发送提醒失败: {exc}')
        return

    if not due_records:
        print(f'[tongue-reminder] 当前无待发送提醒，now_shanghai={scan_time.strftime("%Y-%m-%d %H:%M:%S")}')
        return

    for record in due_records:
        user_id = record.get('userId')
        openid = str(record.get('openid') or '').strip()
        remind_time = record.get('reminderTime') or record.get('remindTime')
        interval_days = record.get('reminderIntervalDays') or record.get('intervalDays')
        next_remind_at = record.get('nextSendAt') or record.get('nextRemindAt')
        print(
            '[tongue-reminder] scan record '
            f'now_shanghai={scan_time.strftime("%Y-%m-%d %H:%M:%S")} '
            f'remindTime={remind_time} intervalDays={interval_days} '
            f'nextRemindAt={next_remind_at} due=True'
        )
        if not openid:
            print(f'[tongue-reminder] user_id={user_id} 缺少 openid，跳过')
            continue

        try:
            result = send_tongue_reminder(openid)
            if result.get('success'):
                mark_tongue_reminder_sent(user_id=user_id, sent_time=scan_time)
                print(f'[tongue-reminder] user_id={user_id} 发送成功')
            else:
                print(f'[tongue-reminder] user_id={user_id} 发送失败: {result}')
        except Exception as exc:
            print(f'[tongue-reminder] user_id={user_id} 发送异常: {exc}')


def tongue_reminder_scheduler_loop() -> None:
    while True:
        run_tongue_reminder_dispatch()
        print(f'[tongue-reminder] { _TONGUE_REMINDER_SCAN_INTERVAL_SECONDS } 秒后再次扫描')
        time.sleep(_TONGUE_REMINDER_SCAN_INTERVAL_SECONDS)


def start_tongue_reminder_scheduler() -> None:
    global _TONGUE_REMINDER_SCHEDULER_STARTED
    if _TONGUE_REMINDER_SCHEDULER_STARTED:
        return

    _TONGUE_REMINDER_SCHEDULER_STARTED = True
    thread = threading.Thread(target=tongue_reminder_scheduler_loop, daemon=True)
    thread.start()


class ChatProxyHandler(BaseHTTPRequestHandler):
    server_version = 'ChatProxy/2.0'

    def _write_json(self, data: Any, status: int = 200) -> None:
        try:
            encoded = json.dumps(data, ensure_ascii=False, default=str).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(encoded)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.send_header('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
            self.end_headers()
            self.wfile.write(encoded)
        except BrokenPipeError:
            print('客户端已断开连接，业务可能已处理完成')

    def do_OPTIONS(self) -> None:
        self._write_json({})

    def do_GET(self) -> None:
        import os
        import mimetypes

        parsed_url = parse.urlparse(self.path)
        path = parsed_url.path
        query = parse.parse_qs(parsed_url.query)

        if self.handle_chat_history_get(path, query):
            return

        if path.startswith('/uploads/avatars/'):
            base_dir = os.path.dirname(os.path.abspath(__file__))
            avatars_dir = os.path.join(base_dir, 'Image', 'avatars')
            filename = path.replace('/uploads/avatars/', '')
            safe_filename = os.path.basename(filename)

            file_path = os.path.join(avatars_dir, safe_filename)

            if not os.path.exists(file_path) or not os.path.isfile(file_path):
                self.send_response(404)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'File not found')
                return

            mime_type, _ = mimetypes.guess_type(file_path)
            content_type = mime_type or 'application/octet-stream'

            with open(file_path, 'rb') as f:
                file_content = f.read()

            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(file_content)))
            self.send_header('Cache-Control', 'public, max-age=86400')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(file_content)
            return

        # 检查报告图片静态文件访问
        if path.startswith('/uploads/reports/'):
            base_dir = os.path.dirname(os.path.abspath(__file__))
            reports_dir = os.path.join(base_dir, 'uploads', 'reports')
            file_path_relative = path.replace('/uploads/reports/', '')
            
            # 安全检查：防止目录遍历
            file_path = os.path.normpath(os.path.join(reports_dir, file_path_relative))
            if not file_path.startswith(reports_dir):
                self.send_response(403)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'Forbidden')
                return

            if not os.path.exists(file_path) or not os.path.isfile(file_path):
                self.send_response(404)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'File not found')
                return

            mime_type, _ = mimetypes.guess_type(file_path)
            content_type = mime_type or 'application/octet-stream'

            with open(file_path, 'rb') as f:
                file_content = f.read()

            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(file_content)))
            self.send_header('Cache-Control', 'public, max-age=86400')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(file_content)
            return

        if path == '/health':
            self._write_json(
                {
                    'status': 'ok',
                    'fastgptBaseUrl': config['fastgpt']['base_url'],
                    'supportedAssistants': list(SUPPORTED_ASSISTANTS),
                }
            )
            return

        if path == '/api/subscription/config':
            self._write_json(get_frontend_subscribe_config())
            return

        if path == '/api/doctors/list':
            try:
                result = get_doctors_list()
                self._write_json(result)
            except Exception as exc:
                self._write_json({'error': str(exc)}, status=500)
            return

        if path == '/api/user/profile':
            # GET 请求从查询参数获取 userId
            user_id = str((query.get('userId') or [''])[0]).strip()
            if user_id:
                self.handle_user_profile({'userId': user_id})
            else:
                self._write_json({'error': 'userId 不能为空'}, status=400)
            return

        if path == '/api/subscription/status':
            user_id = str((query.get('userId') or query.get('user_id') or [''])[0]).strip()
            openid = str((query.get('openid') or [''])[0]).strip()
            scene = str((query.get('scene') or [''])[0]).strip()

            try:
                if scene == 'tongue_reminder' or user_id or openid:
                    from reminder_storage import (
                        get_tongue_reminder_status_mysql,
                        get_tongue_reminder_status_mysql_by_openid,
                    )

                    if openid and not user_id:
                        status = get_tongue_reminder_status_mysql_by_openid(openid)
                    elif user_id:
                        status = get_tongue_reminder_status_mysql(user_id)
                        if not status.get('openid'):
                            status['openid'] = resolve_subscription_openid(user_id, openid or None)
                    else:
                        self._write_json({'success': False, 'error': 'userId 或 openid 不能为空'}, status=400)
                        return

                    self._write_json({'success': True, 'data': normalize_tongue_subscription_status(status)})
                    return

                if openid:
                    self._write_json({'records': list_subscription_records(openid)})
                    return

                self._write_json({'success': False, 'error': 'userId 或 openid 不能为空'}, status=400)
            except ValueError as exc:
                self._write_json({'success': False, 'error': str(exc)}, status=400)
            except Exception as exc:
                self._write_json({'success': False, 'error': str(exc)}, status=500)
            return

        if path == '/api/user/reminder/tongue/status':
            user_id = str((query.get('userId') or [''])[0]).strip()
            if not user_id:
                self._write_json({'error': 'userId 涓嶈兘涓虹┖'}, status=400)
                return

            try:
                self._write_json(get_tongue_reminder_status(user_id))
            except Exception as exc:
                self._write_json({'error': str(exc)}, status=500)
            return

        if path == '/api/chat/result':
            reply_id = str((query.get('replyId') or [''])[0]).strip()
            if not reply_id:
                self._write_json({'error': 'replyId 不能为空'}, status=400)
                return

            record = get_ai_reply(reply_id)
            if not record:
                self._write_json({'error': '未找到 AI 回复记录'}, status=404)
                return

            self._write_json(record)
            return

        if path == '/api/appointments/detail':
            appointment_id = str((query.get('appointmentId') or [''])[0]).strip()
            if not appointment_id:
                self._write_json({'error': 'appointmentId 不能为空'}, status=400)
                return

            record = get_appointment_reminder(appointment_id)
            if not record:
                self._write_json({'error': '未找到预约提醒'}, status=404)
                return

            self._write_json(record)
            return

        if path == '/api/questionnaires/options':
            external_user_id = str((query.get('externalUserId') or [''])[0]).strip()
            if not external_user_id:
                self._write_json({'error': 'externalUserId 不能为空'}, status=400)
                return

            try:
                result = get_questionnaire_options(external_user_id)
                self._write_json(result)
            except Exception as exc:
                self._write_json({'error': str(exc)}, status=500)
            return

        if path == '/api/questionnaires/by-doctor':
            doctor_id_raw = str((query.get('doctorId') or query.get('doctor_id') or [''])[0]).strip()
            patient_id_raw = str((query.get('patientId') or query.get('patient_id') or [''])[0]).strip()

            if not doctor_id_raw:
                self._write_json({'error': 'doctorId 涓嶈兘涓虹┖'}, status=400)
                return
            if not patient_id_raw:
                self._write_json({'error': 'patientId 涓嶈兘涓虹┖'}, status=400)
                return

            try:
                result = get_doctor_questionnaires_by_doctor(
                    doctor_id=int(doctor_id_raw),
                    patient_id=int(patient_id_raw)
                )
                self._write_json(result)
            except ValueError as exc:
                self._write_json({'error': str(exc)}, status=400)
            except Exception as exc:
                self._write_json({'error': str(exc)}, status=500)
            return

        if path == '/api/questionnaires/detail':
            record_id_raw = str((query.get('recordId') or [''])[0]).strip()
            print('接收到 /api/questionnaires/detail 请求，recordId_raw:', record_id_raw)
            print('recordId_raw 类型:', type(record_id_raw))
            
            if not record_id_raw:
                self._write_json({'error': 'recordId 不能为空'}, status=400)
                return

            # 尝试将recordId转换为整数
            try:
                record_id = int(record_id_raw)
                print('转换后的 recordId:', record_id)
                result = get_questionnaire_detail(record_id)
                print('get_questionnaire_detail 返回结果:', result)
                self._write_json(result)
            except ValueError as exc:
                print('ValueError:', str(exc))
                self._write_json({'error': str(exc)}, status=404)
            except Exception as exc:
                print('Exception:', str(exc))
                import traceback
                traceback.print_exc()
                self._write_json({'error': str(exc)}, status=500)
            return

        if path == '/api/questionnaires/records':
            user_id_raw = str((query.get('userId') or query.get('patientId') or [''])[0]).strip()
            limit_raw = str((query.get('limit') or ['50'])[0]).strip()
            offset_raw = str((query.get('offset') or ['0'])[0]).strip()

            if not user_id_raw:
                self._write_json({'error': 'userId 不能为空'}, status=400)
                return

            try:
                result = list_questionnaire_records(
                    user_id=user_id_raw,
                    limit=int(limit_raw or '50'),
                    offset=int(offset_raw or '0')
                )
                self._write_json(result)
            except ValueError as exc:
                self._write_json({'error': str(exc)}, status=400)
            except Exception as exc:
                self._write_json({'error': str(exc)}, status=500)
            return

        if path == '/api/questionnaires/records/detail':
            record_id_raw = str((query.get('recordId') or [''])[0]).strip()
            user_id_raw = str((query.get('userId') or query.get('patientId') or [''])[0]).strip()

            if not record_id_raw:
                self._write_json({'error': 'recordId 不能为空'}, status=400)
                return

            try:
                result = get_questionnaire_record_detail(record_id_raw, user_id=user_id_raw or None)
                self._write_json(result)
            except ValueError as exc:
                self._write_json({'error': str(exc)}, status=404)
            except Exception as exc:
                self._write_json({'error': str(exc)}, status=500)
            return

        if path == '/api/questionnaires/report':
            record_id_raw = str((query.get('recordId') or [''])[0]).strip()
            print('接收到 /api/questionnaires/report 请求，recordId_raw:', record_id_raw)
            print('recordId_raw 类型:', type(record_id_raw))
            
            if not record_id_raw:
                self._write_json({'error': 'recordId 不能为空'}, status=400)
                return

            # 尝试将recordId转换为整数
            try:
                result = get_questionnaire_record_detail(record_id_raw)
                self._write_json(result)
            except ValueError as exc:
                self._write_json({'error': str(exc)}, status=404)
            except Exception as exc:
                self._write_json({'error': str(exc)}, status=500)
            return

        if path == '/api/comprehensive-reports/source-preview':
            patient_id_raw = str((query.get('patientId') or query.get('userId') or [''])[0]).strip()
            if not patient_id_raw:
                self._write_json({'error': 'patientId 不能为空'}, status=400)
                return

            try:
                result = get_comprehensive_report_source_preview(patient_id_raw)
                self._write_json(result)
            except ValueError as exc:
                self._write_json({'error': str(exc)}, status=400)
            except Exception as exc:
                self._write_json({'error': str(exc)}, status=500)
            return

        if path == '/api/comprehensive-reports':
            patient_id_raw = str((query.get('patientId') or query.get('userId') or [''])[0]).strip()
            if not patient_id_raw:
                self._write_json({'error': 'patientId 不能为空'}, status=400)
                return

            try:
                result = list_comprehensive_reports(patient_id=patient_id_raw)
                self._write_json(result)
            except Exception as exc:
                self._write_json({'error': str(exc)}, status=500)
            return

        if path == '/api/comprehensive-reports/detail':
            report_id_raw = str((query.get('reportId') or [''])[0]).strip()
            patient_id_raw = str((query.get('patientId') or query.get('userId') or [''])[0]).strip()
            if not report_id_raw:
                self._write_json({'error': 'reportId 不能为空'}, status=400)
                return

            try:
                result = get_comprehensive_report_detail(
                    report_id=report_id_raw,
                    patient_id=patient_id_raw or None,
                )
                self._write_json(result)
            except Exception as exc:
                self._write_json({'error': str(exc)}, status=500)
            return

        # 检查报告接口路由 - GET
        if path == '/api/tongue/list':
            TongueHandlers.handle_list_tongue_reports(self, query)
            return

        if path == '/api/tongue/detail':
            TongueHandlers.handle_get_tongue_report_detail(self, query)
            return

        if path == '/api/report/list':
            ReportHandlers.handle_list_reports(self, query)
            return
        
        if path == '/api/report/detail':
            ReportHandlers.handle_get_report_detail(self, query)
            return

        self._write_json({'error': 'Not Found'}, status=404)

    def do_POST(self) -> None:
        path = parse.urlparse(self.path).path

        if path == '/api/user/avatar/upload':
            self.handle_avatar_upload()
            return

        # 检查报告接口路由 - POST
        if path == '/api/report/create':
            ReportHandlers.handle_create_report(self, self.rfile.read(int(self.headers.get('Content-Length', 0))))
            return
        
        if path == '/api/report/file/upload':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else b''
            ReportHandlers.handle_upload_file(self, post_data, self.headers.get('Content-Type', ''))
            return
        
        if path == '/api/report/complete':
            ReportHandlers.handle_complete_report(self, self.rfile.read(int(self.headers.get('Content-Length', 0))))
            return
        
        if path == '/api/report/delete':
            ReportHandlers.handle_delete_report(self, self.rfile.read(int(self.headers.get('Content-Length', 0))))
            return

        try:
            payload = parse_json_body(self)
        except ValueError as exc:
            self._write_json({'error': str(exc)}, status=400)
            return

        if self.handle_chat_history_post(path, payload):
            return

        if path == '/api/comprehensive-reports/generate':
            patient_id_raw = str(
                payload.get('patientId')
                or payload.get('patient_id')
                or payload.get('userId')
                or ''
            ).strip()
            if not patient_id_raw:
                self._write_json({'success': False, 'message': 'patientId 不能为空'}, status=400)
                return

            try:
                result = generate_comprehensive_report(patient_id=patient_id_raw)
                self._write_json(result)
            except Exception as exc:
                self._write_json({'success': False, 'message': str(exc)}, status=500)
            return

        if path == '/api/wxapp/login':
            self.handle_login(payload)
            return

        if path == '/api/user/profile':
            self.handle_user_profile(payload)
            return

        if path == '/api/subscription/record':
            self.handle_subscription_record(payload)
            return

        if path == '/api/subscription/config':
            self.handle_subscription_config(payload)
            return

        if path == '/api/subscription/enable':
            self.handle_subscription_enable(payload)
            return

        if path == '/api/subscription/disable':
            self.handle_subscription_disable(payload)
            return

        if path == '/api/chat':
            self.handle_chat(payload)
            return

        if path == '/api/appointments/reminder':
            self.handle_appointment_reminder(payload)
            return

        if path == '/api/subscription/mock-send':
            self.handle_mock_send(payload)
            return

        if path == '/api/subscription/test-send':
            self.handle_test_send(payload)
            return

        if path == '/api/user/reminder/tongue/enable':
            self.handle_tongue_reminder_enable(payload)
            return

        if path == '/api/user/reminder/tongue/save-config':
            self.handle_tongue_reminder_save_config(payload)
            return

        if path == '/api/user/reminder/tongue/disable':
            self.handle_tongue_reminder_disable(payload)
            return

        if path == '/api/questionnaires/start':
            # 打印日志
            print('接收到 /api/questionnaires/start 请求')
            print('原始请求体:', payload)
            
            external_user_id = str(
                payload.get('externalUserId')
                or payload.get('patientId')
                or payload.get('patient_id')
                or ''
            ).strip()
            doctor_id_raw = payload.get('doctorId') or payload.get('doctor_id')
            patient_id_raw = payload.get('patientId') or payload.get('patient_id')
            questionnaire_id_raw = payload.get('questionnaireId') or payload.get('questionnaire_id')
            disease_type_raw = payload.get('diseaseType') or payload.get('disease_type')
            visit_type_raw = payload.get('visitType') or payload.get('visit_type')
            template_id_raw = payload.get('templateId')
            
            print('解析后的 externalUserId:', external_user_id)
            print('解析后的 templateId_raw:', template_id_raw)
            print('templateId_raw 类型:', type(template_id_raw))
            
            if not external_user_id:
                print('返回 400: externalUserId 不能为空')
                self._write_json({'error': 'externalUserId 不能为空'}, status=400)
                return
            
            if template_id_raw is None or str(template_id_raw).strip() == '':
                print('返回 400: templateId 不能为空')
                self._write_json({'error': 'templateId 不能为空'}, status=400)
                return
            
            # 尝试将templateId转换为整数
            try:
                template_id = int(str(template_id_raw).strip())
                print('转换后的 templateId:', template_id)
            except Exception:
                print('返回 400: templateId 必须是有效的整数')
                self._write_json({'error': 'templateId 必须是有效的整数'}, status=400)
                return

            try:
                start_kwargs = {}
                if doctor_id_raw not in (None, ''):
                    start_kwargs['doctor_id'] = int(str(doctor_id_raw))
                if patient_id_raw not in (None, ''):
                    start_kwargs['patient_id'] = int(str(patient_id_raw))
                record_id = start_questionnaire(external_user_id, template_id, **start_kwargs)
                self._write_json({'recordId': record_id})
            except Exception as exc:
                self._write_json({'error': str(exc)}, status=500)
            return

        if path == '/api/questionnaires/submit':
            # 打印日志
            print('接收到 /api/questionnaires/submit 请求')
            print('原始请求体:', payload)
            
            record_id = payload.get('recordId')
            answers = payload.get('answers')
            doctor_id_raw = payload.get('doctorId') or payload.get('doctor_id')
            patient_id_raw = payload.get('patientId') or payload.get('patient_id')
            questionnaire_id_raw = payload.get('questionnaireId') or payload.get('questionnaire_id')
            disease_type_raw = payload.get('diseaseType') or payload.get('disease_type') or ''
            visit_type_raw = payload.get('visitType') or payload.get('visit_type') or ''
            
            print('解析后的 recordId:', record_id)
            print('解析后的 recordId 类型:', type(record_id))
            print('解析后的 answers:', answers)
            print('解析后的 answers 类型:', type(answers))
            
            # 详细校验日志
            print(f"[questionnaire-submit] patientId={patient_id_raw} doctorId={doctor_id_raw} questionnaireId={questionnaire_id_raw} diseaseType={disease_type_raw} visitType={visit_type_raw}")

            if not record_id:
                print('返回 400: recordId 为空')
                self._write_json({'error': 'recordId 不能为空'}, status=400)
                return
            
            # 尝试将recordId转换为整数
            try:
                record_id = int(str(record_id))
                print('转换后的 recordId:', record_id)
            except Exception:
                print('返回 400: recordId 必须是有效的整数')
                self._write_json({'error': 'recordId 必须是有效的整数'}, status=400)
                return
            
            if not answers:
                print('返回 400: answers 为空')
                self._write_json({'error': 'answers 不能为空'}, status=400)
                return
            
            if not isinstance(answers, list):
                print('返回 400: answers 不是数组类型')
                self._write_json({'error': 'answers 必须是有效的数组'}, status=400)
                return
            
            print('参数校验通过，开始调用 submit_questionnaire')
            try:
                submit_kwargs = {}
                if doctor_id_raw not in (None, ''):
                    submit_kwargs['doctor_id'] = int(str(doctor_id_raw))
                if patient_id_raw not in (None, ''):
                    submit_kwargs['patient_id'] = int(str(patient_id_raw))
                if questionnaire_id_raw not in (None, ''):
                    submit_kwargs['questionnaire_id'] = str(questionnaire_id_raw)
                if disease_type_raw not in (None, ''):
                    submit_kwargs['disease_type'] = str(disease_type_raw)
                if visit_type_raw not in (None, ''):
                    submit_kwargs['visit_type'] = str(visit_type_raw)
                result = submit_questionnaire(record_id, answers, **submit_kwargs)
                print('submit_questionnaire 返回结果:', result)
                self._write_json(result)
            except Exception as exc:
                print('submit_questionnaire_sqlite 抛出异常:', exc)
                self._write_json({'error': str(exc)}, status=500)
            return

        self._write_json({'error': 'Not Found'}, status=404)

    def handle_login(self, payload: dict[str, Any]) -> None:
        code = str(payload.get('code') or '').strip()
        if not code:
            self._write_json({'error': 'code 不能为空'}, status=400)
            return

        try:
            self._write_json(exchange_code_for_session(code))
        except Exception as exc:
            print('DEBUG chat exception:', repr(exc))
            self._write_json({'error': str(exc)}, status=502)

    def handle_user_profile(self, payload: dict[str, Any]) -> None:
        try:
            from mysql_storage import get_user_profile_mysql, upsert_user_profile_mysql, get_user_by_user_code_mysql, get_user_sensitive_info_mysql, upsert_user_sensitive_info_mysql, normalize_user_profile

            user_id = payload.get('userId') or payload.get('user_id')
            if not user_id:
                self._write_json({'error': 'userId 不能为空'}, status=400)
                return

            user_id_int = None

            try:
                user_id_int = int(user_id)
            except ValueError:
                user_info = get_user_by_user_code_mysql(str(user_id))
                if user_info:
                    user_id_int = user_info['id']

            if user_id_int is None:
                self._write_json({'error': 'userId 无效，既不是有效的用户ID也不是有效的用户编码'}, status=400)
                return

            if self.command == 'GET':
                profile = get_user_profile_mysql(user_id_int)
                sensitive_info = get_user_sensitive_info_mysql(user_id_int) or {}

                if profile:
                    base_data = {
                        'nickname': profile.get('nickname'),
                        'avatarUrl': profile.get('avatarUrl'),
                        'gender': profile.get('gender'),
                        'birthday': profile.get('birthday'),
                        'updatedAt': profile.get('updatedAt'),
                    }

                    normalized = normalize_user_profile(base_data, sensitive_info)

                    self._write_json({
                        'success': True,
                        'data': normalized
                    })
                else:
                    self._write_json({
                        'success': True,
                        'data': None
                    })
            # POST 请求：保存用户资料
            elif self.command == 'POST':
                # 过滤头像：如果是微信临时路径，不保存
                avatar_url = payload.get('avatarUrl') or payload.get('avatar_url')
                if avatar_url and avatar_url.startswith('http://tmp/'):
                    avatar_url = None
                
                # 保存基本资料
                profile = upsert_user_profile_mysql(
                    user_id=user_id_int,
                    nickname=payload.get('nickname'),
                    avatar_url=avatar_url,
                    gender=payload.get('gender'),
                    birthday=payload.get('birthday'),
                )
                
                # 保存敏感信息（手机号、身份证号）
                sensitive_info = {}
                try:
                    sensitive_info = upsert_user_sensitive_info_mysql(
                        user_id=user_id_int,
                        phone=payload.get('phone'),
                        id_card=payload.get('idCard'),
                    )
                except ValueError as e:
                    self._write_json({
                        'success': False,
                        'error': str(e)
                    })
                    return

                base_data = {
                    'nickname': profile.get('nickname'),
                    'avatarUrl': profile.get('avatarUrl'),
                    'gender': profile.get('gender'),
                    'birthday': profile.get('birthday'),
                    'updatedAt': profile.get('updatedAt'),
                }

                normalized = normalize_user_profile(base_data, sensitive_info)

                self._write_json({
                    'success': True,
                    'data': normalized
                })
            else:
                self._write_json({'error': '不支持的请求方法'}, status=405)
        except Exception as exc:
            print(f'[ERROR] handle_user_profile 异常: {repr(exc)}')
            self._write_json({'error': str(exc)}, status=500)

    def handle_avatar_upload(self) -> None:
        import os
        import time
        from cgi import FieldStorage

        content_type = self.headers.get('Content-Type', '')

        if 'multipart/form-data' not in content_type:
            self._write_json({'error': '请求必须是 multipart/form-data 格式'}, status=400)
            return

        try:
            form = FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={
                    'REQUEST_METHOD': 'POST',
                    'CONTENT_TYPE': content_type,
                }
            )

            user_id = form.getvalue('userId')
            user_code = form.getvalue('userCode')

            if not user_id and not user_code:
                self._write_json({'error': 'userId 或 userCode 不能为空'}, status=400)
                return

            if 'file' not in form:
                self._write_json({'error': '缺少 file 字段'}, status=400)
                return

            file_item = form['file']
            if not file_item.filename or not file_item.file:
                self._write_json({'error': '无效的文件'}, status=400)
                return

            filename = file_item.filename.lower()
            allowed_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
            file_ext = os.path.splitext(filename)[1]

            if file_ext not in allowed_extensions:
                self._write_json({'error': '只支持 jpg、jpeg、png、webp 格式'}, status=400)
                return

            file_data = file_item.file.read()
            max_size = 5 * 1024 * 1024

            if len(file_data) > max_size:
                self._write_json({'error': '文件大小不能超过 5MB'}, status=400)
                return

            base_dir = os.path.dirname(os.path.abspath(__file__))
            avatars_dir = os.path.join(base_dir, 'Image', 'avatars')

            if not os.path.exists(avatars_dir):
                os.makedirs(avatars_dir, exist_ok=True)

            safe_user_code = str(user_code or user_id).replace('/', '_').replace('\\', '_')
            timestamp = int(time.time() * 1000)
            saved_filename = f"{safe_user_code}_{timestamp}{file_ext}"
            saved_path = os.path.join(avatars_dir, saved_filename)

            with open(saved_path, 'wb') as f:
                f.write(file_data)

            avatar_url = f"https://miniprogram.huiliaoyiyuan.com/uploads/avatars/{saved_filename}"

            print(f'[avatar] 上传成功: {saved_filename}, 大小: {len(file_data)} bytes')

            self._write_json({
                'success': True,
                'data': {
                    'avatarUrl': avatar_url
                }
            })

        except Exception as e:
            print(f'[avatar] 上传失败: {e}')
            self._write_json({'error': f'上传失败: {str(e)}'}, status=500)

    def handle_chat_history_get(self, path: str, query: dict[str, list[str]]) -> bool:
        if path == '/api/chat/sessions':
            identity = current_user_identity({
                'userId': (query.get('userId') or query.get('user_id') or [''])[0],
                'openid': (query.get('openid') or [''])[0],
            })
            assistant_id = str((query.get('assistantId') or query.get('assistant_id') or [''])[0]).strip() or None

            sessions = list_chat_sessions(
                openid=identity['openid'],
                user_id=identity['userId'],
                assistant_id=assistant_id,
            )
            self._write_json({'sessions': sessions})
            return True

        if path == '/api/chat/messages':
            session_uuid = str((query.get('sessionId') or query.get('session_id') or [''])[0]).strip()
            if not session_uuid:
                self._write_json({'error': 'sessionId 涓嶈兘涓虹┖'}, status=400)
                return True

            messages = list_chat_messages(session_uuid)
            self._write_json({'sessionId': session_uuid, 'messages': messages})
            return True

        return False

    def handle_chat_history_post(self, path: str, payload: dict[str, Any]) -> bool:
        if path == '/api/chat/session/delete':
            session_uuid = str(payload.get('sessionId') or payload.get('session_uuid') or '').strip()
            if not session_uuid:
                self._write_json({'error': 'sessionId 涓嶈兘涓虹┖'}, status=400)
                return True

            try:
                delete_chat_session(session_uuid)
                self._write_json({'success': True, 'sessionId': session_uuid})
            except Exception as exc:
                self._write_json({'error': str(exc)}, status=500)
            return True

        return False

    def handle_subscription_record(self, payload: dict[str, Any]) -> None:
        user_id = str(payload.get('userId') or payload.get('user_id') or '').strip()
        openid = str(payload.get('openid') or '').strip()
        template_id = str(payload.get('templateId') or payload.get('template_id') or '').strip()
        scene = str(payload.get('scene') or '').strip()
        subscribe_status = str(
            payload.get('subscribeStatus') or payload.get('subscribe_status') or ''
        ).strip()

        if not user_id:
            user_id = openid

        if not openid:
            try:
                openid = resolve_subscription_openid(user_id, openid)
            except ValueError as exc:
                self._write_json({'success': False, 'error': str(exc)}, status=400)
                return

        if not openid or not template_id or not scene or not subscribe_status:
            self._write_json(
                {'error': 'openid、templateId、scene、subscribeStatus 不能为空'},
                status=400,
            )
            return

        try:
            record_subscription_result(
                user_id=user_id,
                openid=openid,
                template_id=template_id,
                scene=scene,
                subscribe_status=subscribe_status,
            )
            self._write_json({'success': True})
        except Exception as exc:
            self._write_json({'error': str(exc)}, status=502)

    def handle_subscription_config(self, payload: dict[str, Any]) -> None:
        scene = str(payload.get('scene') or payload.get('sceneName') or '').strip()
        if scene != 'tongue_reminder':
            self._write_json({'success': False, 'error': '不支持的 scene'}, status=400)
            return

        user_id, openid = resolve_subscription_identity(
            payload.get('userId') or payload.get('user_id'),
            payload.get('openid'),
        )
        if not user_id:
            self._write_json({'success': False, 'error': '未找到用户openid，请重新登录'}, status=400)
            return

        normalized_payload = dict(payload)
        normalized_payload['userId'] = user_id
        if openid:
            normalized_payload['openid'] = openid

        self.handle_tongue_reminder_save_config(normalized_payload)

    def handle_subscription_enable(self, payload: dict[str, Any]) -> None:
        scene = str(payload.get('scene') or payload.get('sceneName') or '').strip()
        if scene != 'tongue_reminder':
            self._write_json({'success': False, 'error': '不支持的 scene'}, status=400)
            return

        user_id, openid = resolve_subscription_identity(
            payload.get('userId') or payload.get('user_id'),
            payload.get('openid'),
        )
        if not user_id:
            self._write_json({'success': False, 'error': '未找到用户openid，请重新登录'}, status=400)
            return

        from reminder_storage import get_tongue_reminder_status_mysql

        status = get_tongue_reminder_status_mysql(user_id)
        if not status.get('configured'):
            self._write_json({'success': False, 'error': '请先设置提醒频率和提醒时间'}, status=400)
            return

        normalized_payload = dict(payload)
        normalized_payload['userId'] = user_id
        if openid:
            normalized_payload['openid'] = openid

        self.handle_tongue_reminder_enable(normalized_payload)

    def handle_subscription_disable(self, payload: dict[str, Any]) -> None:
        scene = str(payload.get('scene') or payload.get('sceneName') or '').strip()
        if scene != 'tongue_reminder':
            self._write_json({'success': False, 'error': '不支持的 scene'}, status=400)
            return

        user_id, openid = resolve_subscription_identity(
            payload.get('userId') or payload.get('user_id'),
            payload.get('openid'),
        )
        if not user_id:
            self._write_json({'success': False, 'error': '未找到用户openid，请重新登录'}, status=400)
            return

        normalized_payload = dict(payload)
        normalized_payload['userId'] = user_id
        if openid:
            normalized_payload['openid'] = openid

        self.handle_tongue_reminder_disable(normalized_payload)

    def handle_tongue_reminder_enable(self, payload: dict[str, Any]) -> None:
        user_id = str(payload.get('userId') or payload.get('user_id') or '').strip()

        if not user_id:
            self._write_json({'error': 'userId 不能为空'}, status=400)
            return

        try:
            from reminder_storage import (
                get_tongue_reminder_status_mysql,
                upsert_tongue_reminder_mysql,
                validate_reminder_interval_days,
                validate_reminder_time,
            )

            print(f'[tongue-reminder] enable 请求: userId={user_id}')
            print(f'[tongue-reminder] 前端传入参数: {payload}')

            existing_status = get_tongue_reminder_status_mysql(user_id)
            if not existing_status.get('configured'):
                self._write_json({'success': False, 'error': '请先设置提醒频率和提醒时间'}, status=400)
                return

            reminder_time = str(
                existing_status.get('remindTime')
                or existing_status.get('reminderTime')
                or ''
            ).strip()
            reminder_interval_days_raw = existing_status.get('intervalDays') or existing_status.get('reminderIntervalDays')

            if not reminder_time or reminder_interval_days_raw is None:
                self._write_json({'success': False, 'error': '请先设置提醒频率和提醒时间'}, status=400)
                return

            validated_time = validate_reminder_time(reminder_time)
            validated_interval = validate_reminder_interval_days(reminder_interval_days_raw)

            print(f'[tongue-reminder] 最终启用参数: time={validated_time}, interval={validated_interval}天')

            result = upsert_tongue_reminder_mysql(
                user_id=user_id,
                reminder_time=validated_time,
                reminder_interval_days=validated_interval,
                enabled=True,
            )
            
            print(f'[tongue-reminder] enable 成功: {result}')
            self._write_json({'success': True, 'data': result})
        except Exception as exc:
            print(f'[tongue-reminder] enable 失败: {exc}')
            import traceback
            traceback.print_exc()
            self._write_json({'error': str(exc)}, status=500)

    def handle_tongue_reminder_save_config(self, payload: dict[str, Any]) -> None:
        user_id = str(payload.get('userId') or payload.get('user_id') or '').strip()

        if not user_id:
            self._write_json({'error': 'userId 不能为空'}, status=400)
            return

        try:
            from reminder_storage import save_tongue_reminder_config_mysql

            print(f'[tongue-reminder] save-config 请求: userId={user_id}')
            print(f'[tongue-reminder] 前端传入参数: {payload}')

            reminder_time = payload.get('remindTime') or payload.get('reminderTime') or payload.get('reminder_time')
            interval_days_raw = (
                payload.get('intervalDays')
                or payload.get('reminderIntervalDays')
                or payload.get('reminder_interval_days')
            )
            frequency = str(payload.get('frequency') or '').strip().lower()
            if interval_days_raw is None and frequency:
                if frequency == 'daily':
                    interval_days_raw = 1
                elif frequency == 'weekly':
                    interval_days_raw = 7
                elif frequency.startswith('every_') and frequency.endswith('_days'):
                    middle = frequency[len('every_'):-len('_days')]
                    interval_days_raw = middle

            if reminder_time is None and interval_days_raw is None:
                self._write_json({
                    'error': '至少需要提供一个配置项 remindTime 或 intervalDays'
                }, status=400)
                return

            kwargs = {'user_id': user_id}

            if reminder_time is not None:
                kwargs['reminder_time'] = str(reminder_time).strip()
                print(f'[tongue-reminder] 将保存时间: {kwargs["reminder_time"]}')

            if interval_days_raw is not None:
                try:
                    kwargs['reminder_interval_days'] = int(interval_days_raw)
                    print(f'[tongue-reminder] 将保存频率: {kwargs["reminder_interval_days"]}天')
                except (ValueError, TypeError):
                    self._write_json({
                        'error': f'intervalDays 必须是有效的整数，收到: {interval_days_raw}'
                    }, status=400)
                    return

            result = save_tongue_reminder_config_mysql(**kwargs)

            print(f'[tongue-reminder] save-config 成功: {result}')
            self._write_json({'success': True, 'data': result})
        except Exception as exc:
            print(f'[tongue-reminder] save-config 失败: {exc}')
            import traceback
            traceback.print_exc()
            self._write_json({'error': str(exc)}, status=500)

    def handle_tongue_reminder_disable(self, payload: dict[str, Any]) -> None:
        user_id = str(payload.get('userId') or payload.get('user_id') or '').strip()

        if not user_id:
            self._write_json({'error': 'userId 涓嶈兘涓虹┖'}, status=400)
            return

        try:
            result = disable_tongue_reminder(user_id=user_id)
            self._write_json({'success': True, 'data': result})
        except Exception as exc:
            print(f'[tongue-reminder] disable 失败: {exc}')
            self._write_json({'error': str(exc)}, status=500)

    def handle_appointment_reminder(self, payload: dict[str, Any]) -> None:
        appointment_id = str(payload.get('appointmentId') or '').strip() or uuid.uuid4().hex
        user_id = str(payload.get('userId') or payload.get('user_id') or '').strip() or None
        openid = str(payload.get('openid') or '').strip()
        doctor_name = str(payload.get('doctorName') or '门诊医生').strip()
        clinic_time = str(payload.get('clinicTime') or '').strip()
        clinic_location = str(payload.get('clinicLocation') or '').strip()
        remark = str(payload.get('remark') or '').strip() or None
        status = str(payload.get('status') or '待就诊').strip()

        if not openid or not clinic_time or not clinic_location:
            self._write_json({'error': 'openid、clinicTime、clinicLocation 不能为空'}, status=400)
            return

        try:
            save_appointment_reminder(
                appointment_id=appointment_id,
                user_id=user_id,
                openid=openid,
                doctor_name=doctor_name,
                clinic_time=clinic_time,
                clinic_location=clinic_location,
                remark=remark,
                status=status,
            )

            notify_result = send_subscribe_message(
                openid=openid,
                scene='appointment_reminder',
                biz_id=appointment_id,
                context={
                    'appointment_id': appointment_id,
                    'doctor_name': doctor_name,
                    'clinic_time': clinic_time,
                    'clinic_location': safe_summary(clinic_location),
                    'remark': safe_summary(remark or ''),
                },
            )

            self._write_json(
                {
                    'success': True,
                    'appointmentId': appointment_id,
                    'notifyResult': notify_result,
                }
            )
        except Exception as exc:
            self._write_json({'error': str(exc)}, status=502)

    def handle_mock_send(self, payload: dict[str, Any]) -> None:
        scene = str(payload.get('scene') or '').strip()
        openid = str(payload.get('openid') or '').strip()

        if scene not in {'ai_reply', 'tongue_result', 'appointment_reminder'} or not openid:
            self._write_json({'error': 'scene 或 openid 无效'}, status=400)
            return

        context_map = {
            'ai_reply': {
                'assistant_id': 'xiaohui',
                'assistant_name': '小慧',
                'reply_id': str(payload.get('replyId') or uuid.uuid4().hex),
                'summary': '您的 AI 回复已准备好',
                'event_time': str(payload.get('eventTime') or '点击查看详情'),
            },
            'tongue_result': {
                'analysis_id': str(payload.get('analysisId') or uuid.uuid4().hex),
                'subject': '平和体质倾向',
                'summary': '舌诊报告已生成，可点击查看',
                'event_time': str(payload.get('eventTime') or '点击查看详情'),
            },
            'appointment_reminder': {
                'appointment_id': str(payload.get('appointmentId') or uuid.uuid4().hex),
                'doctor_name': str(payload.get('doctorName') or '门诊医生'),
                'clinic_time': str(payload.get('clinicTime') or '请填写就诊时间'),
                'clinic_location': str(payload.get('clinicLocation') or '门诊诊室'),
                'remark': str(payload.get('remark') or '请按时到诊'),
            },
        }

        try:
            biz_id = (
                context_map[scene].get('reply_id')
                or context_map[scene].get('analysis_id')
                or context_map[scene].get('appointment_id')
            )
            self._write_json(
                send_subscribe_message(
                    openid=openid,
                    scene=scene,
                    biz_id=str(biz_id),
                    context=context_map[scene],
                )
            )
        except Exception as exc:
            self._write_json({'error': str(exc)}, status=502)

    def handle_test_send(self, payload: dict[str, Any]) -> None:
        user_id = str(payload.get('userId') or payload.get('user_id') or '').strip()
        scene = str(payload.get('scene') or 'tongue_reminder').strip()

        print(f'[test-send] 收到测试发送请求: userId={user_id}, scene={scene}')

        if not user_id:
            print('[test-send] 错误: userId 不能为空')
            self._write_json({'error': 'userId 不能为空'}, status=400)
            return

        if scene != 'tongue_reminder':
            print(f'[test-send] 错误: 不支持的 scene={scene}，目前仅支持 tongue_reminder')
            self._write_json({'error': f'不支持的场景: {scene}，目前仅支持 tongue_reminder'}, status=400)
            return

        try:
            from reminder_storage import get_user_openid_by_user_id_mysql, get_tongue_reminder_status_mysql

            print(f'[test-send] 正在查询用户 {user_id} 的 openid...')

            openid = get_user_openid_by_user_id_mysql(user_id)

            if not openid:
                print(f'[test-send] 错误: 未找到用户 {user_id} 的 openid')
                self._write_json({'error': f'未找到用户 {user_id} 的 openid，请确认用户是否存在'}, status=404)
                return

            print(f'[test-send] 查询到 openid: {openid}')

            print(f'[test-send] 正在获取用户 {user_id} 的提醒配置...')
            reminder_status = get_tongue_reminder_status_mysql(user_id)

            template_id = reminder_status.get('templateId') or reminder_status.get('template_id') or ''
            enabled = reminder_status.get('enabled', False)

            print(f'[test-send] 用户配置 - templateId: {template_id}, enabled: {enabled}')

            if not template_id:
                print('[test-send] 错误: 未配置 templateId')
                self._write_json({'error': '未配置舌苔提醒模板ID，请先在 config.py 中配置 tongueReminderTemplateId'}, status=500)
                return

            if not enabled:
                print(f'[test-send] 警告: 用户 {user_id} 未开启舌苔提醒，但仍尝试发送测试消息')

            print(f'[test-send] 正在调用微信订阅消息发送 API...')
            print(f'[test-send] 参数 - openid: {openid}, scene: {scene}, templateId: {template_id}')

            import time
            start_time = time.time()

            result = send_tongue_reminder(openid)

            end_time = time.time()
            duration_ms = round((end_time - start_time) * 1000, 2)

            print(f'[test-send] 微信 API 调用完成，耗时: {duration_ms}ms')
            print(f'[test-send] 微信返回结果: {json.dumps(result, ensure_ascii=False, indent=2)}')

            response_data = {
                'success': True,
                'data': {
                    'userId': user_id,
                    'openid': openid,
                    'scene': scene,
                    'templateId': template_id,
                    'page': 'pages/tongue-upload/tongue-upload',
                    'wechatResult': result,
                    'durationMs': duration_ms,
                    'sentAt': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            }

            errcode = result.get('errcode', 0) if isinstance(result, dict) else -1

            if errcode == 0:
                print(f'[test-send] ✅ 发送成功! userId={user_id}, openid={openid}')
                self._write_json(response_data)
            else:
                errmsg = result.get('errmsg', '未知错误') if isinstance(result, dict) else str(result)
                print(f'[test-send] ❌ 发送失败! errcode={errcode}, errmsg={errmsg}')
                print(f'[test-send] 完整错误信息: {json.dumps(result, ensure_ascii=False, indent=2)}')

                response_data['success'] = False
                response_data['error'] = {
                    'errcode': errcode,
                    'errmsg': errmsg,
                    'message': f'微信订阅消息发送失败: {errmsg} ({errcode})'
                }
                self._write_json(response_data, status=502)

        except ValueError as ve:
            error_msg = str(ve)
            print(f'[test-send] 参数验证失败: {error_msg}')
            self._write_json({
                'error': error_msg,
                'type': 'ValidationError'
            }, status=400)

        except RuntimeError as re:
            error_msg = str(re)
            print(f'[test-send] 微信 API 运行时错误: {error_msg}')
            import traceback
            traceback.print_exc()

            self._write_json({
                'error': error_msg,
                'type': 'WechatAPIError',
                'message': f'微信 API 调用失败: {error_msg}'
            }, status=502)

        except Exception as e:
            error_msg = str(e)
            print(f'[test-send] ❌ 发送过程出现异常: {error_msg}')
            import traceback
            print(f'[test-send] 异常堆栈:')
            traceback.print_exc()

            self._write_json({
                'error': error_msg,
                'type': 'InternalServerError',
                'message': f'服务器内部错误: {error_msg}'
            }, status=500)

    def handle_chat(self, payload: dict[str, Any]) -> None:
        assistant_id = str(payload.get('assistantId') or '').strip()
        question = str(payload.get('question') or '').strip()
        chat_id = str(payload.get('chatId') or '').strip() or None
        session_uuid = str(payload.get('sessionId') or payload.get('session_id') or '').strip() or None
        identity = current_user_identity(payload)
        user_id = identity['userId']
        openid = identity['openid']

        if assistant_id not in SUPPORTED_ASSISTANTS:
            self._write_json({'error': 'assistantId 无效'}, status=400)
            return

        if not question:
            self._write_json({'error': 'question 不能为空'}, status=400)
            return

        try:
            session_uuid = session_uuid or uuid.uuid4().hex
            session_record = get_chat_session(session_uuid)

            if session_record and session_record.get('deletedAt'):
                session_uuid = uuid.uuid4().hex
                session_record = None

            owner_openid = openid or (session_record.get('openid') if session_record else None) or 'anonymous'
            owner_user_id = user_id or (session_record.get('userId') if session_record else None)
            llm_chat_id = chat_id or (session_record.get('llmChatId') if session_record else None)
            now_value = now_iso()

            if not session_record:
                upsert_chat_session(
                    session_uuid=session_uuid,
                    user_id=owner_user_id,
                    openid=owner_openid,
                    assistant_id=assistant_id,
                    llm_chat_id=llm_chat_id,
                    title=build_session_title(question),
                    preview=question,
                    message_count=0,
                    last_message_at=now_value,
                )
            else:
                upsert_chat_session(
                    session_uuid=session_uuid,
                    user_id=owner_user_id,
                    openid=owner_openid,
                    assistant_id=assistant_id,
                    llm_chat_id=llm_chat_id,
                    title=session_record.get('title') or build_session_title(question),
                    preview=question,
                    message_count=int(session_record.get('messageCount') or 0),
                    last_message_at=now_value,
                    deleted_at=None,
                )

            save_chat_message(
                message_uuid=uuid.uuid4().hex,
                session_uuid=session_uuid,
                role='user',
                message_type='text',
                content=question,
            )

            result = call_fastgpt(question, llm_chat_id)
            reply_id = uuid.uuid4().hex

            print('[CHAT-API] call_fastgpt 返回结果:')
            print(f'[CHAT-API]   result type: {type(result).__name__}')
            print(f'[CHAT-API]   result keys: {list(result.keys()) if isinstance(result, dict) else "N/A"}')
            print(f'[CHAT-API]   result 完整内容 (前3000字符): {json.dumps(result, ensure_ascii=False)[:3000]}')

            reply_content = str(result.get('content') or '').strip()
            final_chat_id = result.get('chatId') or llm_chat_id

            print(f'[CHAT-API]   最终 reply_content 长度: {len(reply_content)}')
            print(f'[CHAT-API]   最终 reply_content (前200字符): {reply_content[:200]}')
            print(f'[CHAT-API]   final_chat_id: {final_chat_id}')

            try:
                save_ai_reply(
                    reply_id=reply_id,
                    user_id=owner_user_id,
                    openid=owner_openid if owner_openid != 'anonymous' else None,
                    assistant_id=assistant_id,
                    question=question,
                    content=reply_content,
                    chat_id=final_chat_id,
                )
            except Exception as save_error:
                print(f'保存 AI 回复记录失败（非致命错误，继续返回结果）: {save_error}')

            save_chat_message(
                message_uuid=uuid.uuid4().hex,
                session_uuid=session_uuid,
                role='assistant',
                message_type='text',
                content=reply_content,
                llm_reply_id=reply_id,
            )

            upsert_chat_session(
                session_uuid=session_uuid,
                user_id=owner_user_id,
                openid=owner_openid,
                assistant_id=assistant_id,
                llm_chat_id=final_chat_id,
                title=session_record.get('title') if session_record else build_session_title(question),
                preview=build_message_preview(reply_content or question),
                message_count=int((session_record.get('messageCount') if session_record else 0) or 0) + 2,
                last_message_at=now_value,
                deleted_at=None,
            )

            notify_result = None
            if owner_openid and owner_openid != 'anonymous':
                try:
                    notify_result = send_subscribe_message(
                        openid=owner_openid,
                        scene='ai_reply',
                        biz_id=reply_id,
                        context={
                            'assistant_id': assistant_id,
                            'assistant_name': '小惠' if assistant_id == 'xiaohui' else '陈主任',
                            'reply_id': reply_id,
                            'summary': safe_summary(reply_content),
                            'event_time': '点击查看详情',
                        },
                    )
                except Exception as notify_exc:
                    print(f'[CHAT-API] ai_reply 订阅消息发送失败，已跳过: {notify_exc}')
                    notify_result = {
                        'success': False,
                        'skipped': True,
                        'error': str(notify_exc),
                    }

            self._write_json(
                {
                    'assistantId': assistant_id,
                    'content': reply_content,
                    'chatId': final_chat_id,
                    'sessionId': session_uuid,
                    'replyId': reply_id,
                    'notifyResult': notify_result,
                }
            )
        except Exception as exc:
            self._write_json({'error': str(exc)}, status=502)

    def log_message(self, format: str, *args: Any) -> None:
        return


def run_server() -> None:
    host = config['server']['host']
    port = config['server']['port']
    server = ThreadingHTTPServer((host, port), ChatProxyHandler)
    start_tongue_reminder_scheduler()
    print(f'Chat proxy server running on http://{host}:{port}')
    server.serve_forever()


if __name__ == '__main__':
    run_server()
11
