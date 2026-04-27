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

try:
    # 连接MySQL数据库
    connection = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = connection.cursor(dictionary=True)
    
    # 查询所有模板
    cursor.execute("SELECT id, questionnaire_name FROM crm_questionnaire_template ORDER BY id")
    templates = cursor.fetchall()
    
    print(f"=== MySQL 中的所有模板（共 {len(templates)} 条）===")
    for i, template in enumerate(templates):
        print(f"{i+1}. ID: {template['id']}, 名称: {template['questionnaire_name']}")
    
    # 查找特定的 templateId
    test_id = 2044969684322750465
    cursor.execute(
        "SELECT id, questionnaire_name FROM crm_questionnaire_template WHERE id = %s",
        (test_id,)
    )
    result = cursor.fetchone()
    
    print(f"\n=== 查找特定 templateId: {test_id} ===")
    if result:
        print(f"找到: {result['questionnaire_name']}")
    else:
        print("未找到")
    
    # 关闭连接
    cursor.close()
    connection.close()
    
except Exception as e:
    print(f"错误: {e}")
