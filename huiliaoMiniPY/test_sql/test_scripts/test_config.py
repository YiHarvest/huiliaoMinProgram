from config import config
print("config内容:")
print(config)
print("\ndatabase.type:", config.get('database', {}).get('type', 'sqlite'))
print("database.mysql:", config.get('database', {}).get('mysql', {}))

# 检查mysql_storage导入
print("\n检查mysql_storage导入:")
try:
    from mysql_storage import get_questionnaire_options_mysql
    print("mysql_storage导入成功")
except Exception as e:
    print(f"mysql_storage导入失败: {e}")

# 检查db模块
print("\n检查db模块:")
try:
    from db import get_db_type, use_mysql
    print("db模块导入成功")
    print("get_db_type():", get_db_type())
    print("use_mysql():", use_mysql())
except Exception as e:
    print(f"db模块导入失败: {e}")