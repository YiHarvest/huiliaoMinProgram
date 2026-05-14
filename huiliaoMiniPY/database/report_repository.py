#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查报告数据库操作模块
遵循 AGENTS.md 规范，所有检查报告数据库操作集中在此
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
import mysql.connector
from mysql_storage import get_mysql_connection


class ReportRepository:
    """检查报告数据仓库"""
    
    @staticmethod
    def create_report(user_id: int, doctor_id: Optional[str] = None,
                      doctor_name: Optional[str] = None,
                      doctor_department: Optional[str] = None,
                      report_type: Optional[str] = None,
                      remark: Optional[str] = None) -> int:
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
            新创建的报告ID
        """
        with get_mysql_connection() as connection:
            with connection.cursor() as cursor:
                sql = """
                    INSERT INTO checkup_reports 
                    (user_id, doctor_id, doctor_name, doctor_department, report_type, status, remark)
                    VALUES (%s, %s, %s, %s, %s, 'created', %s)
                """
                cursor.execute(sql, (user_id, doctor_id, doctor_name, 
                                   doctor_department, report_type, remark))
                connection.commit()
                return cursor.lastrowid
    
    @staticmethod
    def get_report_by_id(report_id: int, include_deleted: bool = False) -> Optional[Dict[str, Any]]:
        """
        根据ID获取报告详情
        
        Args:
            report_id: 报告ID
            include_deleted: 是否包含已删除的记录
            
        Returns:
            报告详情字典，不存在返回None
        """
        with get_mysql_connection() as connection:
            with connection.cursor(dictionary=True) as cursor:
                if include_deleted:
                    sql = "SELECT * FROM checkup_reports WHERE id = %s"
                    cursor.execute(sql, (report_id,))
                else:
                    sql = "SELECT * FROM checkup_reports WHERE id = %s AND deleted_at IS NULL"
                    cursor.execute(sql, (report_id,))
                return cursor.fetchone()
    
    @staticmethod
    def update_report_status(report_id: int, status: str) -> bool:
        """
        更新报告状态
        
        Args:
            report_id: 报告ID
            status: 新状态 (created/uploaded/completed)
            
        Returns:
            是否更新成功
        """
        with get_mysql_connection() as connection:
            with connection.cursor() as cursor:
                sql = """
                    UPDATE checkup_reports 
                    SET status = %s, updated_at = NOW()
                    WHERE id = %s AND deleted_at IS NULL
                """
                cursor.execute(sql, (status, report_id))
                connection.commit()
                return cursor.rowcount > 0
    
    @staticmethod
    def soft_delete_report(report_id: int) -> bool:
        """
        软删除报告
        
        Args:
            report_id: 报告ID
            
        Returns:
            是否删除成功
        """
        with get_mysql_connection() as connection:
            with connection.cursor() as cursor:
                sql = """
                    UPDATE checkup_reports 
                    SET deleted_at = NOW(), updated_at = NOW()
                    WHERE id = %s AND deleted_at IS NULL
                """
                cursor.execute(sql, (report_id,))
                connection.commit()
                return cursor.rowcount > 0
    
    @staticmethod
    def list_reports_by_user(user_id: int, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """
        获取用户的报告列表
        
        Args:
            user_id: 用户ID
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            报告列表
        """
        with get_mysql_connection() as connection:
            with connection.cursor(dictionary=True) as cursor:
                sql = """
                    SELECT id, user_id, doctor_id, doctor_name, doctor_department,
                           report_type, status, remark, created_at, updated_at
                    FROM checkup_reports
                    WHERE user_id = %s
                      AND status = 'completed'
                      AND deleted_at IS NULL
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """
                cursor.execute(sql, (user_id, limit, offset))
                return cursor.fetchall()
    
    @staticmethod
    def count_reports_by_user(user_id: int) -> int:
        """
        获取用户的报告总数
        
        Args:
            user_id: 用户ID
            
        Returns:
            报告数量
        """
        with get_mysql_connection() as connection:
            with connection.cursor() as cursor:
                sql = """
                    SELECT COUNT(*) FROM checkup_reports
                    WHERE user_id = %s
                      AND status = 'completed'
                      AND deleted_at IS NULL
                """
                cursor.execute(sql, (user_id,))
                result = cursor.fetchone()
                return result[0] if result else 0


class ReportFileRepository:
    """检查报告文件数据仓库"""
    
    @staticmethod
    def create_file(report_id: int, user_id: int, file_path: str, file_url: str,
                    original_name: Optional[str] = None, file_size: Optional[int] = None,
                    mime_type: Optional[str] = None, sort_order: int = 0) -> int:
        """
        创建报告文件记录
        
        Args:
            report_id: 报告ID
            user_id: 用户ID
            file_path: 文件存储路径
            file_url: 文件访问URL
            original_name: 原始文件名
            file_size: 文件大小
            mime_type: MIME类型
            sort_order: 排序顺序
            
        Returns:
            新创建的文件ID
        """
        with get_mysql_connection() as connection:
            with connection.cursor() as cursor:
                sql = """
                    INSERT INTO checkup_report_files 
                    (report_id, user_id, file_path, file_url, original_name, 
                     file_size, mime_type, sort_order)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (report_id, user_id, file_path, file_url,
                                   original_name, file_size, mime_type, sort_order))
                connection.commit()
                return cursor.lastrowid
    
    @staticmethod
    def get_files_by_report(report_id: int) -> List[Dict[str, Any]]:
        """
        获取报告的所有文件
        
        Args:
            report_id: 报告ID
            
        Returns:
            文件列表
        """
        with get_mysql_connection() as connection:
            with connection.cursor(dictionary=True) as cursor:
                sql = """
                    SELECT id, report_id, file_path, file_url, original_name,
                           file_size, mime_type, sort_order, created_at
                    FROM checkup_report_files
                    WHERE report_id = %s
                    ORDER BY sort_order ASC, id ASC
                """
                cursor.execute(sql, (report_id,))
                return cursor.fetchall()
    
    @staticmethod
    def count_files_by_report(report_id: int) -> int:
        """
        获取报告的文件数量
        
        Args:
            report_id: 报告ID
            
        Returns:
            文件数量
        """
        with get_mysql_connection() as connection:
            with connection.cursor() as cursor:
                sql = """
                    SELECT COUNT(*) FROM checkup_report_files
                    WHERE report_id = %s
                """
                cursor.execute(sql, (report_id,))
                result = cursor.fetchone()
                return result[0] if result else 0
    
    @staticmethod
    def delete_files_by_report(report_id: int) -> int:
        """
        删除报告的所有文件记录
        
        Args:
            report_id: 报告ID
            
        Returns:
            删除的文件数量
        """
        with get_mysql_connection() as connection:
            with connection.cursor() as cursor:
                sql = "DELETE FROM checkup_report_files WHERE report_id = %s"
                cursor.execute(sql, (report_id,))
                connection.commit()
                return cursor.rowcount
    
    @staticmethod
    def get_file_by_id(file_id: int) -> Optional[Dict[str, Any]]:
        """
        根据ID获取文件信息
        
        Args:
            file_id: 文件ID
            
        Returns:
            文件信息字典，不存在返回None
        """
        with get_mysql_connection() as connection:
            with connection.cursor(dictionary=True) as cursor:
                sql = "SELECT * FROM checkup_report_files WHERE id = %s"
                cursor.execute(sql, (file_id,))
                return cursor.fetchone()
