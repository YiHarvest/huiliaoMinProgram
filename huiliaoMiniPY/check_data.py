#!/usr/bin/env python3
"""
检查 crm_questionnaire_template 表中的数据
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

# 检查所有数据
cursor.execute("SELECT COUNT(*) FROM crm_questionnaire_template")
print(f"总记录数: {cursor.fetchone()[0]}")

# 检查符合条件的数据
cursor.execute("SELECT COUNT(*) FROM crm_questionnaire_template WHERE del_flag = '0' AND status = '1'")
print(f"符合 del_flag='0' AND status='1' 的记录数: {cursor.fetchone()[0]}")

# 检查 del_flag 的值
cursor.execute("SELECT DISTINCT del_flag FROM crm_questionnaire_template")
print(f"del_flag 的不同值: {[row[0] for row in cursor.fetchall()]}")

# 检查 status 的值
cursor.execute("SELECT DISTINCT status FROM crm_questionnaire_template")
print(f"status 的不同值: {[row[0] for row in cursor.fetchall()]}")

# 检查前几条数据
cursor.execute("SELECT id, del_flag, status, questionnaire_name FROM crm_questionnaire_template LIMIT 5")
print("\n前5条数据:")
for row in cursor.fetchall():
    print(f"  {row}")

cursor.close()
conn.close()
