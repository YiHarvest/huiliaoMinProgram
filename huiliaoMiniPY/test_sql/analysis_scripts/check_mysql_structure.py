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
    'ssl_disabled': True  # 禁用 SSL
}

try:
    # 连接 MySQL 数据库
    connection = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = connection.cursor()
    
    # 查询 crm_questionnaire_template_subject 表的结构
    print("=== crm_questionnaire_template_subject 表结构 ===")
    cursor.execute("SHOW COLUMNS FROM crm_questionnaire_template_subject")
    columns = cursor.fetchall()
    for column in columns:
        print(f"{column[0]}: {column[1]}")
    
    # 查询 crm_questionnaire_template 表的结构
    print("\n=== crm_questionnaire_template 表结构 ===")
    cursor.execute("SHOW COLUMNS FROM crm_questionnaire_template")
    columns = cursor.fetchall()
    for column in columns:
        print(f"{column[0]}: {column[1]}")
    
    # 查询 crm_questionnaire_template 表的前 10 条记录
    print("\n=== crm_questionnaire_template 表前 10 条记录 ===")
    cursor.execute("SELECT id, questionnaire_name, questionnaire_type, apply_department, group_type FROM crm_questionnaire_template LIMIT 10")
    records = cursor.fetchall()
    for record in records:
        print(f"ID: {record[0]}, 名称: {record[1]}, 类型: {record[2]}, 科室: {record[3]}, 分组: {record[4]}")
    
    # 关闭连接
    cursor.close()
    connection.close()
    
except Exception as e:
    print(f"错误: {e}")
