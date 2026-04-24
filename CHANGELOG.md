# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2026-04-10
### Added
- 舌诊上传分析功能
  - 视频上传区域重排，按"必填在上、选填在下"顺序
  - 视频大小、时长、帧率前端校验
  - 舌诊分析结果展示（总体结论、调理建议、舌象分析、面诊分析、体质分析）
- 智能体对话功能
  - 陈主任智能体接入
  - 小慧智能体接入
  - 智能体对话页面优化
- 后端服务
  - 舌诊上传代理服务（tongue_upload_server.py）
  - 智能体对话代理服务（chat_proxy_server.py）
  - 统一配置文件（config.json）
- 配置管理
  - 支持从配置文件读取 API 密钥
  - 生命涌现 API 密钥配置
  - FastGPT API 密钥配置
- 文档完善
  - 前端 README.md
  - 后端 README.md
  - 根目录 README.md
  - 页面展示图片

### Changed
- 后端脚本统一管理
  - 将舌诊和智能体后端脚本移动到 huiliaoMiniPY 目录
  - 统一配置文件管理
- 舌诊上传页面优化
  - 取消"医生必选"
  - 增加"参考视频"、"分析提示"、"分析报告"区块
  - 分析完成后在当前页面展示报告，不跳页
- 修复视频信息读取失败问题
- 修复 showLoading 与 hideLoading 不配对问题

### Fixed
- 真机调试语法错误（可选链操作符）
- 视频预览黑屏问题
- 前端不调用接口问题
- 环境变量配置问题

## [1.0.0] - 2026-04-08
### Added
- 初始导入小程序源码
- 首页重构，实现医疗科技感设计
- 联系我们页面完善
- 底部导航栏配置
- 图片资源和图标生成

### Changed
- 品牌名称从"慧疗"改为"榕慧"
- 公司名称更新为"榕慧科技(杭州)有限公司"
- 联系方式更新

### Fixed
- 底部导航栏图标显示问题

[Unreleased]: https://github.com/YiHarvest/huiliaoMinProgram/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/YiHarvest/huiliaoMinProgram/releases/tag/v1.1.0
[1.0.0]: https://github.com/YiHarvest/huiliaoMinProgram/releases/tag/v1.0.0
