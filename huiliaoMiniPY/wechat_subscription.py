import json
import re
from datetime import datetime, timedelta
from typing import Any, Optional
from urllib import error, parse, request

from config import config
from db import (
    find_sendable_subscription,
    get_meta,
    insert_send_log,
    mark_subscription_sent,
    upsert_subscription_record,
    upsert_user,
)
from storage import now_iso

DEFAULT_SCENE_CONFIG: dict[str, dict[str, Any]] = {
    'ai_reply': {
        'name': 'AI问答结果提醒',
        'description': 'AI 回复完成后发送简洁服务通知',
        'template_id': 'TODO_MINIPROGRAM_AI_REPLY_TEMPLATE_ID',
        'page': 'pages/chen-agent/chen-agent?assistantId={{assistant_id}}&replyId={{reply_id}}',
        'keywords': {
            'thing1': 'AI回复已完成',
            'thing2': '{{assistant_name}}',
            'thing3': '{{summary}}',
            'time4': '{{event_time}}',
        },
    },
    'tongue_result': {
        'name': '舌诊结果提醒',
        'description': '舌诊报告生成后发送服务通知',
        'template_id': 'TODO_MINIPROGRAM_TONGUE_RESULT_TEMPLATE_ID',
        'page': 'pages/comprehensive-report/comprehensive-report?scene=tongue&analysisId={{analysis_id}}',
        'keywords': {
            'thing1': '舌诊报告已生成',
            'thing2': '{{subject}}',
            'thing3': '{{summary}}',
            'time4': '{{event_time}}',
        },
    },
    'appointment_reminder': {
        'name': '预约/复诊提醒',
        'description': '预约、复诊或到诊前提醒',
        'template_id': 'TODO_MINIPROGRAM_APPOINTMENT_TEMPLATE_ID',
        'page': 'pages/appointment-detail/appointment-detail?appointmentId={{appointment_id}}',
        'keywords': {
            'thing1': '复诊提醒',
            'thing2': '{{doctor_name}}',
            'date3': '{{clinic_time}}',
            'thing4': '{{clinic_location}}',
        },
    },
}

TOKEN_META_KEY = 'wechat_access_token_cache'


def get_wechat_mini_program_config() -> dict[str, Any]:
    mini_program = config.get('wechat_mini_program') or {}
    custom_templates = mini_program.get('subscribe_templates') or {}
    merged_templates: dict[str, dict[str, Any]] = {}

    for scene, default_config in DEFAULT_SCENE_CONFIG.items():
        current_config = custom_templates.get(scene) or {}
        merged_templates[scene] = {
            **default_config,
            **current_config,
            'keywords': {
                **default_config.get('keywords', {}),
                **(current_config.get('keywords') or {}),
            },
        }

    # 优先读取 wechat 配置节点
    wechat_config = config.get('wechat') or {}
    app_id = wechat_config.get('appid') or wechat_config.get('app_id')
    
    # 兼容 wxapp 配置节点
    if not app_id:
        wxapp_config = config.get('wxapp') or {}
        app_id = wxapp_config.get('appid') or wxapp_config.get('app_id')
    
    # 兼容旧的 wechat_mini_program 配置节点
    if not app_id:
        app_id = mini_program.get('app_id')
    
    # 设置默认值
    if not app_id or str(app_id).startswith('TODO_'):
        app_id = 'TODO_MINIPROGRAM_APPID'

    # 同样处理 app_secret
    app_secret = wechat_config.get('secret') or wechat_config.get('app_secret')
    if not app_secret:
        wxapp_config = config.get('wxapp') or {}
        app_secret = wxapp_config.get('secret') or wxapp_config.get('app_secret')
    if not app_secret:
        app_secret = mini_program.get('app_secret')
    if not app_secret or str(app_secret).startswith('TODO_'):
        app_secret = 'TODO_MINIPROGRAM_SECRET'

    return {
        'app_id': app_id,
        'app_secret': app_secret,
        'subscribe_templates': merged_templates,
    }


def scene_is_configured(scene_config: dict[str, Any]) -> bool:
    template_id = str(scene_config.get('template_id') or '').strip()
    return bool(template_id and not template_id.startswith('TODO_'))


def mini_program_is_configured() -> bool:
    wx_config = get_wechat_mini_program_config()
    app_id = str(wx_config.get('app_id') or '').strip()
    app_secret = str(wx_config.get('app_secret') or '').strip()
    return (
        bool(app_id and not app_id.startswith('TODO_'))
        and bool(app_secret and not app_secret.startswith('TODO_'))
    )


