#!/usr/bin/env python3
"""
验证 crm_questionnaire_user_subject_record 表中的数据
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

# 统计记录数
cursor.execute("SELECT COUNT(*) FROM crm_questionnaire_user_subject_record WHERE record_id = '1777000284665'")
count = cursor.fetchone()[0]
print(f"crm_questionnaire_user_subject_record 中 record_id=1777000284665 的记录数: {count}")

# 查询前 5 条记录
cursor.execute("SELECT id, record_id, subject_id, subject_title, score, create_time FROM crm_questionnaire_user_subject_record WHERE record_id = '1777000284665' LIMIT 5")
print("\n前 5 条记录:")
for row in cursor.fetchall():
    print(f"  {row}")

cursor.close()
conn.close()
