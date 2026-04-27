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
    
    # 查询crm_questionnaire_template表
    print("=== crm_questionnaire_template 表前10条记录 ===")
    cursor.execute("SELECT id, questionnaire_name, questionnaire_type, apply_department, group_type FROM crm_questionnaire_template LIMIT 10")
    templates = cursor.fetchall()
    
    for template in templates:
        print(f"ID: {template['id']}, 名称: {template['questionnaire_name']}, 类型: {template['questionnaire_type']}, 科室: {template['apply_department']}, 分组: {template['group_type']}")
    
    # 统计总数
    cursor.execute("SELECT COUNT(*) as total FROM crm_questionnaire_template")
    total = cursor.fetchone()['total']
    print(f"\n量表总数: {total}")
    
    # 关闭连接
    cursor.close()
    connection.close()
    
except Exception as e:
    print(f"错误: {e}")
