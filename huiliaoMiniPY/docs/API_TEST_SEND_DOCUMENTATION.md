# 订阅消息测试接口文档

## 📋 接口概述

**接口地址：** `POST /api/subscription/test-send`

**功能描述：** 手动给指定用户发送一次舌苔拍摄提醒订阅消息（用于测试）

**特点：**
- ✅ 不影响原有的开启/关闭/保存配置逻辑
- ✅ 不影响定时任务
- ✅ 即使未开启提醒，也会尝试发送
- ✅ 返回完整的微信 API 结果和错误信息
- ✅ 详细的日志记录，便于排查问题

---

## 🔧 请求参数

### 请求方式
```
POST /api/subscription/test-send
Content-Type: application/json
```

### 请求体

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `userId` | string/number | ✅ 是 | - | 用户ID |
| `scene` | string | ❌ 否 | `tongue_reminder` | 场景名称，目前仅支持 `tongue_reminder` |

### 请求示例

#### **基本请求**
```bash
curl -X POST http://localhost:8000/api/subscription/test-send \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "1"
  }'
```

#### **完整请求（显式指定场景）**
```bash
curl -X POST http://localhost:8000/api/subscription/test-send \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "1",
    "scene": "tongue_reminder"
  }'
```

---

## 📤 响应格式

### 成功响应 (HTTP 200)

```json
{
  "success": true,
  "data": {
    "userId": "1",
    "openid": "oXXXXXXXXXXXXXXXXXXXX",
    "scene": "tongue_reminder",
    "templateId": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "page": "pages/tongue-upload/tongue-upload",
    "wechatResult": {
      "errcode": 0,
      "errmsg": "ok",
      "msgid": 1234567890
    },
    "durationMs": 256.78,
    "sentAt": "2026-05-14 14:30:00"
  }
}
```

### 微信发送失败响应 (HTTP 502)

```json
{
  "success": false,
  "data": {
    "userId": "1",
    "openid": "oXXXXXXXXXXXXXXXXXXXX",
    "scene": "tongue_reminder",
    "templateId": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "page": "pages/tongue-upload/tongue-upload",
    "wechatResult": {
      "errcode": 43101,
      "errmsg": "user refuse to accept the msg",
      "msgid": 0
    },
    "durationMs": 189.45,
    "sentAt": "2026-05-14 14:30:00"
  },
  "error": {
    "errcode": 43101,
    "errmsg": "user refuse to accept the msg",
    "message": "微信订阅消息发送失败: user refuse to accept the msg (43101)"
  }
}
```

### 参数验证失败响应 (HTTP 400)

```json
{
  "error": "userId 不能为空",
  "type": "ValidationError"
}
```

### 用户不存在响应 (HTTP 404)

```json
{
  "error": "未找到用户 999 的 openid，请确认用户是否存在"
}
```

### 服务器内部错误响应 (HTTP 500)

```json
{
  "error": "数据库连接失败",
  "type": "InternalServerError",
  "message": "服务器内部错误: 数据库连接失败"
}
```

---

## 📊 响应字段说明

### data 对象

| 字段 | 类型 | 说明 |
|------|------|------|
| `userId` | string | 用户ID |
| `openid` | string | 用户微信 OpenID |
| `scene` | string | 场景名称 |
| `templateId` | string | 消息模板ID |
| `page` | string | 点击消息后跳转的小程序页面路径 |
| `wechatResult` | object | 微信 API 原始返回结果 |
| `durationMs` | number | 调用微信 API 的耗时（毫秒） |
| `sentAt` | string | 发送时间（YYYY-MM-DD HH:MM:SS） |

### wechatResult 对象（微信 API 返回）

| 字段 | 类型 | 说明 |
|------|------|------|
| `errcode` | number | 错误码，0 表示成功 |
| `errmsg` | string | 错误信息 |
| `msgid` | number | 消息 ID（成功时返回） |

---

## ⚠️ 常见错误码

### 微信订阅消息错误码

| 错误码 | 错误信息 | 原因及解决方案 |
|--------|---------|--------------|
| `0` | `ok` | 发送成功 ✅ |
| `40003` | `invalid openid` | 无效的 OpenID，检查用户是否正确授权登录 |
| `40037` | `invalid template_id` | 无效的模板ID，检查 config.py 配置 |
| `43101` | `user refuse to accept the msg` | 用户拒绝接收消息，需要重新授权订阅 |
| `43102` | `user is blocked by the merchant` | 用户被拉黑或投诉 |
| `47003` | `argument invalid!` | 参数不合法，检查模板数据是否符合要求 |
| `41030` | `page path is not valid` | 小程序页面路径无效 |
| `45009` | `reach max api daily quota limit` | 达到接口调用频率限制 |

