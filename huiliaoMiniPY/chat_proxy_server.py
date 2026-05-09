import json
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Optional
from urllib import error, parse, request

from config import config
from db import (
    get_ai_reply,
    get_appointment_reminder,
    get_questionnaire_detail,
    get_questionnaire_options,
    get_questionnaire_report,
    list_subscription_records,
    save_ai_reply,
    save_appointment_reminder,
    start_questionnaire,
    submit_questionnaire,
)
from wechat_subscription import (
    exchange_code_for_session,
    get_frontend_subscribe_config,
    record_subscription_result,
    send_subscribe_message,
)

SUPPORTED_ASSISTANTS = {'xiaohui', 'chen'}


def call_fastgpt(question: str, chat_id: Optional[str] = None) -> dict[str, Any]:
    base_url = config['fastgpt']['base_url'].rstrip('/')
    url = f"{base_url}/v1/chat/completions"

    payload = {
        'chatId': chat_id or 'test',
        'stream': False,
        'variables': {},
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

    content = (
        response_data.get('choices', [{}])[0]
        .get('message', {})
        .get('content', '')
        .strip()
    )

    if not content:
        raise RuntimeError('上游接口返回成功，但没有有效回复内容')

    return {
        'content': content,
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


class ChatProxyHandler(BaseHTTPRequestHandler):
    server_version = 'ChatProxy/2.0'

    def _write_json(self, data: Any, status: int = 200) -> None:
        encoded = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(encoded)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        self.end_headers()
        self.wfile.write(encoded)

    def do_OPTIONS(self) -> None:
        self._write_json({})

    def do_GET(self) -> None:
        import os
        import mimetypes

        parsed_url = parse.urlparse(self.path)
        path = parsed_url.path
        query = parse.parse_qs(parsed_url.query)

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

        if path == '/api/user/profile':
            # GET 请求从查询参数获取 userId
            user_id = str((query.get('userId') or [''])[0]).strip()
            if user_id:
                self.handle_user_profile({'userId': user_id})
            else:
                self._write_json({'error': 'userId 不能为空'}, status=400)
            return

        if path == '/api/subscription/status':
            openid = str((query.get('openid') or [''])[0]).strip()
            if not openid:
                self._write_json({'error': 'openid 不能为空'}, status=400)
                return

            self._write_json({'records': list_subscription_records(openid)})
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

        if path == '/api/questionnaires/report':
            record_id_raw = str((query.get('recordId') or [''])[0]).strip()
            print('接收到 /api/questionnaires/report 请求，recordId_raw:', record_id_raw)
            print('recordId_raw 类型:', type(record_id_raw))
            
            if not record_id_raw:
                self._write_json({'error': 'recordId 不能为空'}, status=400)
                return

            # 尝试将recordId转换为整数
            try:
                record_id = int(record_id_raw)
                print('转换后的 recordId:', record_id)
                result = get_questionnaire_report(record_id)
                self._write_json(result)
            except ValueError as exc:
                self._write_json({'error': str(exc)}, status=404)
            except Exception as exc:
                self._write_json({'error': str(exc)}, status=500)
            return

        self._write_json({'error': 'Not Found'}, status=404)

    def do_POST(self) -> None:
        path = parse.urlparse(self.path).path

        if path == '/api/user/avatar/upload':
            self.handle_avatar_upload()
            return

        try:
            payload = parse_json_body(self)
        except ValueError as exc:
            self._write_json({'error': str(exc)}, status=400)
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

        if path == '/api/chat':
            self.handle_chat(payload)
            return

        if path == '/api/appointments/reminder':
            self.handle_appointment_reminder(payload)
            return

        if path == '/api/subscription/mock-send':
            self.handle_mock_send(payload)
            return

        if path == '/api/questionnaires/start':
            # 打印日志
            print('接收到 /api/questionnaires/start 请求')
            print('原始请求体:', payload)
            
            external_user_id = str(payload.get('externalUserId') or '').strip()
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
                record_id = start_questionnaire(external_user_id, template_id)
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
            
            print('解析后的 recordId:', record_id)
            print('解析后的 recordId 类型:', type(record_id))
            print('解析后的 answers:', answers)
            print('解析后的 answers 类型:', type(answers))
            
            # 详细校验日志
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
                result = submit_questionnaire(record_id, answers)
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
            from mysql_storage import get_user_profile_mysql, upsert_user_profile_mysql, get_user_by_user_code_mysql, get_user_sensitive_info_mysql, upsert_user_sensitive_info_mysql
            
            user_id = payload.get('userId') or payload.get('user_id')
            if not user_id:
                self._write_json({'error': 'userId 不能为空'}, status=400)
                return
            
            user_id_int = None
            
            # 尝试将 userId 解析为整数（users.id）
            try:
                user_id_int = int(user_id)
            except ValueError:
                # 如果不是整数，尝试作为 user_code 查询
                user_info = get_user_by_user_code_mysql(str(user_id))
                if user_info:
                    user_id_int = user_info['id']
            
            if user_id_int is None:
                self._write_json({'error': 'userId 无效，既不是有效的用户ID也不是有效的用户编码'}, status=400)
                return
            
            # GET 请求：获取用户资料
            if self.command == 'GET':
                profile = get_user_profile_mysql(user_id_int)
                sensitive_info = get_user_sensitive_info_mysql(user_id_int) or {}
                
                if profile:
                    self._write_json({
                        'success': True,
                        'data': {
                            'nickname': profile.get('nickname'),
                            'avatarUrl': profile.get('avatarUrl'),
                            'gender': profile.get('gender'),
                            'birthday': profile.get('birthday'),
                            'updatedAt': profile.get('updatedAt'),
                            # 添加敏感信息（脱敏）
                            'phone': sensitive_info.get('phone'),
                            'phoneMasked': sensitive_info.get('phoneMasked'),
                            'idCardMasked': sensitive_info.get('idCardMasked'),
                        }
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
                    # 如果敏感信息校验失败，只返回错误，不影响基本资料保存
                    self._write_json({
                        'success': False,
                        'error': str(e)
                    })
                    return
                
                self._write_json({
                    'success': True,
                    'data': {
                        'nickname': profile.get('nickname'),
                        'avatarUrl': profile.get('avatarUrl'),
                        'gender': profile.get('gender'),
                        'birthday': profile.get('birthday'),
                        'updatedAt': profile.get('updatedAt'),
                        # 返回脱敏后的敏感信息
                        'phone': sensitive_info.get('phone'),
                        'phoneMasked': sensitive_info.get('phoneMasked'),
                        'idCardMasked': sensitive_info.get('idCardMasked'),
                    }
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

    def handle_chat(self, payload: dict[str, Any]) -> None:
        assistant_id = str(payload.get('assistantId') or '').strip()
        question = str(payload.get('question') or '').strip()
        chat_id = str(payload.get('chatId') or '').strip() or None
        user_id = str(payload.get('userId') or payload.get('user_id') or '').strip() or None
        openid = str(payload.get('openid') or '').strip() or None

        if assistant_id not in SUPPORTED_ASSISTANTS:
            self._write_json({'error': 'assistantId 无效'}, status=400)
            return

        if not question:
            self._write_json({'error': 'question 不能为空'}, status=400)
            return

        try:
            result = call_fastgpt(question, chat_id)
            reply_id = uuid.uuid4().hex

            try:
                save_ai_reply(
                    reply_id=reply_id,
                    user_id=user_id,
                    openid=openid,
                    assistant_id=assistant_id,
                    question=question,
                    content=result['content'],
                    chat_id=result.get('chatId'),
                )
            except Exception as save_error:
                print(f'保存 AI 回复记录失败（非致命错误，继续返回结果）: {save_error}')

            notify_result = None
            if openid:
                notify_result = send_subscribe_message(
                    openid=openid,
                    scene='ai_reply',
                    biz_id=reply_id,
                    context={
                        'assistant_id': assistant_id,
                        'assistant_name': '小慧' if assistant_id == 'xiaohui' else '陈主任',
                        'reply_id': reply_id,
                        'summary': safe_summary(result['content']),
                        'event_time': '点击查看详情',
                    },
                )

            self._write_json(
                {
                    'assistantId': assistant_id,
                    'content': result['content'],
                    'chatId': result.get('chatId'),
                    'replyId': reply_id,
                    'notifyResult': notify_result,
                }
            )
        except Exception as exc:
            self._write_json({'error': str(exc)}, status=502)

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

    def log_message(self, format: str, *args: Any) -> None:
        return


def run_server() -> None:
    host = config['server']['host']
    port = config['server']['port']
    server = ThreadingHTTPServer((host, port), ChatProxyHandler)
    print(f'Chat proxy server running on http://{host}:{port}')
    server.serve_forever()


if __name__ == '__main__':
    run_server()
