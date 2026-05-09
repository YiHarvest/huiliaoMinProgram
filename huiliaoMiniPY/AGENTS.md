【慧疗小程序后端开发固定约束】

请严格遵守以下开发规范，后续所有新功能、新接口、新数据库操作都必须按照这个规范执行。

一、总体原则

1. 当前项目后端已经有多个功能跑通，包括：
   - 微信登录
   - 用户资料保存与读取
   - 手机号、身份证号保存与脱敏展示
   - 智能对话
   - 量表填写
   - 舌诊上传与结果查询

2. 开发新功能时，必须优先保证上述功能不被破坏。

3. 不允许为了开发新功能，大量改动已有核心文件。

4. 不允许把新功能继续堆到以下文件中：
   - chat_proxy_server.py
   - tongue_upload_server.py
   - mysql_storage.py

5. 以上文件只能做必要的最小改动：
   - chat_proxy_server.py 只允许增加少量“路由分发代码”
   - tongue_upload_server.py 除非是舌诊功能本身，否则不要修改
   - mysql_storage.py 暂时保留旧逻辑，不要继续往里面新增新业务 SQL

二、新功能必须按文件夹分类

以后每开发一个新功能，都必须在 modules/ 下新建独立功能目录。

示例：

huiliaoMiniPY/
  modules/
    user/
      handlers.py
      service.py
    report/
      handlers.py
      service.py
    appointment/
      handlers.py
      service.py
    payment/
      handlers.py
      service.py

每个模块职责如下：

1. handlers.py
   - 负责处理接口请求
   - 解析参数
   - 调用 service
   - 返回 JSON 响应
   - 不允许直接写复杂业务逻辑
   - 不允许直接写 SQL

2. service.py
   - 负责业务逻辑
   - 参数校验
   - 数据转换
   - 调用 database 目录下的 repository
   - 不允许直接管理数据库连接

三、数据库操作必须单独放到 database/ 目录

以后新功能涉及数据库读写时，必须放到 database/ 目录，不允许继续写进 mysql_storage.py。

推荐结构：

huiliaoMiniPY/
  database/
    __init__.py
    connection.py
    user_repository.py
    questionnaire_repository.py
    chat_repository.py
    tongue_repository.py
    report_repository.py
    appointment_repository.py

职责说明：

1. database/connection.py
   - 只负责 MySQL 连接
   - 只写通用数据库工具函数
   - 不写具体业务 SQL

2. xxx_repository.py
   - 只负责某一个业务模块的数据库读写
   - 一个业务模块一个 repository 文件
   - 不同业务不要混写在同一个 repository 文件中

例如：

用户相关 SQL：
database/user_repository.py

量表相关 SQL：
database/questionnaire_repository.py

智能对话相关 SQL：
database/chat_repository.py

舌诊相关 SQL：
database/tongue_repository.py

检查报告相关 SQL：
database/report_repository.py

四、接口入口文件的限制

chat_proxy_server.py 是主服务入口，不允许继续堆业务逻辑。

允许的写法：

1. 在 chat_proxy_server.py 中识别 URL 路径
2. 把请求转交给对应模块的 handler
3. handler 再调用 service
4. service 再调用 repository

推荐调用链：

chat_proxy_server.py
  ↓
modules/功能名/handlers.py
  ↓
modules/功能名/service.py
  ↓
database/功能名_repository.py
  ↓
MySQL

不允许的写法：

1. 直接在 chat_proxy_server.py 里写大量 if else 业务逻辑
2. 直接在 chat_proxy_server.py 里写 SQL
3. 直接在 chat_proxy_server.py 里处理复杂数据计算
4. 把新功能写到 tongue_upload_server.py
5. 把新功能 SQL 写到 mysql_storage.py

五、tongue_upload_server.py 保护规则

tongue_upload_server.py 是舌诊服务入口，当前用于 3162 端口。

除非明确要求修改舌诊功能，否则不要修改该文件。

不允许把以下功能写入 tongue_upload_server.py：

1. 用户资料
2. 手机号、身份证号
3. 量表
4. 智能对话
5. 检查报告
6. 预约
7. 支付
8. 日志
9. 其他非舌诊功能

六、mysql_storage.py 保护规则

mysql_storage.py 当前作为历史数据库操作文件保留。

后续要求：