### 接口业务错误

| HTTP 状态码 | 错误类型 | 说明 |
|------------|---------|------|
| 400 | `ValidationError` | 参数验证失败（如 userId 为空、scene 不支持） |
| 404 | `NotFound` | 用户不存在或未找到 openid |
| 500 | `InternalServerError` | 服务器内部错误（如数据库异常） |
| 502 | `WechatAPIError` | 微信 API 调用失败 |

---

## 🚀 快速开始

### 方法一：使用 curl 测试

```bash
# 1. 给用户ID=1 发送测试消息
curl -X POST http://localhost:8000/api/subscription/test-send \
  -H "Content-Type: application/json" \
  -d '{"userId": "1"}'

# 2. 查看详细结果（美化输出）
curl -X POST http://localhost:8000/api/subscription/test-send \
  -H "Content-Type: application/json" \
  -d '{"userId": "1"}' | python -m json.tool
```

### 方法二：使用 Python 测试脚本

```bash
# 进入项目目录
cd huiliaoMiniPY

# 运行测试脚本
python tests/test_subscription_send.py --user-id 1

# 完整参数示例
python tests/test_subscription_send.py \
  --user-id 1 \
  --scene tongue_reminder \
  --base-url http://localhost:8000
```

### 方法三：使用 Postman / Apifox

1. 创建新请求
2. 设置方法为 `POST`
3. 输入 URL：`http://localhost:8000/api/subscription/test-send`
4. Headers 中添加：
   ```
   Content-Type: application/json
   ```
5. Body 选择 `raw` -> `JSON`，输入：
   ```json
   {
     "userId": "1"
   }
   ```
6. 点击 Send 按钮

---

## 📝 使用流程

### 1️⃣ 确认前置条件

- [x] 后端服务已启动（`python chat_proxy_server.py`）
- [x] 用户已在小程序中登录过（数据库中有该用户的 openid）
- [x] 已在 `config.py` 中配置了 `tongueReminderTemplateId`
- [x] （可选但推荐）用户已在小程序中授权过订阅消息

### 2️⃣ 执行测试请求

```bash
# 示例：给用户ID=1发送测试消息
curl -X POST http://localhost:8000/api/subscription/test-send \
  -H "Content-Type: application/json" \
  -d '{"userId": "1"}'
```

### 3️⃣ 查看后端日志

后端会打印详细的执行日志：

```
[test-send] 收到测试发送请求: userId=1, scene=tongue_reminder
[test-send] 正在查询用户 1 的 openid...
[test-send] 查询到 openid: oXXXXXXXXXXXXXXXXXXXX
[test-send] 正在获取用户 1 的提醒配置...
[test-send] 用户配置 - templateId: XXXXXX, enabled: True
[test-send] 正在调用微信订阅消息发送 API...
[test-send] 参数 - openid: oXXXXXXXXXXXXXXXXXXXX, scene: tongue_reminder, templateId: XXXXXX
[test-send] 微信 API 调用完成，耗时: 256.78ms
[test-send] 微信返回结果: {"errcode": 0, "errmsg": "ok", "msgid": 1234567890}
[test-send] ✅ 发送成功! userId=1, openid=oXXXXXXXXXXXXXXXXXXXX
```

### 4️⃣ 在微信中查看结果

打开微信 → 服务通知 → 查看是否收到舌苔拍摄提醒消息

---

## 🔍 问题排查指南

### 场景1：收到 errcode=43101（用户拒绝）

**原因：** 用户未授权或已取消订阅

**解决方案：**
1. 在小程序中进入"消息提醒"页面
2. 点击"开启提醒"按钮
3. 在弹窗中点击"允许"授权订阅消息
4. 重新调用测试接口

---

### 场景2：收到 errcode=40003（无效的 openid）

**原因：** 用户未在小程序中登录过，或 openid 已失效

**解决方案：**
1. 确认用户ID正确
2. 让用户重新打开小程序并登录
3. 检查数据库中是否有该用户的 openid 记录

```sql
-- 检查用户表
SELECT id, openid, nickname FROM users WHERE id = 1;
```

---

