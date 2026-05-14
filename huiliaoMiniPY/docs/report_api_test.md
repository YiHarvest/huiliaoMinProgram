# 检查报告接口测试记录

## 测试时间
2026-05-09

## 测试环境
- 服务器: 1Panel (192.168.1.208)
- 服务端口: 3161 (chat_proxy_server.py)
- 公网域名: https://miniprogram.huiliaoyiyuan.com
- 数据库: 1Panel MySQL

## 已通过测试的接口

### 1. 创建报告接口

**请求:**
```http
POST /api/report/create
Content-Type: application/json

{
  "userId": 1,
  "doctorId": "doc_001",
  "doctorName": "张医生",
  "doctorDepartment": "内科",
  "reportType": "血常规",
  "remark": "年度体检报告"
}
```

**响应:**
```json
{
  "success": true,
  "data": {
    "reportId": 2,
    "userId": 1,
    "status": "created",
    "createdAt": "2026-05-09T14:30:00.000000"
  }
}
```

**状态:** ✅ 通过

---

### 2. 上传报告图片接口

**请求:**
```http
POST /api/report/file/upload
Content-Type: multipart/form-data

reportId: 2
userId: 1
sortOrder: 0
file: [二进制图片数据]
```

**响应:**
```json
{
  "success": true,
  "data": {
    "fileId": 1,
    "reportId": 2,
    "fileUrl": "https://miniprogram.huiliaoyiyuan.com/uploads/reports/1/20260509/xxxx-xxxx.jpg",
    "originalName": "report.jpg",
    "fileSize": 102400,
    "sortOrder": 0
  }
}
```

**状态:** ✅ 通过

**限制:**
- 支持格式: jpg, jpeg, png, webp
- 单张最大: 10MB
- 每报告最多: 9张

---

### 3. 查询报告详情接口

**请求:**
```http
GET /api/report/detail?reportId=2&userId=1
```

**响应:**
```json
{
  "success": true,
  "data": {
    "reportId": 2,
    "userId": 1,
    "doctorId": "doc_001",
    "doctorName": "张医生",
    "doctorDepartment": "内科",
    "reportType": "血常规",
    "status": "uploaded",
    "remark": "年度体检报告",
    "createdAt": "2026-05-09T14:30:00.000000",
    "updatedAt": "2026-05-09T14:35:00.000000",
    "files": [
      {
        "fileId": 1,
        "fileUrl": "https://miniprogram.huiliaoyiyuan.com/uploads/reports/1/20260509/xxxx-xxxx.jpg",
        "originalName": "report.jpg",
        "fileSize": 102400,
        "mimeType": "image/jpeg",
        "sortOrder": 0,
        "createdAt": "2026-05-09T14:32:00.000000"
      }
    ]
  }
}
```

**状态:** ✅ 通过

---

### 4. 完成报告接口

**请求:**
```http
POST /api/report/complete
Content-Type: application/json

{
  "reportId": 2,
  "userId": 1
}
```

**响应:**
```json
{
  "success": true,
  "data": {
    "reportId": 2,
    "status": "completed",
    "fileCount": 1,
    "completedAt": "2026-05-09T14:40:00.000000"
  }
}
```

**状态:** ✅ 通过

---

### 5. 查询报告列表接口

**请求:**
```http
GET /api/report/list?userId=1&limit=20&offset=0
```

**响应:**
```json
{
  "success": true,
  "data": {
    "list": [
      {
        "reportId": 2,
        "userId": 1,
        "doctorId": "doc_001",
        "doctorName": "张医生",
        "doctorDepartment": "内科",
        "reportType": "血常规",
        "status": "completed",
        "remark": "年度体检报告",
        "createdAt": "2026-05-09T14:30:00.000000",
        "updatedAt": "2026-05-09T14:40:00.000000"
      }
    ],
    "total": 1,
    "limit": 20,
    "offset": 0
  }
}
```

**状态:** ✅ 通过

**公网测试:**
```bash
curl "https://miniprogram.huiliaoyiyuan.com/api/report/list?userId=1"
# 返回 HTTP 200
```

---

## 完整测试流程记录

### reportId=2 测试流程

| 步骤 | 接口 | 状态 | 说明 |
|------|------|------|------|
| 1 | POST /api/report/create | ✅ | 创建报告成功，返回 reportId=2 |
| 2 | POST /api/report/file/upload | ✅ | 上传图片成功 |
| 3 | GET /api/report/detail | ✅ | 查询详情成功，包含文件列表 |
| 4 | POST /api/report/complete | ✅ | 完成报告成功，状态变为 completed |
| 5 | GET /api/report/list | ✅ | 列表中包含已完成的报告 |

---

## 数据库表结构

### checkup_reports 表
```sql
CREATE TABLE checkup_reports (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT NOT NULL,
  doctor_id VARCHAR(64) NULL,
  doctor_name VARCHAR(128) NULL,
  doctor_department VARCHAR(128) NULL,
  report_type VARCHAR(64) NULL,
  status VARCHAR(32) DEFAULT 'created',
  remark TEXT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted_at DATETIME NULL,
  INDEX idx_reports_user_id (user_id),
  INDEX idx_reports_created_at (created_at),
  INDEX idx_reports_status (status),
  INDEX idx_reports_deleted_at (deleted_at)
);
```

### checkup_report_files 表
```sql
CREATE TABLE checkup_report_files (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  report_id BIGINT NOT NULL,
  user_id BIGINT NOT NULL,
  file_path VARCHAR(512) NOT NULL,
  file_url VARCHAR(512) NOT NULL,
  original_name VARCHAR(255) NULL,
  file_size BIGINT NULL,
  mime_type VARCHAR(64) NULL,
  sort_order INT DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_files_report_id (report_id),
  INDEX idx_files_user_id (user_id),
  INDEX idx_files_created_at (created_at)
);
```

---

## 文件存储路径

```
uploads/reports/{user_id}/{yyyyMMdd}/{uuid}.{ext}
```

示例:
```
uploads/reports/1/20260509/a1b2c3d4-e5f6-7890-abcd-ef1234567890.jpg
```

---

## 前端接入说明

### 接口调用顺序

```
1. POST /api/report/create
   ↓ 获取 reportId
2. POST /api/report/file/upload (可多次调用，最多9张)
   ↓ 所有图片上传完成
3. POST /api/report/complete
   ↓ 完成
4. GET /api/report/list (查询列表)
```

### 错误处理

| 错误场景 | 返回状态码 | 错误信息 |
|----------|-----------|----------|
| 用户ID为空 | 400 | 用户ID不能为空 |
| 报告不存在 | 400 | 报告不存在 |
| 无权操作 | 400 | 无权操作此报告 |
| 文件格式错误 | 400 | 不支持的文件格式 |
| 文件过大 | 400 | 文件大小超过限制 |
| 图片数量超限 | 400 | 每个报告最多上传9张图片 |

---

## 后端代码文件

| 文件路径 | 说明 |
|----------|------|
| `database/report_repository.py` | 数据库操作层 |
| `modules/report/service.py` | 业务逻辑层 |
| `modules/report/handlers.py` | 接口处理层 |
| `chat_proxy_server.py` | 路由分发（已添加6个接口+1个静态文件路由） |

---

## 备注

- 所有接口均已通过服务器端测试
- 公网域名可正常访问
- 图片上传后可通过 fileUrl 直接访问
- 报告删除使用软删除（设置 deleted_at）
