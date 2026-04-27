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

record_id = 1776841012538750167

try:
    # 连接MySQL数据库
    connection = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = connection.cursor(dictionary=True)
    
    # 查询 record_id
    cursor.execute(
        "SELECT id, external_user_id, questionnaire_name, status, create_time FROM crm_questionnaire_user_record WHERE id = %s",
        (record_id,)
    )
    result = cursor.fetchone()
    
    print(f"=== 查询 record_id: {record_id} ===")
    if result:
        print(f"找到记录:")
        print(f"  id: {result['id']}")
        print(f"  external_user_id: {result['external_user_id']}")
        print(f"  questionnaire_name: {result['questionnaire_name']}")
        print(f"  status: {result['status']}")
        print(f"  create_time: {result['create_time']}")
    else:
        print(f"未找到 record_id: {record_id}")
    
    cursor.close()
    connection.close()
    
except Exception as e:
    print(f"错误: {e}")
