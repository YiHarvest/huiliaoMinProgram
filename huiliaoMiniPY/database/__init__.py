"""
database 包 - 数据库操作层

职责：
- connection.py: MySQL连接和通用数据库工具
- user_repository.py: 用户相关数据库操作
- questionnaire_repository.py: 量表相关数据库操作
- chat_repository.py: 智能对话相关数据库操作
- tongue_repository.py: 舌诊相关数据库操作
- report_repository.py: 报告相关数据库操作（预留）

使用说明：
1. 新功能的数据库操作请写到对应的 repository 文件中
2. 不要在 chat_proxy_server.py 中直接写 SQL
3. 不要继续往 mysql_storage.py 添加新函数
4. 旧功能保持使用 mysql_storage.py 不变，避免破坏现有功能
"""

from .connection import get_mysql_connection, get_mysql_cursor
from .user_repository import UserRepository
from .questionnaire_repository import QuestionnaireRepository
from .chat_repository import ChatRepository
from .tongue_repository import TongueRepository
from .report_repository import ReportRepository

__all__ = [
    'get_mysql_connection',
    'get_mysql_cursor',
    'UserRepository',
    'QuestionnaireRepository',
    'ChatRepository',
    'TongueRepository',
    'ReportRepository',
]
