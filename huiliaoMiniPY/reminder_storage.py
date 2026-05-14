from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Any, Optional

from config import config
from mysql_storage import (
    _to_int_or_none,
    get_mysql_connection,
    get_mysql_cursor,
    get_user_by_id_mysql,
    get_user_by_openid_mysql,
)


SHANGHAI_TZ = ZoneInfo('Asia/Shanghai')


def calculate_next_send_at(reminder_time: str, interval_days: int = 1) -> str:
    """
    计算下次发送时间

    规则：
    - 如果用户选择的时间今天还没到：nextSendAt = 今天 reminderTime
    - 如果今天已经过了这个时间：nextSendAt = 今天 + reminderIntervalDays 天 的 reminderTime

    Args:
        reminder_time: 提醒时间，格式 HH:mm
        interval_days: 间隔天数（1=每天, 2=每两天, 3=每三天, 7=每周）

    Returns:
        下次发送时间的字符串格式 'YYYY-MM-DD HH:MM:SS'
    """
    now = datetime.now(SHANGHAI_TZ)
    time_parts = str(reminder_time or '08:00').strip().split(':')
    hour = int(time_parts[0]) if len(time_parts) > 0 else 8
    minute = int(time_parts[1]) if len(time_parts) > 1 else 0

    target_time_today = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

    if now < target_time_today:
        next_send = target_time_today
    else:
        days_to_add = max(1, interval_days)
        next_send = target_time_today + timedelta(days=days_to_add)

    return next_send.strftime('%Y-%m-%d %H:%M:%S')


def validate_reminder_interval_days(interval_days: Any) -> int:
    """
    校验提醒间隔天数

    只允许：1(每天), 2(每两天), 3(每三天), 7(每周)

    Args:
        interval_days: 待校验的值

    Returns:
        校验后的有效值，无效则返回默认值 1
    """
    valid_values = [1, 2, 3, 7]
    try:
        value = int(interval_days)
        if value in valid_values:
            return value
    except (ValueError, TypeError):
        pass
    return 1


def validate_reminder_time(reminder_time: Any) -> str:
    """
    校验提醒时间格式

    必须是 HH:mm 格式，且时间合法（00-23小时，00-59分钟）

    Args:
        reminder_time: 待校验的值

    Returns:
        校验后的有效时间字符串，无效则返回默认值 '08:00'
    """
    time_str = str(reminder_time or '').strip()
    if not time_str:
        return '08:00'

    parts = time_str.split(':')
    if len(parts) != 2:
        return '08:00'

    try:
        hour = int(parts[0])
        minute = int(parts[1])
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return f'{hour:02d}:{minute:02d}'
    except ValueError:
        pass

    return '08:00'


