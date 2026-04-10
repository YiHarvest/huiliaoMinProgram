# 榕慧小程序后端服务

## 项目结构

```
huiliaoMiniPY/
├── config.json         # 配置文件
├── config.py           # 配置读取模块
├── test_shezheng_api.py # 测试脚本
├── tongue_upload_server.py # 舌诊上传代理服务
├── requirements.txt    # 依赖项
└── uploads/            # 上传文件存储目录
```

## 主要功能

1. **舌诊分析代理**：
   - 接收前端上传的视频文件
   - 调用生命涌现的舌面分析 API
   - 处理轮询获取分析结果
   - 返回结构化的分析报告

2. **智能问答代理**：
   - 转发智能体问答请求到 FastGPT
   - 处理响应并返回给前端

## 技术栈

- Python 3.8+
- requests 库
- 内置 http.server 模块

## 环境配置

1. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   ```

2. **配置 API 密钥**：
   - 编辑 `config.json` 文件
   - 在 `life_emergence.ak` 和 `life_emergence.sk` 字段中填入生命涌现的 API 密钥
   - 可选：修改 `server.host` 和 `server.port` 配置服务器地址和端口

## 启动服务

### 舌诊上传服务

```bash
python tongue_upload_server.py
```

服务默认运行在：`http://127.0.0.1:8020`

### 智能问答服务

```bash
python chat_proxy_server.py
```

服务默认运行在：`http://127.0.0.1:8010`

## 后端服务地址

- **舌诊上传服务**：`http://127.0.0.1:8020`
- **智能体服务**：`http://127.0.0.1:8010`

## API 端点

### 舌诊上传服务

- **POST /api/tongue-analysis**：
  - 上传视频文件进行分析
  - 请求：multipart/form-data，参数 `video` 为视频文件
  - 响应：JSON 格式的分析报告

- **GET /health**：
  - 健康检查
  - 响应：服务状态信息

- **GET /examples/tongue-video**：
  - 获取示例视频
  - 响应：MP4 视频文件

### 智能问答服务

- **POST /api/chat**：
  - 智能体问答
  - 请求：JSON 格式，包含 `assistantId`、`question`、`chatId`
  - 响应：JSON 格式的智能体回复

- **GET /health**：
  - 健康检查
  - 响应：服务状态信息

## 配置说明

### config.json 示例

```json
{
  "life_emergence": {
    "ak": "your_api_key",
    "sk": "your_secret_key",
    "base_url": "https://open.lifeemergence.com"
  },
  "server": {
    "host": "127.0.0.1",
    "port": 8020
  }
}
```

## 错误处理

- **VIDEO_POOR_QUALITY**：视频质量不满足要求
- **HEALTH_ANALYSIS_ERROR**：分析失败
- **HEALTH_ANALYSIS_TIMEOUT**：分析超时
- **LOCAL_POLL_TIMEOUT**：本地轮询超时

## 部署说明

1. **本地开发**：
   - 直接运行 Python 脚本
   - 前端使用 `http://127.0.0.1:8020` 访问

2. **生产环境**：
   - 使用 Nginx 反向代理
   - 配置 SSL 证书实现 HTTPS
   - 前端使用域名访问

3. **服务器配置**：
   - 确保服务器安全组开放相应端口
   - 配置防火墙规则
   - 设置服务自启动

## 注意事项

1. **API 密钥安全**：
   - 不要将 `config.json` 提交到版本控制系统
   - 生产环境使用环境变量或密钥管理服务

2. **文件存储**：
   - 上传的视频文件会存储在 `uploads` 目录
   - 定期清理过期文件

3. **性能优化**：
   - 生产环境建议使用 Gunicorn 等 WSGI 服务器
   - 配置适当的超时时间

4. **监控**：
   - 建议添加日志记录
   - 监控服务运行状态