### 场景3：收到"未配置 templateId"错误

**原因：** config.py 中未配置 tongueReminderTemplateId

**解决方案：**

编辑 `config.py`：
```python
config = {
    # ... 其他配置 ...

    # 舌苔提醒模板ID（必填）
    'tongueReminderTemplateId': '你的模板ID',

    # ... 其他配置 ...
}
```

获取模板ID的方法：
1. 登录 [微信公众平台](https://mp.weixin.qq.com)
2. 进入「订阅消息」→「公共模板库」
3. 选择合适的模板（如"拍摄提醒"类）
4. 添加到我的模板，复制模板ID

---

### 场景4：连接被拒绝（Connection refused）

**原因：** 后端服务未启动或端口不对

**解决方案：**

```bash
# 启动后端服务
cd huiliaoMiniPY
python chat_proxy_server.py

# 确认端口（默认8000）
# 如果修改了端口，测试时需对应修改 base_url
```

---

### 场景5：超时（Request timeout）

**原因：** 微信 API 响应慢或网络问题

**解决方案：**
1. 检查网络连接
2. 查看后端日志确认卡在哪一步
3. 稍后重试

---

## 🎯 测试用例

### 用例1：正常发送成功

**前置条件：** 用户存在、有openid、已配置templateId

**请求：**
```json
{"userId": "1"}
```

**预期结果：**
- HTTP 200
- `success: true`
- `wechatResult.errcode: 0`
- 微信收到消息

---

### 用例2：用户未授权订阅

**前置条件：** 用户存在但未授权

**请求：**
```json
{"userId": "1"}
```

**预期结果：**
- HTTP 502
- `success: false`
- `wechatResult.errcode: 43101`
- 错误信息："user refuse to accept the msg"

---

### 用例3：用户不存在

**请求：**
```json
{"userId": "99999"}
```

**预期结果：**
- HTTP 404
- 错误信息："未找到用户 99999 的 openid"

---

### 用例4：缺少必要参数

**请求：**
```json
{}
```

**预期结果：**
- HTTP 400
- 错误信息："userId 不能为空"

---

### 用例5：不支持的场景

**请求：**
```json
{"userId": "1", "scene": "ai_reply"}
```

**预期结果：**
- HTTP 400
- 错误信息："不支持的场景: ai_reply"

---

## 📌 注意事项

### ⚠️ 重要提示

1. **仅用于测试**
   - 此接口专门用于开发和调试
   - 不要在生产环境中频繁调用
   - 避免对同一用户短时间内大量发送

2. **不影响原有逻辑**
   - 不会修改用户的提醒配置
   - 不会更新 last_sent_date 或 next_send_at
   - 不会影响定时任务的判断逻辑

3. **微信限制**
   - 每个用户每天最多接收一定数量的订阅消息
   - 用户可以随时取消订阅
   - 模板内容必须符合审核规范

4. **日志监控**
   - 所有操作都会打印详细日志
   - 包含完整的请求参数和响应结果
   - 出错时会打印完整堆栈信息

---

## 🔗 相关文件

| 文件 | 说明 |
|------|------|
| [chat_proxy_server.py](../chat_proxy_server.py) | 接口实现（handle_test_send 方法） |
| [reminder_storage.py](../reminder_storage.py) | 数据库查询（get_user_openid_by_user_id_mysql 等） |
| [wechat_subscription.py](../wechat_subscription.py) | 微信API调用（send_tongue_reminder 等） |
| [test_subscription_send.py](./test_subscription_send.py) | Python 测试脚本 |

---

## 📞 技术支持

如果遇到问题：

1. **查看后端日志**
   ```bash
   # Linux
   tail -f chat_proxy_server.log | grep test-send
   
   # Windows PowerShell
   Get-Content chat_proxy_server.log -Wait | Select-String "test-send"
   ```

2. **检查微信官方文档**
   - [订阅消息接口文档](https://developers.weixin.qq.com/miniprogram/dev/OpenApiDoc/msg-subscribe/msg-subscribe/sendMessage.html)
   - [错误码查询](https://developers.weixin.qq.com/doc/offiaccount/Message_Management/Template_Message_Interface/Error_Code.html)

3. **联系开发团队**
   - 提供完整的请求参数和响应结果
   - 提供后端日志截图
   - 说明复现步骤

---

**最后更新时间：** 2026-05-14 14:35:00  
**接口版本：** v1.0.0  
**适用环境：** Development / Staging
