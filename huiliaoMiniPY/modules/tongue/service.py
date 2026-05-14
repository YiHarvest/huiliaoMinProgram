#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
舌苔记录业务层
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from database.tongue_repository import (
    count_tongue_reports,
    get_tongue_report,
    list_tongue_reports,
    save_tongue_report,
)


BEIJING_TZ = timezone(timedelta(hours=8))


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


def _format_beijing_dt(value: Any) -> str:
    dt = _to_beijing_datetime(value)
    if dt is None:
        return ''
    return dt.strftime('%Y-%m-%d %H:%M:%S')


class TongueServiceError(Exception):
    pass


class TongueService:
    @staticmethod
    def save_analysis_report(
        *,
        analysis_id: str,
        user_id: int,
        openid: Optional[str],
        report: Dict[str, Any],
        tips: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not analysis_id:
            raise TongueServiceError('analysisId 不能为空')
        if not user_id:
            raise TongueServiceError('userId 不能为空')

        save_tongue_report(
            analysis_id=analysis_id,
            user_id=user_id,
            openid=openid,
            report=report,
            tips=tips,
        )

        record = get_tongue_report(analysis_id, user_id)
        if not record:
            raise TongueServiceError('舌苔报告保存失败')

        return TongueService._format_detail(record)

    @staticmethod
    def list_reports(user_id: int, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        if not user_id:
            raise TongueServiceError('userId 不能为空')

        reports = list_tongue_reports(user_id, limit, offset)
        total = count_tongue_reports(user_id)

        return {
            'list': [TongueService._format_list_item(report) for report in reports],
            'total': total,
            'limit': limit,
            'offset': offset,
        }

    @staticmethod
    def get_report_detail(analysis_id: str, user_id: int) -> Dict[str, Any]:
        if not analysis_id:
            raise TongueServiceError('analysisId 不能为空')
        if not user_id:
            raise TongueServiceError('userId 不能为空')

        record = get_tongue_report(analysis_id, user_id)
        if not record:
            raise TongueServiceError('舌苔报告不存在或无权访问')

        return TongueService._format_detail(record)

    @staticmethod
    def _format_list_item(record: Dict[str, Any]) -> Dict[str, Any]:
        report = record.get('report') or {}
        overall = report.get('overall') or {}
        title = record.get('subject') or overall.get('subject') or '舌苔分析记录'
        summary = record.get('summary') or overall.get('summary') or ''
        return {
            'analysisId': record.get('analysis_id'),
            'userId': record.get('user_id'),
            'title': title,
            'summary': summary,
            'status': record.get('status') or 'completed',
            'createdAt': record.get('created_at') if isinstance(record.get('created_at'), str) else str(record.get('created_at') or ''),
            'updatedAt': record.get('updated_at') if isinstance(record.get('updated_at'), str) else str(record.get('updated_at') or ''),
        }

    @staticmethod
    def _format_detail(record: Dict[str, Any]) -> Dict[str, Any]:
        report = record.get('report') or {}
        overall = report.get('overall') or {}
        return {
            'analysisId': record.get('analysis_id'),
            'userId': record.get('user_id'),
            'openid': record.get('openid') or '',
            'status': record.get('status') or 'completed',
            'subject': record.get('subject') or overall.get('subject') or '',
            'summary': record.get('summary') or overall.get('summary') or '',
            'tips': record.get('tips') or '',
            'createdAt': record.get('created_at') if isinstance(record.get('created_at'), str) else str(record.get('created_at') or ''),
            'updatedAt': record.get('updated_at') if isinstance(record.get('updated_at'), str) else str(record.get('updated_at') or ''),
            'report': report,
        }