1. 不要删除 mysql_storage.py
2. 不要大规模重构 mysql_storage.py
3. 不要继续往 mysql_storage.py 增加新功能 SQL
4. 如果必须修改，只允许修复已有函数的问题
5. 新功能数据库操作必须写到 database/xxx_repository.py

七、测试文件必须放到 tests/ 目录

所有测试脚本必须放到 tests/ 目录，不允许散落在后端根目录。

推荐结构：

huiliaoMiniPY/
  tests/
    test_user_profile.py
    test_login.py
    test_questionnaire.py
    test_chat.py
    test_tongue.py
    test_report.py

测试规则：

1. 临时测试脚本也要放到 tests/
2. 不要在根目录随便新建 test_xxx.py
3. 测试脚本不能影响生产数据库数据
4. 涉及手机号、身份证号、openid、session_key 的测试日志必须脱敏

八、脚本文件必须放到 scripts/ 目录

数据库初始化、迁移、修复类脚本必须放到 scripts/ 目录。

推荐结构：

huiliaoMiniPY/
  scripts/
    create_user_sensitive_info.sql
    alter_user_profiles.sql
    migrate_xxx.py
    fix_xxx_data.py

不允许把一次性脚本直接放在后端根目录。

九、数据库使用限制

1. 当前生产环境只使用 1Panel 中的 MySQL。
2. 不允许新增 SQLite 逻辑。
3. 不允许新功能依赖 SQLite。
4. 不允许新增 SQLite 数据库文件。
5. 历史 SQLite 文件可以保留备份，但新功能不要使用。

十、敏感信息处理规则

涉及以下信息时必须注意安全：

1. 手机号
2. 身份证号
3. openid
4. unionid
5. session_key
6. token
7. 用户头像地址
8. 用户真实资料

要求：

1. 日志中不要打印完整手机号
2. 日志中不要打印完整身份证号
3. 日志中不要打印 session_key
4. 前端展示手机号和身份证号时默认脱敏
5. 数据库存储敏感信息时，业务层返回给前端应优先返回脱敏字段
6. 除非明确需要，不要把完整敏感信息返回给前端

十一、端口保护规则

当前端口规划：

1. 3161：主业务服务，包括微信登录、用户资料、智能对话、量表等
2. 3162：舌诊服务

要求：

1. 不要随意修改 3161 和 3162
2. 不要新增未知端口
3. 如果确实需要新增服务端口，必须先说明原因，再等待确认
4. 不要把多个服务重复监听同一个端口

十二、开发前必须先做的事情

每次开发新功能前，必须先检查：

1. 当前目录结构
2. 当前接口路径
3. 当前数据库表
4. 当前已有函数
5. 是否已有类似功能
6. 新功能应该放在哪个 modules 子目录
7. 新功能数据库操作应该放在哪个 database repository 文件

不要在不了解现有结构的情况下直接修改核心文件。

十三、开发完成后必须汇报

每次修改完成后，请按照以下格式汇报：

1. 本次新增了哪些文件
2. 本次修改了哪些文件
3. 是否修改了 chat_proxy_server.py
4. 是否修改了 tongue_upload_server.py
5. 是否修改了 mysql_storage.py
6. 新功能放在哪个 modules 目录
7. 数据库操作放在哪个 database repository 文件
8. 新增或修改了哪些接口
9. 新增或修改了哪些数据库表或字段
10. 测试了哪些接口
11. 是否确认没有影响：
    - 微信登录
    - 用户资料
    - 手机号、身份证号
    - 智能对话
    - 量表填写
    - 舌诊服务

十四、禁止事项总结

禁止把新功能直接写进 chat_proxy_server.py。
禁止把非舌诊功能写进 tongue_upload_server.py。
禁止继续把新 SQL 堆到 mysql_storage.py。
禁止新增 SQLite 逻辑。
禁止测试脚本散落在根目录。
禁止打印完整敏感信息。
禁止大规模重构已跑通功能。
禁止未经确认修改 3161、3162 端口。

十五、推荐开发方式

新功能开发推荐流程：

1. 先说明功能属于哪个模块
2. 在 modules/功能名/ 下创建 handlers.py 和 service.py
3. 在 database/ 下创建或使用对应 repository 文件
4. 在 chat_proxy_server.py 中只增加最小路由分发
5. 在 tests/ 下新增测试脚本
6. 测试通过后再汇报修改结果