def get_frontend_subscribe_config() -> dict[str, Any]:
    wx_config = get_wechat_mini_program_config()
    scene_items = []

    for scene, scene_config in wx_config['subscribe_templates'].items():
        scene_items.append(
            {
                'scene': scene,
                'name': scene_config.get('name'),
                'description': scene_config.get('description'),
                'templateId': scene_config.get('template_id'),
                'page': scene_config.get('page'),
                'enabled': scene_is_configured(scene_config),
            }
        )

    return {
        'configured': mini_program_is_configured(),
        'scenes': scene_items,
    }


def http_json_request(url: str, payload: Optional[dict[str, Any]] = None, method: str = 'GET') -> dict[str, Any]:
    request_data = None
    headers = {}

    if payload is not None:
        request_data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        headers['Content-Type'] = 'application/json'

    req = request.Request(url, data=request_data, headers=headers, method=method)

    try:
        with request.urlopen(req, timeout=15) as response:
            raw_body = response.read().decode('utf-8')
    except error.HTTPError as exc:
        error_body = exc.read().decode('utf-8', errors='ignore')
        raise RuntimeError(error_body or f'微信接口返回 HTTP {exc.code}') from exc
    except error.URLError as exc:
        raise RuntimeError(f'微信接口连接失败: {exc.reason}') from exc

    return json.loads(raw_body)


def exchange_code_for_session(code: str) -> dict[str, Any]:
    wx_config = get_wechat_mini_program_config()
    app_id = wx_config['app_id']
    app_secret = wx_config['app_secret']

    if str(app_id).startswith('TODO_') or str(app_secret).startswith('TODO_'):
        raise RuntimeError('小程序 appid 或 secret 尚未配置')

    # 打印日志用于排查
    code_length = len(code) if code else 0
    code_prefix = code[:6] if code_length >= 6 else code
    code_suffix = code[-4:] if code_length >= 4 else ''
    print(f"[登录调试] appid: {app_id}")
    print(f"[登录调试] code 长度: {code_length}, 前缀: {code_prefix}, 后缀: {code_suffix}")

    query = parse.urlencode(
        {
            'appid': app_id,
            'secret': app_secret,
            'js_code': code,
            'grant_type': 'authorization_code',
        }
    )
    
    print(f"[登录调试] 请求微信接口: sns/jscode2session")
    result = http_json_request(
        f'https://api.weixin.qq.com/sns/jscode2session?{query}'
    )
    
    print(f"[登录调试] 微信接口返回: {json.dumps(result, ensure_ascii=False)}")

    errcode = result.get('errcode')
    if errcode:
        raise RuntimeError(result.get('errmsg') or f'登录失败: {errcode}')

    openid = str(result.get('openid') or '').strip()
    if not openid:
        raise RuntimeError('微信登录未返回 openid')

    # 使用 MySQL 版本的 upsert_user
    from mysql_storage import upsert_user_mysql, get_user_profile_mysql
    user_info = upsert_user_mysql(
        openid=openid,
        session_key=result.get('session_key'),
        unionid=result.get('unionid'),
    )

    # 获取用户资料
    user_id = user_info['id']
    profile = get_user_profile_mysql(user_id) or {}

    return {
        'userId': user_id,
        'userCode': user_info['userCode'],
        'openid': openid,
        'unionid': result.get('unionid'),
        'profile': {
            'nickname': profile.get('nickname'),
            'avatarUrl': profile.get('avatarUrl'),
            'gender': profile.get('gender'),
            'birthday': profile.get('birthday'),
        }
    }


def parse_cached_token() -> Optional[dict[str, Any]]:
    raw_value = get_meta(TOKEN_META_KEY)
    if not raw_value:
        return None

    try:
        cache_data = json.loads(raw_value)
    except json.JSONDecodeError:
        return None

    expires_at = str(cache_data.get('expires_at') or '')
    if not expires_at:
        return None

    try:
        expire_time = datetime.fromisoformat(expires_at)
    except ValueError:
        return None

    if expire_time <= datetime.now():
        return None

    access_token = str(cache_data.get('access_token') or '').strip()
    if not access_token:
        return None

    return cache_data


def cache_access_token(access_token: str, expires_in: int) -> None:
    expires_at = datetime.now() + timedelta(seconds=max(expires_in - 300, 60))
    set_meta(
        TOKEN_META_KEY,
        json.dumps(
            {
                'access_token': access_token,
                'expires_at': expires_at.isoformat(),
            },
            ensure_ascii=False,
        ),
    )


