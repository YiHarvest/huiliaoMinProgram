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
    
    # 检查模板表结构
    cursor.execute("DESCRIBE crm_questionnaire_template")
    print("=== crm_questionnaire_template 表结构 ===")
    for column in cursor.fetchall():
        print(f"{column['Field']}: {column['Type']}")
    
    # 查找特定的模板
    target_names = [
        "不育症诊断量表（第一次填表请选择这个表）",
        "国际前列腺症状评分表I-PSS（第一次填表请选择这个表）"
    ]
    
    print("\n=== 查找目标模板 ===")
    for name in target_names:
        cursor.execute(
            "SELECT id, questionnaire_name FROM crm_questionnaire_template WHERE questionnaire_name = %s",
            (name,)
        )
        result = cursor.fetchone()
        if result:
            print(f"模板: {result['questionnaire_name']}")
            print(f"ID: {result['id']}")
            print(f"ID 类型: {type(result['id'])}")
            print(f"ID 长度: {len(str(result['id']))}")
        else:
            print(f"未找到模板: {name}")
        print()
    
    # 检查用户报告的 templateId
    test_ids = [2044969684322750500, 2042879199571611600]
    print("\n=== 检查用户报告的 templateId ===")
    for test_id in test_ids:
        cursor.execute(
            "SELECT id, questionnaire_name FROM crm_questionnaire_template WHERE id = %s",
            (test_id,)
        )
        result = cursor.fetchone()
        if result:
            print(f"找到: {test_id} -> {result['questionnaire_name']}")
        else:
            print(f"未找到: {test_id}")
    
    # 关闭连接
    cursor.close()
    connection.close()
    
except Exception as e:
    print(f"错误: {e}")