def _ensure_user_subscribe_reminder_table_mysql(cursor) -> None:
    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS user_subscribe_reminder (
            id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT NOT NULL,
            openid VARCHAR(128) NOT NULL,
            reminder_type VARCHAR(64) NOT NULL,
            template_id VARCHAR(255) NOT NULL,
            reminder_time VARCHAR(8) NOT NULL DEFAULT '08:00',
            enabled TINYINT(1) NOT NULL DEFAULT 1,
            last_sent_date DATE NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY uniq_user_reminder_type (user_id, reminder_type),
            INDEX idx_user_subscribe_reminder_enabled_date (reminder_type, enabled, last_sent_date),
            INDEX idx_user_subscribe_reminder_openid (openid)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        '''
    )


def _ensure_user_subscribe_reminder_columns_mysql(cursor) -> None:
    for column_sql in [
        "ADD COLUMN reminder_time VARCHAR(8) NOT NULL DEFAULT '08:00'",
        'ADD COLUMN enabled TINYINT(1) NOT NULL DEFAULT 1',
        'ADD COLUMN last_sent_date DATE NULL',
        'ADD COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP',
        'ADD COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP',
        "ADD COLUMN reminder_interval_days INT NOT NULL DEFAULT 1 COMMENT '几天提醒一次'",
        "ADD COLUMN next_send_at DATETIME NULL COMMENT '下次应发送时间'",
        "ADD COLUMN last_sent_at DATETIME NULL COMMENT '上次实际发送时间'",
    ]:
        try:
            cursor.execute(f'ALTER TABLE user_subscribe_reminder {column_sql}')
        except Exception as exc:
            errno = getattr(exc, 'errno', None)
            if errno not in (1060, 1091):
                raise


def get_user_openid_by_user_id_mysql(user_id: Any) -> Optional[str]:
    user = get_user_by_id_mysql(user_id)
    if not user:
        return None
    openid = str(user.get('openid') or '').strip()
    return openid or None


def get_user_id_by_openid_mysql(openid: Any) -> Optional[int]:
    openid_value = str(openid or '').strip()
    if not openid_value:
        return None

    user = get_user_by_openid_mysql(openid_value)
    if not user:
        return None

    return _to_int_or_none(user.get('id'))


def _normalize_tongue_reminder_status(
    *,
    user_id: Optional[int],
    openid: Optional[str],
    row: Optional[tuple[Any, ...]],
) -> dict[str, Any]:
    template_id = str(config.get('tongueReminderTemplateId') or '').strip()
    reminder_time = '08:00'
    reminder_interval_days = 1
    enabled = False
    last_sent_date = None
    next_send_at = None
    last_sent_at = None
    configured = False

    if row:
        configured = True
        reminder_time = str(row[4] or '08:00').strip() or '08:00'
        reminder_interval_days = int(row[5]) if row[5] else 1
        enabled = bool(row[6])
        last_sent_date = str(row[7]) if row[7] else None
        next_send_at = str(row[8]) if row[8] else None
        last_sent_at = str(row[9]) if row[9] else None
        template_id = str(row[3] or template_id).strip() or template_id
    elif openid:
        resolved_user_id = get_user_id_by_openid_mysql(openid)
        if resolved_user_id:
            user_id = resolved_user_id

    return {
        'scene': 'tongue_reminder',
        'configured': configured,
        'userId': user_id,
        'openid': openid,
        'templateId': template_id,
        'enabled': enabled,
        'intervalDays': reminder_interval_days,
        'reminderIntervalDays': reminder_interval_days,
        'remindTime': reminder_time,
        'reminderTime': reminder_time,
        'lastSentDate': last_sent_date,
        'lastSentAt': last_sent_at,
        'nextRemindAt': next_send_at,
        'nextSendAt': next_send_at,
    }


def get_tongue_reminder_status_mysql(user_id: Any) -> dict[str, Any]:
    user_id_int = _to_int_or_none(user_id)
    if user_id_int is None:
        raise ValueError('userId 不能为空')

    with get_mysql_connection() as connection:
        with get_mysql_cursor(connection) as cursor:
            _ensure_user_subscribe_reminder_table_mysql(cursor)
            _ensure_user_subscribe_reminder_columns_mysql(cursor)

            cursor.execute(
                '''
                SELECT user_id, openid, reminder_type, template_id, reminder_time,
                       reminder_interval_days, enabled, last_sent_date,
                       next_send_at, last_sent_at, created_at, updated_at
                FROM user_subscribe_reminder
                WHERE user_id = %s AND reminder_type = %s
                LIMIT 1
                ''',
                (user_id_int, 'tongue')
            )
            row = cursor.fetchone()
            openid = get_user_openid_by_user_id_mysql(user_id_int)
            return _normalize_tongue_reminder_status(user_id=user_id_int, openid=openid, row=row)


def get_tongue_reminder_status_mysql_by_openid(openid: Any) -> dict[str, Any]:
    openid_value = str(openid or '').strip()
    if not openid_value:
        raise ValueError('openid 不能为空')

    with get_mysql_connection() as connection:
        with get_mysql_cursor(connection) as cursor:
            _ensure_user_subscribe_reminder_table_mysql(cursor)
            _ensure_user_subscribe_reminder_columns_mysql(cursor)

            cursor.execute(
                '''
                SELECT user_id, openid, reminder_type, template_id, reminder_time,
                       reminder_interval_days, enabled, last_sent_date,
                       next_send_at, last_sent_at, created_at, updated_at
                FROM user_subscribe_reminder
                WHERE openid = %s AND reminder_type = %s
                LIMIT 1
                ''',
                (openid_value, 'tongue')
            )
            row = cursor.fetchone()
            user_id = get_user_id_by_openid_mysql(openid_value)
            return _normalize_tongue_reminder_status(user_id=user_id, openid=openid_value, row=row)


def upsert_tongue_reminder_mysql(

    *,
    user_id: Any,
    reminder_time: str = '08:00',
    reminder_interval_days: int = 1,
    enabled: bool = True
) -> dict[str, Any]:
    user_id_int = _to_int_or_none(user_id)
    if user_id_int is None:
        raise ValueError('userId 必须是有效的整数')

    openid = get_user_openid_by_user_id_mysql(user_id_int)
    if not openid:
        raise ValueError('未找到用户对应的 openid')

    template_id = str(config.get('tongueReminderTemplateId') or '').strip()
    if not template_id:
        raise ValueError('tongueReminderTemplateId 尚未配置')

    reminder_time_value = validate_reminder_time(reminder_time)
    interval_days_value = validate_reminder_interval_days(reminder_interval_days)
    enabled_value = 1 if enabled else 0

    next_send_at_value = None
    if enabled:
        next_send_at_value = calculate_next_send_at(reminder_time_value, interval_days_value)

    with get_mysql_connection() as connection:
        with get_mysql_cursor(connection) as cursor:
            _ensure_user_subscribe_reminder_table_mysql(cursor)
            _ensure_user_subscribe_reminder_columns_mysql(cursor)

            cursor.execute(
                '''
                INSERT INTO user_subscribe_reminder (
                    user_id, openid, reminder_type, template_id, reminder_time,
                    reminder_interval_days, enabled, last_sent_date,
                    next_send_at, last_sent_at, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, NULL, %s, NULL, NOW(), NOW())
                ON DUPLICATE KEY UPDATE
                    openid = VALUES(openid),
                    template_id = VALUES(template_id),
                    reminder_time = VALUES(reminder_time),
                    reminder_interval_days = VALUES(reminder_interval_days),
                    enabled = VALUES(enabled),
                    next_send_at = IF(VALUES(enabled) = 1, VALUES(next_send_at), next_send_at),
                    updated_at = VALUES(updated_at)
                ''',
                (
                    user_id_int,
                    openid,
                    'tongue',
                    template_id,
                    reminder_time_value,
                    interval_days_value,
                    enabled_value,
                    next_send_at_value,
                )
            )
            connection.commit()

    return get_tongue_reminder_status_mysql(user_id_int)


def upsert_tongue_reminder(
    *,
    user_id: Any,
    reminder_time: str = '08:00',
    reminder_interval_days: int = 1,
    enabled: bool = True
) -> dict[str, Any]:
    return upsert_tongue_reminder_mysql(
        user_id=user_id,
        reminder_time=reminder_time,
        reminder_interval_days=reminder_interval_days,
        enabled=enabled,
    )


def disable_tongue_reminder_mysql(*, user_id: Any) -> dict[str, Any]:
    user_id_int = _to_int_or_none(user_id)
    if user_id_int is None:
        raise ValueError('userId 必须是有效的整数')

    with get_mysql_connection() as connection:
        with get_mysql_cursor(connection) as cursor:
            _ensure_user_subscribe_reminder_table_mysql(cursor)
            _ensure_user_subscribe_reminder_columns_mysql(cursor)

            cursor.execute(
                '''
                UPDATE user_subscribe_reminder
                SET enabled = 0,
                    updated_at = NOW()
                WHERE user_id = %s
                  AND reminder_type = 'tongue'
                ''',
                (user_id_int,)
            )
            connection.commit()

            if cursor.rowcount == 0:
                raise ValueError(f'未找到用户 {user_id} 的舌苔提醒配置')

    return {
        'userId': user_id_int,
        'enabled': False,
        'disabledAt': datetime.now(SHANGHAI_TZ).strftime('%Y-%m-%d %H:%M:%S')
    }


def save_tongue_reminder_config_mysql(
    *,
    user_id: Any,
    reminder_time: Optional[str] = None,
    reminder_interval_days: Optional[int] = None
) -> dict[str, Any]:
    user_id_int = _to_int_or_none(user_id)
    if user_id_int is None:
        raise ValueError('userId 不能为空')

    openid = get_user_openid_by_user_id_mysql(user_id_int)
    if not openid:
        raise ValueError('未找到用户openid，请重新登录')

    template_id = str(config.get('tongueReminderTemplateId') or '').strip()
    if not template_id:
        raise ValueError('tongueReminderTemplateId 未配置')

    reminder_time_value = validate_reminder_time(reminder_time) if reminder_time is not None else None
    reminder_interval_days_value = (
        validate_reminder_interval_days(reminder_interval_days)
        if reminder_interval_days is not None
        else None
    )

    if reminder_time_value is None and reminder_interval_days_value is None:
        raise ValueError('请先保存提醒配置，至少传入 reminderTime 或 intervalDays')

    with get_mysql_connection() as connection:
        with get_mysql_cursor(connection) as cursor:
            _ensure_user_subscribe_reminder_table_mysql(cursor)
            _ensure_user_subscribe_reminder_columns_mysql(cursor)

            cursor.execute(
                '''
                SELECT reminder_time, reminder_interval_days, enabled
                FROM user_subscribe_reminder
                WHERE user_id = %s
                  AND reminder_type = 'tongue'
                LIMIT 1
                ''',
                (user_id_int,)
            )
            existing_row = cursor.fetchone()

            saved_time = (
                reminder_time_value
                if reminder_time_value is not None
                else (str(existing_row[0]).strip() if existing_row and existing_row[0] else '08:00')
            )
            saved_interval = (
                reminder_interval_days_value
                if reminder_interval_days_value is not None
                else (int(existing_row[1]) if existing_row and existing_row[1] else 1)
            )
            is_enabled = bool(existing_row[2]) if existing_row and len(existing_row) > 2 else False

            if existing_row:
                update_fields = [
                    'openid = %s',
                    'template_id = %s',
                    'reminder_time = %s',
                    'reminder_interval_days = %s',
                    'updated_at = NOW()',
                ]
                params = [
                    openid,
                    template_id,
                    saved_time,
                    saved_interval,
                ]

                if is_enabled:
                    update_fields.insert(4, 'next_send_at = %s')
                    params.append(calculate_next_send_at(saved_time, saved_interval))
                else:
                    update_fields.insert(4, 'next_send_at = NULL')

                params.append(user_id_int)
                cursor.execute(
                    f'''
                    UPDATE user_subscribe_reminder
                    SET {', '.join(update_fields)}
                    WHERE user_id = %s
                      AND reminder_type = 'tongue'
                    ''',
                    tuple(params)
                )
            else:
                cursor.execute(
                    '''
                    INSERT INTO user_subscribe_reminder (
                        user_id, openid, reminder_type, template_id, reminder_time,
                        reminder_interval_days, enabled, last_sent_date,
                        next_send_at, last_sent_at, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, 0, NULL, NULL, NULL, NOW(), NOW())
                    ''',
                    (
                        user_id_int,
                        openid,
                        'tongue',
                        template_id,
                        saved_time,
                        saved_interval,
                    )
                )
            connection.commit()

    return {
        'userId': user_id_int,
        'reminderTime': saved_time,
        'intervalDays': saved_interval,
        'enabled': is_enabled,
        'savedAt': datetime.now(SHANGHAI_TZ).strftime('%Y-%m-%d %H:%M:%S')
    }


def list_due_tongue_reminders_mysql(*, target_time: Optional[datetime] = None) -> list[dict[str, Any]]:

    now = target_time or datetime.now(SHANGHAI_TZ)
    now_str = now.strftime('%Y-%m-%d %H:%M:%S')

    with get_mysql_connection() as connection:
        with get_mysql_cursor(connection) as cursor:
            _ensure_user_subscribe_reminder_table_mysql(cursor)
            _ensure_user_subscribe_reminder_columns_mysql(cursor)

            cursor.execute(
                '''
                SELECT user_id, openid, reminder_time, template_id,
                       last_sent_date, next_send_at, last_sent_at,
                       reminder_interval_days
                FROM user_subscribe_reminder
                WHERE reminder_type = %s
                  AND enabled = 1
                  AND (next_send_at IS NULL OR next_send_at <= %s)
                ORDER BY
                    (next_send_at IS NULL) ASC,
                    next_send_at ASC,
                    user_id ASC
                ''',
                ('tongue', now_str)
            )
            rows = cursor.fetchall() or []

    return [
        {
            'userId': row[0],
            'openid': row[1],
            'reminderTime': row[2] or '08:00',
            'templateId': row[3],
            'lastSentDate': str(row[4]) if row[4] else None,
            'nextSendAt': str(row[5]) if row[5] else None,
            'lastSentAt': str(row[6]) if row[6] else None,
            'reminderIntervalDays': int(row[7]) if row[7] else 1,
        }
        for row in rows
        if row and str(row[1] or '').strip()
    ]


def mark_tongue_reminder_sent_mysql(*, user_id: Any, sent_time: Optional[datetime] = None) -> None:
    user_id_int = _to_int_or_none(user_id)
    if user_id_int is None:
        raise ValueError('userId 必须是有效的整数')

    sent_time_value = sent_time or datetime.now(SHANGHAI_TZ)
    sent_date_str = sent_time_value.strftime('%Y-%m-%d')
    sent_at_str = sent_time_value.strftime('%Y-%m-%d %H:%M:%S')

    with get_mysql_connection() as connection:
        with get_mysql_cursor(connection) as cursor:
            _ensure_user_subscribe_reminder_table_mysql(cursor)
            _ensure_user_subscribe_reminder_columns_mysql(cursor)

            cursor.execute(
                '''
                UPDATE user_subscribe_reminder
                SET last_sent_date = %s,
                    last_sent_at = %s,
                    next_send_at = %s,
                    updated_at = NOW()
                WHERE user_id = %s AND reminder_type = %s AND enabled = 1
                ''',
                (
                    sent_date_str,
                    sent_at_str,
                    calculate_next_send_at_for_user(user_id_int),
                    user_id_int,
                    'tongue'
                )
            )
            connection.commit()


def calculate_next_send_at_for_user(user_id: int) -> Optional[str]:
    """
    为指定用户计算下次发送时间

    根据用户当前的配置（reminder_time 和 reminder_interval_days）计算

    Args:
        user_id: 用户ID

    Returns:
        下次发送时间字符串，或 None（如果查询失败）
    """
    try:
        with get_mysql_connection() as connection:
            with get_mysql_cursor(connection) as cursor:
                cursor.execute(
                    '''
                    SELECT reminder_time, reminder_interval_days
                    FROM user_subscribe_reminder
                    WHERE user_id = %s AND reminder_type = %s
                    LIMIT 1
                    ''',
                    (user_id, 'tongue')
                )
                row = cursor.fetchone()
                if row:
                    return calculate_next_send_at(row[0] or '08:00', row[1] or 1)
    except Exception as exc:
        print(f'[reminder-storage] 计算下次发送时间失败: {exc}')
    return None
