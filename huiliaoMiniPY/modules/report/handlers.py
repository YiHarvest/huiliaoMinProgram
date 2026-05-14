#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查报告接口处理模块
遵循 AGENTS.md 规范，处理 HTTP 请求并调用 service 层
"""
import json
from http.server import BaseHTTPRequestHandler
from typing import Dict, Any, Optional
from urllib.parse import parse_qs, urlparse

from modules.report.service import ReportService, ReportServiceError


class ReportHandlers:
    """检查报告接口处理器"""
    
    @staticmethod
    def handle_create_report(handler: BaseHTTPRequestHandler, post_data: bytes = None) -> None:
        """
        处理创建报告请求
        POST /api/report/create
        """
        try:
            # 解析请求体
            if post_data:
                data = json.loads(post_data.decode('utf-8'))
            else:
                data = {}
            
            user_id = data.get('userId')
            doctor_id = data.get('doctorId')
            doctor_name = data.get('doctorName')
            doctor_department = data.get('doctorDepartment')
            report_type = data.get('reportType')
            remark = data.get('remark')
            
            # 调用服务层
            result = ReportService.create_report(
                user_id=user_id,
                doctor_id=doctor_id,
                doctor_name=doctor_name,
                doctor_department=doctor_department,
                report_type=report_type,
                remark=remark
            )
            
            ReportHandlers._send_json_response(handler, 200, {
                "success": True,
                "data": result
            })
            
        except ReportServiceError as e:
            ReportHandlers._send_json_response(handler, 400, {
                "success": False,
                "error": str(e)
            })
        except Exception as e:
            ReportHandlers._send_json_response(handler, 500, {
                "success": False,
                "error": f"服务器错误: {str(e)}"
            })
    
    @staticmethod
    def handle_upload_file(handler: BaseHTTPRequestHandler, post_data: bytes = None, 
                          content_type: str = None) -> None:
        """
        处理文件上传请求
        POST /api/report/file/upload
        支持 multipart/form-data 格式
        """
        try:
            # 解析 multipart/form-data
            if not content_type or 'multipart/form-data' not in content_type:
                ReportHandlers._send_json_response(handler, 400, {
                    "success": False,
                    "error": "Content-Type 必须是 multipart/form-data"
                })
                return
            
            # 解析表单数据
            form_data = ReportHandlers._parse_multipart_form(post_data, content_type)
            
            report_id = form_data.get('reportId')
            user_id = form_data.get('userId')
            sort_order = int(form_data.get('sortOrder', 0))
            file_info = form_data.get('file')
            
            if not file_info:
                ReportHandlers._send_json_response(handler, 400, {
                    "success": False,
                    "error": "缺少文件"
                })
                return
            
            # 调用服务层
            result = ReportService.upload_file(
                report_id=int(report_id) if report_id else 0,
                user_id=int(user_id) if user_id else 0,
                file_data=file_info['data'],
                original_name=file_info['filename'],
                mime_type=file_info['content_type'],
                sort_order=sort_order
            )
            
            ReportHandlers._send_json_response(handler, 200, {
                "success": True,
                "data": result
            })
            
        except ReportServiceError as e:
            ReportHandlers._send_json_response(handler, 400, {
                "success": False,
                "error": str(e)
            })
        except Exception as e:
            ReportHandlers._send_json_response(handler, 500, {
                "success": False,
                "error": f"服务器错误: {str(e)}"
            })
    
    @staticmethod
    def handle_complete_report(handler: BaseHTTPRequestHandler, post_data: bytes = None) -> None:
        """
        处理完成报告请求
        POST /api/report/complete
        """
        try:
            if post_data:
                data = json.loads(post_data.decode('utf-8'))
            else:
                data = {}
            
            report_id = data.get('reportId')
            user_id = data.get('userId')
            
            result = ReportService.complete_report(
                report_id=int(report_id) if report_id else 0,
                user_id=int(user_id) if user_id else 0
            )
            
            ReportHandlers._send_json_response(handler, 200, {
                "success": True,
                "data": result
            })
            
        except ReportServiceError as e:
            ReportHandlers._send_json_response(handler, 400, {
                "success": False,
                "error": str(e)
            })
        except Exception as e:
            ReportHandlers._send_json_response(handler, 500, {
                "success": False,
                "error": f"服务器错误: {str(e)}"
            })
    
    @staticmethod
    def handle_list_reports(handler: BaseHTTPRequestHandler, query_params: Dict[str, Any] = None) -> None:
        """
        处理获取报告列表请求
        GET /api/report/list?userId=xxx&limit=20&offset=0
        """
        try:
            user_id = query_params.get('userId', [None])[0] if query_params else None
            limit = int(query_params.get('limit', ['20'])[0]) if query_params else 20
            offset = int(query_params.get('offset', ['0'])[0]) if query_params else 0
            
            result = ReportService.get_report_list(
                user_id=int(user_id) if user_id else 0,
                limit=limit,
                offset=offset
            )
            
            ReportHandlers._send_json_response(handler, 200, {
                "success": True,
                "data": result
            })
            
        except ReportServiceError as e:
            ReportHandlers._send_json_response(handler, 400, {
                "success": False,
                "error": str(e)
            })
        except Exception as e:
            ReportHandlers._send_json_response(handler, 500, {
                "success": False,
                "error": f"服务器错误: {str(e)}"
            })
    
    @staticmethod
    def handle_get_report_detail(handler: BaseHTTPRequestHandler, query_params: Dict[str, Any] = None) -> None:
        """
        处理获取报告详情请求
        GET /api/report/detail?reportId=xxx&userId=xxx
        """
        try:
            report_id = query_params.get('reportId', [None])[0] if query_params else None
            user_id = query_params.get('userId', [None])[0] if query_params else None
            
            result = ReportService.get_report_detail(
                report_id=int(report_id) if report_id else 0,
                user_id=int(user_id) if user_id else 0
            )
            
            ReportHandlers._send_json_response(handler, 200, {
                "success": True,
                "data": result
            })
            
        except ReportServiceError as e:
            ReportHandlers._send_json_response(handler, 400, {
                "success": False,
                "error": str(e)
            })
        except Exception as e:
            ReportHandlers._send_json_response(handler, 500, {
                "success": False,
                "error": f"服务器错误: {str(e)}"
            })
    
    @staticmethod
    def handle_delete_report(handler: BaseHTTPRequestHandler, post_data: bytes = None) -> None:
        """
        处理删除报告请求
        POST /api/report/delete
        """
        try:
            if post_data:
                data = json.loads(post_data.decode('utf-8'))
            else:
                data = {}
            
            report_id = data.get('reportId')
            user_id = data.get('userId')
            
            result = ReportService.delete_report(
                report_id=int(report_id) if report_id else 0,
                user_id=int(user_id) if user_id else 0
            )
            
            ReportHandlers._send_json_response(handler, 200, {
                "success": True,
                "data": result
            })
            
        except ReportServiceError as e:
            ReportHandlers._send_json_response(handler, 400, {
                "success": False,
                "error": str(e)
            })
        except Exception as e:
            ReportHandlers._send_json_response(handler, 500, {
                "success": False,
                "error": f"服务器错误: {str(e)}"
            })
    
    @staticmethod
    def _send_json_response(handler: BaseHTTPRequestHandler, status_code: int, data: Dict[str, Any]) -> None:
        """发送 JSON 响应"""
        handler.send_response(status_code)
        handler.send_header('Content-Type', 'application/json; charset=utf-8')
        handler.send_header('Access-Control-Allow-Origin', '*')
        handler.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        handler.send_header('Access-Control-Allow-Headers', 'Content-Type')
        handler.end_headers()
        handler.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    @staticmethod
    def _parse_multipart_form(post_data: bytes, content_type: str) -> Dict[str, Any]:
        """
        解析 multipart/form-data 数据
        简化版实现，适用于小程序上传场景
        """
        result = {}
        
        # 提取 boundary
        boundary = None
        for part in content_type.split(';'):
            if 'boundary=' in part:
                boundary = part.split('boundary=')[1].strip().strip('"')
                break
        
        if not boundary:
            return result
        
        boundary_bytes = f'--{boundary}'.encode('utf-8')
        parts = post_data.split(boundary_bytes)
        
        for part in parts:
            if not part or part == b'--\r\n' or part == b'--':
                continue
            
            # 分离 header 和 body
            if b'\r\n\r\n' in part:
                header_bytes, body = part.split(b'\r\n\r\n', 1)
                header = header_bytes.decode('utf-8', errors='ignore')
                
                # 移除末尾的 \r\n
                if body.endswith(b'\r\n'):
                    body = body[:-2]
                
                # 解析 Content-Disposition
                if 'Content-Disposition:' in header:
                    # 提取 name
                    name = None
                    filename = None
                    content_type_part = None
                    
                    for line in header.split('\r\n'):
                        if 'Content-Disposition:' in line:
                            # 提取 name
                            if 'name="' in line:
                                name_start = line.find('name="') + 6
                                name_end = line.find('"', name_start)
                                name = line[name_start:name_end]
                            
                            # 提取 filename
                            if 'filename="' in line:
                                filename_start = line.find('filename="') + 10
                                filename_end = line.find('"', filename_start)
                                filename = line[filename_start:filename_end]
                        
                        if 'Content-Type:' in line:
                            content_type_part = line.split('Content-Type:')[1].strip()
                    
                    if name:
                        if filename:
                            # 文件字段
                            result[name] = {
                                'filename': filename,
                                'content_type': content_type_part or 'application/octet-stream',
                                'data': body
                            }
                        else:
                            # 普通字段
                            result[name] = body.decode('utf-8', errors='ignore')
        
        return result
