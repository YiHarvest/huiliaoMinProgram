#!/usr/bin/env python3
"""
检查数据库中是否有题目相关的表
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

# 检查所有表
cursor.execute("SHOW TABLES LIKE 'crm_questionnaire%'")
print("所有 crm_questionnaire 相关表:")
for row in cursor.fetchall():
    print(f"  {row[0]}")

# 检查题目相关的表
print("\n检查题目相关的表:")
cursor.execute("SHOW TABLES LIKE '%question%'")
for row in cursor.fetchall():
    print(f"  {row[0]}")

cursor.close()
conn.close()
