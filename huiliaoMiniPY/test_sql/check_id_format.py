import mysql.connector

config = {
    'host': '192.168.1.208',
    'port': 13060,
    'user': 'miniprogramYQY',
    'password': 'yqy123456',
    'database': 'miniprogramYQY',
    'charset': 'utf8mb4'
}

conn = mysql.connector.connect(**config)
cursor = conn.cursor(dictionary=True)

print("=== 查看现有记录的 id 格式 ===")
cursor.execute("SELECT id FROM crm_questionnaire_user_record ORDER BY id DESC LIMIT 5")
rows = cursor.fetchall()
for row in rows:
    print(f"  id: {row['id']}, 类型: {type(row['id'])}")

cursor.close()
conn.close()

import time
import random

current_time = int(time.time() * 1000) * 1000000 + random.randint(1, 999999)
print(f"\n生成的测试 ID: {current_time}")