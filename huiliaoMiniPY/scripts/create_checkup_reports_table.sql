-- 检查报告功能数据库表创建脚本
-- 创建时间: 2026-05-09
-- 注意: 不要修改已有表，只新增检查报告相关表

-- ============================================
-- 1. 检查报告主表
-- 保存一次检查报告记录
-- ============================================
CREATE TABLE IF NOT EXISTS checkup_reports (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '报告ID',
    user_id BIGINT NOT NULL COMMENT '用户ID',
    doctor_id VARCHAR(64) NULL COMMENT '医生ID',
    doctor_name VARCHAR(128) NULL COMMENT '医生姓名',
    doctor_department VARCHAR(128) NULL COMMENT '医生科室',
    report_type VARCHAR(64) NULL COMMENT '报告类型',
    status VARCHAR(32) DEFAULT 'created' COMMENT '状态: created/uploaded/completed',
    remark TEXT NULL COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    deleted_at DATETIME NULL COMMENT '软删除时间',
    
    -- 索引
    INDEX idx_reports_user_id (user_id),
    INDEX idx_reports_created_at (created_at),
    INDEX idx_reports_status (status),
    INDEX idx_reports_deleted_at (deleted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='检查报告主表';

-- ============================================
-- 2. 检查报告文件表
-- 保存报告图片文件
-- ============================================
CREATE TABLE IF NOT EXISTS checkup_report_files (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '文件ID',
    report_id BIGINT NOT NULL COMMENT '关联的报告ID',
    user_id BIGINT NOT NULL COMMENT '用户ID',
    file_path VARCHAR(512) NOT NULL COMMENT '文件存储路径',
    file_url VARCHAR(512) NOT NULL COMMENT '文件访问URL',
    original_name VARCHAR(255) NULL COMMENT '原始文件名',
    file_size BIGINT NULL COMMENT '文件大小(字节)',
    mime_type VARCHAR(64) NULL COMMENT '文件MIME类型',
    sort_order INT DEFAULT 0 COMMENT '排序顺序',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    -- 索引
    INDEX idx_files_report_id (report_id),
    INDEX idx_files_user_id (user_id),
    INDEX idx_files_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='检查报告文件表';

-- ============================================
-- 3. 验证表创建成功
-- ============================================
SHOW TABLES LIKE 'checkup%';

-- 查看表结构
DESC checkup_reports;
DESC checkup_report_files;
