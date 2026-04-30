#!/usr/bin/env python3
"""
查看 crm_questionnaire_template 表结构
"""
import mysql.connector
from config import config

mysql_config = config['database']['mysql']
conn = mysql.connector.connect(
    host=mysql_config['host'],
    port=mysql_config['port'],
    user=mysql_config['user'],
    password=mysql_config['password'],
    database=mysql_config['database']
)

cursor = conn.cursor()

# 查看表结构
cursor.execute("DESCRIBE crm_questionnaire_template")
print("crm_questionnaire_template 表结构:")
for row in cursor.fetchall():
    print(f"  {row}")

# 查看前几条数据
cursor.execute("SELECT * FROM crm_questionnaire_template LIMIT 3")
print("\ncrm_questionnaire_template 前3条数据:")
for row in cursor.fetchall():
    print(f"  {row}")

cursor.close()
conn.close()
