#!/usr/bin/env python3
"""
检查用户作答相关表的结构
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

# 检查表结构
print("crm_questionnaire_user_subject_record 表结构:")
cursor.execute("DESCRIBE crm_questionnaire_user_subject_record")
for row in cursor.fetchall():
    print(f"  {row}")

print("\ncrm_questionnaire_user_submit_result 表结构:")
cursor.execute("DESCRIBE crm_questionnaire_user_submit_result")
for row in cursor.fetchall():
    print(f"  {row}")

print("\ncrm_questionnaire_user_submit_result_analysis 表结构:")
cursor.execute("DESCRIBE crm_questionnaire_user_submit_result_analysis")
for row in cursor.fetchall():
    print(f"  {row}")

cursor.close()
conn.close()
