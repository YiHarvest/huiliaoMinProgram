#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
舌苔记录接口处理器
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler
from typing import Any, Dict

from modules.tongue.service import TongueService, TongueServiceError


class TongueHandlers:
    @staticmethod
    def handle_list_tongue_reports(handler: BaseHTTPRequestHandler, query_params: Dict[str, Any] = None) -> None:
        try:
            user_id = query_params.get('userId', [None])[0] if query_params else None
            limit = int(query_params.get('limit', ['20'])[0]) if query_params else 20
            offset = int(query_params.get('offset', ['0'])[0]) if query_params else 0

            result = TongueService.list_reports(
                user_id=int(user_id) if user_id else 0,
                limit=limit,
                offset=offset,
            )
            TongueHandlers._send_json_response(handler, 200, {'success': True, 'data': result})
        except TongueServiceError as exc:
            TongueHandlers._send_json_response(handler, 400, {'success': False, 'error': str(exc)})
        except Exception as exc:
            TongueHandlers._send_json_response(handler, 500, {'success': False, 'error': f'服务器错误: {str(exc)}'})

    @staticmethod
    def handle_get_tongue_report_detail(handler: BaseHTTPRequestHandler, query_params: Dict[str, Any] = None) -> None:
        try:
            analysis_id = query_params.get('analysisId', [None])[0] if query_params else None
            user_id = query_params.get('userId', [None])[0] if query_params else None

            result = TongueService.get_report_detail(
                analysis_id=str(analysis_id or ''),
                user_id=int(user_id) if user_id else 0,
            )
            TongueHandlers._send_json_response(handler, 200, {'success': True, 'data': result})
        except TongueServiceError as exc:
            TongueHandlers._send_json_response(handler, 400, {'success': False, 'error': str(exc)})
        except Exception as exc:
            TongueHandlers._send_json_response(handler, 500, {'success': False, 'error': f'服务器错误: {str(exc)}'})

    @staticmethod
    def _send_json_response(handler: BaseHTTPRequestHandler, status_code: int, data: Dict[str, Any]) -> None:
        handler.send_response(status_code)
        handler.send_header('Content-Type', 'application/json; charset=utf-8')
        handler.send_header('Access-Control-Allow-Origin', '*')
        handler.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        handler.send_header('Access-Control-Allow-Headers', 'Content-Type')
        handler.end_headers()
        handler.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
