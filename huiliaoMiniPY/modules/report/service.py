#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查报告业务逻辑模块
遵循 AGENTS.md 规范，处理检查报告业务逻辑
"""
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path

from database.report_repository import ReportRepository, ReportFileRepository

# 文件存储配置
BASE_DIR = Path(__file__).parent.parent.parent
REPORTS_DIR = BASE_DIR / 'uploads' / 'reports'
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_FILES_PER_REPORT = 9

# 确保目录存在
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

BEIJING_TZ = timezone(timedelta(hours=8))


def _beijing_now() -> datetime:
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


def _format_beijing_dt(value: Any) -> Optional[str]:
    dt = _to_beijing_datetime(value)
    if dt is None:
        return None
    return dt.strftime('%Y-%m-%d %H:%M:%S')


class ReportServiceError(Exception):
    """报告服务异常"""
    pass


class ReportService:
    """检查报告服务"""
    
    @staticmethod
    def create_report(user_id: int, doctor_id: Optional[str] = None,
                      doctor_name: Optional[str] = None,
                      doctor_department: Optional[str] = None,
                      report_type: Optional[str] = None,
                      remark: Optional[str] = None) -> Dict[str, Any]:
        """
        创建检查报告记录
        
        Args:
            user_id: 用户ID
            doctor_id: 医生ID
            doctor_name: 医生姓名
            doctor_department: 医生科室
            report_type: 报告类型
            remark: 备注
            
        Returns:
            包含 reportId 和创建信息的字典
        """
        if not user_id:
            raise ReportServiceError("用户ID不能为空")
        
        report_id = ReportRepository.create_report(
            user_id=user_id,
            doctor_id=doctor_id,
            doctor_name=doctor_name,
            doctor_department=doctor_department,
            report_type=report_type,
            remark=remark
        )
        
        return {
            "reportId": report_id,
            "userId": user_id,
            "status": "created",
            "createdAt": _format_beijing_dt(_beijing_now())
        }
    
    @staticmethod
    def upload_file(report_id: int, user_id: int, file_data: bytes,
                    original_name: str, mime_type: str,
                    sort_order: int = 0) -> Dict[str, Any]:
        """
        上传报告文件
        
        Args:
            report_id: 报告ID
            user_id: 用户ID
            file_data: 文件二进制数据
            original_name: 原始文件名
            mime_type: MIME类型
            sort_order: 排序顺序
            
        Returns:
            包含文件信息的字典
        """
        # 验证参数
        if not user_id:
            raise ReportServiceError("用户ID不能为空")
        
        if not report_id:
            raise ReportServiceError("报告ID不能为空")
        
        # 检查报告是否存在
        report = ReportRepository.get_report_by_id(report_id)
        if not report:
            raise ReportServiceError("报告不存在")
        
        if report['user_id'] != user_id:
            raise ReportServiceError("无权上传到此报告")
        
        # 检查文件数量限制
        current_count = ReportFileRepository.count_files_by_report(report_id)
        if current_count >= MAX_FILES_PER_REPORT:
            raise ReportServiceError(f"每个报告最多上传 {MAX_FILES_PER_REPORT} 张图片")
        
        # 验证文件大小
        file_size = len(file_data)
        if file_size > MAX_FILE_SIZE:
            raise ReportServiceError(f"文件大小超过限制（最大 {MAX_FILE_SIZE // 1024 // 1024}MB）")
        
        # 验证文件扩展名
        file_ext = Path(original_name).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise ReportServiceError(f"不支持的文件格式，仅支持: {', '.join(ALLOWED_EXTENSIONS)}")
        
        # 生成存储路径
        today = _beijing_now().strftime('%Y%m%d')
        file_uuid = str(uuid.uuid4())
        saved_filename = f"{file_uuid}{file_ext}"
        
        # 存储路径: uploads/reports/{user_id}/{yyyyMMdd}/{uuid}.{ext}
        user_dir = REPORTS_DIR / str(user_id)
        date_dir = user_dir / today
        date_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = date_dir / saved_filename
        
        # 保存文件
        try:
            with open(file_path, 'wb') as f:
                f.write(file_data)
        except Exception as e:
            raise ReportServiceError(f"文件保存失败: {str(e)}")
        
        # 生成访问URL
        file_url = f"https://miniprogram.huiliaoyiyuan.com/uploads/reports/{user_id}/{today}/{saved_filename}"
        
        # 保存到数据库
        file_id = ReportFileRepository.create_file(
            report_id=report_id,
            user_id=user_id,
            file_path=str(file_path.relative_to(BASE_DIR)),
            file_url=file_url,
            original_name=original_name,
            file_size=file_size,
            mime_type=mime_type,
            sort_order=sort_order
        )
        
        # 更新报告状态为 uploaded
        ReportRepository.update_report_status(report_id, 'uploaded')
        
        return {
            "fileId": file_id,
            "reportId": report_id,
            "fileUrl": file_url,
            "originalName": original_name,
            "fileSize": file_size,
            "sortOrder": sort_order
        }
    
    @staticmethod
    def complete_report(report_id: int, user_id: int) -> Dict[str, Any]:
        """
        完成报告上传
        
        Args:
            report_id: 报告ID
            user_id: 用户ID
            
        Returns:
            包含完成信息的字典
        """
        # 检查报告是否存在
        report = ReportRepository.get_report_by_id(report_id)
        if not report:
            raise ReportServiceError("报告不存在")
        
        if report['user_id'] != user_id:
            raise ReportServiceError("无权操作此报告")
        
        # 检查是否有文件
        file_count = ReportFileRepository.count_files_by_report(report_id)
        if file_count == 0:
            raise ReportServiceError("报告没有上传任何图片")
        
        # 更新状态为 completed
        success = ReportRepository.update_report_status(report_id, 'completed')
        if not success:
            raise ReportServiceError("更新报告状态失败")
        
        return {
            "reportId": report_id,
            "status": "completed",
            "fileCount": file_count,
            "completedAt": _format_beijing_dt(_beijing_now())
        }
    
    @staticmethod
    def get_report_list(user_id: int, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """
        获取用户报告列表
        
        Args:
            user_id: 用户ID
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            包含报告列表和总数的字典
        """
        if not user_id:
            raise ReportServiceError("用户ID不能为空")
        
        reports = ReportRepository.list_reports_by_user(user_id, limit, offset)
        total = ReportRepository.count_reports_by_user(user_id)
        
        # 格式化返回数据
        formatted_reports = []
        for report in reports:
            files = ReportFileRepository.get_files_by_report(report['id'])

            formatted_reports.append({
                "reportId": report['id'],
                "userId": report['user_id'],
                "doctorId": report['doctor_id'],
                "doctorName": report['doctor_name'],
                "doctorDepartment": report['doctor_department'],
                "reportType": report['report_type'],
                "status": report['status'],
                "remark": report['remark'],
                "createdAt": _format_beijing_dt(report['created_at']),
                "updatedAt": _format_beijing_dt(report['updated_at']),
                "fileCount": len(files),
                "firstFileName": files[0]['original_name'] if files else None,
                "firstFileUrl": files[0]['file_url'] if files else None
            })
        
        return {
            "list": formatted_reports,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    
    @staticmethod
    def get_report_detail(report_id: int, user_id: int) -> Dict[str, Any]:
        """
        获取报告详情
        
        Args:
            report_id: 报告ID
            user_id: 用户ID
            
        Returns:
            包含报告详情和文件列表的字典
        """
        # 检查报告是否存在
        report = ReportRepository.get_report_by_id(report_id)
        if not report:
            raise ReportServiceError("报告不存在")
        
        if report['user_id'] != user_id:
            raise ReportServiceError("无权查看此报告")
        
        # 获取文件列表
        files = ReportFileRepository.get_files_by_report(report_id)
        formatted_files = []
        for file in files:
            formatted_files.append({
                "fileId": file['id'],
                "fileUrl": file['file_url'],
                "originalName": file['original_name'],
                "fileSize": file['file_size'],
                "mimeType": file['mime_type'],
                "sortOrder": file['sort_order'],
                "createdAt": _format_beijing_dt(file['created_at'])
            })
        
        return {
            "reportId": report['id'],
            "userId": report['user_id'],
            "doctorId": report['doctor_id'],
            "doctorName": report['doctor_name'],
            "doctorDepartment": report['doctor_department'],
            "reportType": report['report_type'],
            "status": report['status'],
            "remark": report['remark'],
            "createdAt": _format_beijing_dt(report['created_at']),
            "updatedAt": _format_beijing_dt(report['updated_at']),
            "files": formatted_files
        }
    
    @staticmethod
    def delete_report(report_id: int, user_id: int) -> Dict[str, Any]:
        """
        软删除报告
        
        Args:
            report_id: 报告ID
            user_id: 用户ID
            
        Returns:
            包含删除结果的字典
        """
        # 检查报告是否存在
        report = ReportRepository.get_report_by_id(report_id)
        if not report:
            raise ReportServiceError("报告不存在")
        
        if report['user_id'] != user_id:
            raise ReportServiceError("无权删除此报告")
        
        # 软删除报告
        success = ReportRepository.soft_delete_report(report_id)
        if not success:
            raise ReportServiceError("删除报告失败")
        
        return {
            "reportId": report_id,
            "deleted": True,
            "deletedAt": _format_beijing_dt(_beijing_now())
        }
