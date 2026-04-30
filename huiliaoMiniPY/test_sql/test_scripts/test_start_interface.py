from db import start_questionnaire, use_mysql
import mysql.connector
from config import config

# MySQL连接配置
MYSQL_CONFIG = {
    'host': config.get('database', {}).get('mysql', {}).get('host', '192.168.1.208'),
    'port': config.get('database', {}).get('mysql', {}).get('port', 13060),
    'user': config.get('database', {}).get('mysql', {}).get('user', 'miniprogramYQY'),
    'password': config.get('database', {}).get('mysql', {}).get('password', 'yqy123456'),
    'database': config.get('database', {}).get('mysql', {}).get('database', 'miniprogramYQY'),
    'charset': 'utf8mb4',
    'autocommit': True,
    'ssl_disabled': True
}

print("是否使用 MySQL:", use_mysql())

# 测试调用 start 接口
template_id = 2044969684322750465
external_user_id = "test_user_123"

print(f"\n=== 调用 start_questionnaire ===")
print(f"external_user_id: {external_user_id}")
print(f"template_id: {template_id}")

try:
    record_id = start_questionnaire(external_user_id, template_id)
    print(f"返回的 record_id: {record_id}")
    print(f"record_id 类型: {type(record_id)}")
    
    # 在 MySQL 中查询这个 record_id
    connection = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = connection.cursor(dictionary=True)
    
    cursor.execute(
        "SELECT id, external_user_id, questionnaire_name, status FROM crm_questionnaire_user_record WHERE id = %s",
        (record_id,)
    )
    result = cursor.fetchone()
    
    print(f"\n=== 在 MySQL 中查询 record_id ===")
    if result:
        print(f"找到记录:")
        print(f"  id: {result['id']}")
        print(f"  external_user_id: {result['external_user_id']}")
        print(f"  questionnaire_name: {result['questionnaire_name']}")
        print(f"  status: {result['status']}")
    else:
        print(f"未找到 record_id: {record_id}")
    
    cursor.close()
    connection.close()
    
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
