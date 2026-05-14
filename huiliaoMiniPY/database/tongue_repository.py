#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
舌苔记录数据库仓库
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from mysql_storage import get_mysql_connection


BEIJING_TZ = timezone(timedelta(hours=8))


def _now() -> datetime:
    return datetime.now(timezone.utc).astimezone(BEIJING_TZ)


def _to_beijing_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        if text.endswith('Z'):
            text = text[:-1] + '+00:00'
        try:
            value = datetime.fromisoformat(text)
        except ValueError:
            return None
    if not isinstance(value, datetime):
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(BEIJING_TZ)


def _format_dt(value: Any) -> Optional[str]:
    if value is None:
        return None
    dt = _to_beijing_datetime(value)
    if dt is not None:
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    return str(value)


def _ensure_schema(connection) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tongue_report_records (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                analysis_id VARCHAR(64) NOT NULL,
                user_id BIGINT NOT NULL,
                openid VARCHAR(64) NULL,
                status VARCHAR(32) NOT NULL DEFAULT 'completed',
                subject VARCHAR(255) NULL,
                summary TEXT NULL,
                report_json LONGTEXT NOT NULL,
                tips TEXT NULL,
                error_message TEXT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                deleted_at DATETIME NULL,
                UNIQUE KEY uk_tongue_analysis_id (analysis_id),
                KEY idx_tongue_user_status_deleted_created (user_id, status, deleted_at, created_at),
                KEY idx_tongue_openid (openid)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        )


def _row_to_dict(row: Dict[str, Any]) -> Dict[str, Any]:
    result = dict(row)
    report_json = result.get('report_json')
    if isinstance(report_json, str):
        try:
            result['report'] = json.loads(report_json)
        except json.JSONDecodeError:
            result['report'] = {}
    else:
        result['report'] = report_json or {}

    result.pop('report_json', None)
    result['created_at'] = _format_dt(result.get('created_at'))
    result['updated_at'] = _format_dt(result.get('updated_at'))
    result['deleted_at'] = _format_dt(result.get('deleted_at'))
    return result


def save_tongue_report(
    *,
    analysis_id: str,
    user_id: Optional[int],
    openid: Optional[str],
    report: Dict[str, Any],
    tips: Optional[str],
    status: str = 'completed',
    error_message: Optional[str] = None,
) -> None:
    if not analysis_id:
        raise ValueError('analysis_id 不能为空')
    if not user_id:
        raise ValueError('user_id 不能为空')

    subject = (
        (report.get('overall') or {}).get('subject')
        or report.get('subject')
        or ''
    )
    summary = (
        (report.get('overall') or {}).get('summary')
        or report.get('summary')
        or ''
    )

    with get_mysql_connection() as connection:
        _ensure_schema(connection)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO tongue_report_records (
                    analysis_id, user_id, openid, status, subject, summary,
                    report_json, tips, error_message, created_at, updated_at, deleted_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), NULL)
                ON DUPLICATE KEY UPDATE
                    user_id = VALUES(user_id),
                    openid = VALUES(openid),
                    status = VALUES(status),
                    subject = VALUES(subject),
                    summary = VALUES(summary),
                    report_json = VALUES(report_json),
                    tips = VALUES(tips),
                    error_message = VALUES(error_message),
                    updated_at = NOW(),
                    deleted_at = NULL
                """,
                (
                    analysis_id,
                    user_id,
                    openid,
                    status,
                    subject,
                    summary,
                    json.dumps(report, ensure_ascii=False),
                    tips,
                    error_message,
                ),
            )
        connection.commit()


def update_tongue_status(
    analysis_id: str,
    *,
    user_id: Optional[int] = None,
    status: str,
    error_message: Optional[str] = None,
) -> bool:
    if not analysis_id:
        return False

    with get_mysql_connection() as connection:
        _ensure_schema(connection)
        with connection.cursor() as cursor:
            if user_id:
                cursor.execute(
                    """
                    UPDATE tongue_report_records
                    SET status = %s, error_message = %s, updated_at = NOW()
                    WHERE analysis_id = %s AND user_id = %s AND deleted_at IS NULL
                    """,
                    (status, error_message, analysis_id, user_id),
                )
            else:
                cursor.execute(
                    """
                    UPDATE tongue_report_records
                    SET status = %s, error_message = %s, updated_at = NOW()
                    WHERE analysis_id = %s AND deleted_at IS NULL
                    """,
                    (status, error_message, analysis_id),
                )
            connection.commit()
            return cursor.rowcount > 0


def soft_delete_tongue_report(analysis_id: str, user_id: Optional[int] = None) -> bool:
    if not analysis_id:
        return False

    with get_mysql_connection() as connection:
        _ensure_schema(connection)
        with connection.cursor() as cursor:
            if user_id:
                cursor.execute(
                    """
                    UPDATE tongue_report_records
                    SET deleted_at = NOW(), updated_at = NOW(), status = 'deleted'
                    WHERE analysis_id = %s AND user_id = %s AND deleted_at IS NULL
                    """,
                    (analysis_id, user_id),
                )
            else:
                cursor.execute(
                    """
                    UPDATE tongue_report_records
                    SET deleted_at = NOW(), updated_at = NOW(), status = 'deleted'
                    WHERE analysis_id = %s AND deleted_at IS NULL
                    """,
                    (analysis_id,),
                )
            connection.commit()
            return cursor.rowcount > 0


def get_tongue_report(analysis_id: str, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    if not analysis_id:
        return None

    with get_mysql_connection() as connection:
        _ensure_schema(connection)
        with connection.cursor(dictionary=True) as cursor:
            if user_id:
                cursor.execute(
                    """
                    SELECT id, analysis_id, user_id, openid, status, subject, summary,
                           report_json, tips, error_message, created_at, updated_at, deleted_at
                    FROM tongue_report_records
                    WHERE analysis_id = %s AND user_id = %s AND deleted_at IS NULL
                    LIMIT 1
                    """,
                    (analysis_id, user_id),
                )
            else:
                cursor.execute(
                    """
                    SELECT id, analysis_id, user_id, openid, status, subject, summary,
                           report_json, tips, error_message, created_at, updated_at, deleted_at
                    FROM tongue_report_records
                    WHERE analysis_id = %s AND deleted_at IS NULL
                    LIMIT 1
                    """,
                    (analysis_id,),
                )
            row = cursor.fetchone()

    if not row:
        return None

    return _row_to_dict(row)


def list_tongue_reports(
    user_id: int,
    limit: int = 20,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    with get_mysql_connection() as connection:
        _ensure_schema(connection)
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute(
                """
                SELECT id, analysis_id, user_id, openid, status, subject, summary,
                       report_json, tips, error_message, created_at, updated_at, deleted_at
                FROM tongue_report_records
                WHERE user_id = %s
                  AND status = 'completed'
                  AND deleted_at IS NULL
                ORDER BY created_at DESC, id DESC
                LIMIT %s OFFSET %s
                """,
                (user_id, limit, offset),
            )
            rows = cursor.fetchall()

    return [_row_to_dict(row) for row in rows]


def count_tongue_reports(user_id: int) -> int:
    with get_mysql_connection() as connection:
        _ensure_schema(connection)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM tongue_report_records
                WHERE user_id = %s
                  AND status = 'completed'
                  AND deleted_at IS NULL
                """,
                (user_id,),
            )
            result = cursor.fetchone()

    if not result:
        return 0
    return int(result[0] if isinstance(result, tuple) else result.get('COUNT(*)', 0))