def fetch_access_token(force_refresh: bool = False) -> str:
    if not force_refresh:
        cache_data = parse_cached_token()
        if cache_data:
            return str(cache_data['access_token'])

    wx_config = get_wechat_mini_program_config()
    app_id = wx_config['app_id']
    app_secret = wx_config['app_secret']

    if str(app_id).startswith('TODO_') or str(app_secret).startswith('TODO_'):
        raise RuntimeError('小程序 appid 或 secret 尚未配置')

    query = parse.urlencode(
        {
            'grant_type': 'client_credential',
            'appid': app_id,
            'secret': app_secret,
        }
    )
    result = http_json_request(f'https://api.weixin.qq.com/cgi-bin/token?{query}')

    errcode = result.get('errcode')
    if errcode:
        raise RuntimeError(result.get('errmsg') or f'获取 access_token 失败: {errcode}')

    access_token = str(result.get('access_token') or '').strip()
    expires_in = int(result.get('expires_in') or 7200)
    if not access_token:
        raise RuntimeError('微信接口未返回 access_token')

    cache_access_token(access_token, expires_in)
    return access_token


def replace_template_values(template: str, context: dict[str, Any]) -> str:
    def replacer(match: re.Match[str]) -> str:
        key = match.group(1)
        value = context.get(key)
        return '' if value is None else str(value)

    return re.sub(r'{{\s*([\w_]+)\s*}}', replacer, template)


def normalize_page_path(page_path: str) -> str:
    return page_path.lstrip('/')


def build_subscribe_payload(
    *,
    scene: str,
    openid: str,
    context: dict[str, Any],
    page_path: Optional[str]
) -> tuple[str, dict[str, Any], str]:
    wx_config = get_wechat_mini_program_config()
    scene_config = wx_config['subscribe_templates'].get(scene)

    if not scene_config:
        raise RuntimeError(f'未找到场景配置: {scene}')

    template_id = str(scene_config.get('template_id') or '').strip()
    if not scene_is_configured(scene_config):
        raise RuntimeError(f'{scene} 的模板 ID 尚未配置')

    resolved_page = normalize_page_path(
        replace_template_values(page_path or str(scene_config.get('page') or ''), context)
    )
    data = {
        keyword: {
            'value': replace_template_values(str(value), context)
        }
        for keyword, value in (scene_config.get('keywords') or {}).items()
    }

    return template_id, {
        'touser': openid,
        'template_id': template_id,
        'page': resolved_page,
        'data': data,
    }, resolved_page


def record_subscription_result(
    *,
    user_id: str,
    openid: str,
    template_id: str,
    scene: str,
    subscribe_status: str
) -> None:
    accepted_at = now_iso() if subscribe_status == 'accept' else None
    upsert_subscription_record(
        user_id=user_id,
        openid=openid,
        template_id=template_id,
        scene=scene,
        subscribe_status=subscribe_status,
        accepted_at=accepted_at,
    )


def send_subscribe_message(
    *,
    openid: str,
    scene: str,
    context: dict[str, Any],
    biz_id: Optional[str] = None,
    page_path: Optional[str] = None,
) -> dict[str, Any]:
    template_id, payload, resolved_page = build_subscribe_payload(
        scene=scene,
        openid=openid,
        context=context,
        page_path=page_path,
    )

    subscription_record = find_sendable_subscription(openid, template_id, scene)
    if not subscription_record:
        return {
            'success': False,
            'skipped': True,
            'reason': 'no_active_subscription',
            'templateId': template_id,
        }

    def do_send(force_refresh_token: bool = False) -> dict[str, Any]:
        access_token = fetch_access_token(force_refresh=force_refresh_token)
        return http_json_request(
            f'https://api.weixin.qq.com/cgi-bin/message/subscribe/send?access_token={access_token}',
            payload,
            method='POST',
        )

    try:
        response = do_send(force_refresh_token=False)
        if response.get('errcode') in {40001, 42001}:
            response = do_send(force_refresh_token=True)
    except Exception as exc:
        insert_send_log(
            openid=openid,
            template_id=template_id,
            scene=scene,
            biz_id=biz_id,
            page_path=resolved_page,
            payload=payload,
            send_status='request_failed',
            errcode=None,
            errmsg=str(exc),
        )
        raise

    errcode = response.get('errcode')
    errmsg = response.get('errmsg')
    is_success = errcode in {None, 0}

    insert_send_log(
        openid=openid,
        template_id=template_id,
        scene=scene,
        biz_id=biz_id,
        page_path=resolved_page,
        payload=payload,
        send_status='success' if is_success else 'failed',
        errcode=None if errcode is None else str(errcode),
        errmsg=None if errmsg is None else str(errmsg),
    )

    if is_success:
        mark_subscription_sent(openid, template_id, scene)
    else:
        return {
            'success': False,
            'skipped': False,
            'templateId': template_id,
            'errcode': errcode,
            'errmsg': errmsg,
        }

    return {
        'success': True,
        'skipped': False,
        'templateId': template_id,
        'page': resolved_page,
    }
