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
    
    # 测试查询几个 templateId
    test_ids = [2044969684322750465, 2042879199571611650, 2044968508025999362]
    
    print("=== 测试查询 templateId ===")
    for test_id in test_ids:
        cursor.execute(
            "SELECT id, questionnaire_name FROM crm_questionnaire_template WHERE id = %s",
            (test_id,)
        )
        result = cursor.fetchone()
        if result:
            print(f"[OK] 找到: {test_id} -> {result['questionnaire_name']}")
        else:
            print(f"[FAIL] 未找到: {test_id}")
    
    # 查询实际的模板ID
    print("\n=== MySQL 中的实际模板ID ===")
    cursor.execute("SELECT id, questionnaire_name FROM crm_questionnaire_template LIMIT 5")
    templates = cursor.fetchall()
    for template in templates:
        print(f"ID: {template['id']}, 名称: {template['questionnaire_name']}")
    
    # 关闭连接
    cursor.close()
    connection.close()
    
except Exception as e:
    print(f"错误: {e}")
