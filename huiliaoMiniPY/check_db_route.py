from db import use_mysql, get_db_type, mysql_available

print("数据库类型配置:", get_db_type())
print("MySQL 模块是否可用:", mysql_available)
print("是否使用 MySQL:", use_mysql())

# 测试调用 options 接口
from db import get_questionnaire_options
result = get_questionnaire_options("test123")
print("\n=== 量表列表前 3 条 ===")
for i, scale in enumerate(result['scales'][:3]):
    print(f"{i+1}. templateId: {scale['templateId']}, 名称: {scale['questionnaireName']}")
