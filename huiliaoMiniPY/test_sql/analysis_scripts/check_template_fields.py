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

print("=== crm_questionnaire_template 真实字段 ===")
cursor.execute("SHOW COLUMNS FROM crm_questionnaire_template")
for col in cursor.fetchall():
    print(f"  {col['Field']}: {col['Type']}")

print("\n=== 样本数据 ===")
cursor.execute("SELECT * FROM crm_questionnaire_template LIMIT 1")
row = cursor.fetchone()
if row:
    for k, v in row.items():
        print(f"  {k}: {v}")

cursor.close()
conn.close()