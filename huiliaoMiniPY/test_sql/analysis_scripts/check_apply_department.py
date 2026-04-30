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

print("=== crm_questionnaire_template_subject 关键字段 ===")
cursor.execute("SHOW COLUMNS FROM crm_questionnaire_template_subject WHERE Field IN ('apply_department', 'template_id')")
for col in cursor.fetchall():
    print(f"  {col['Field']}: {col['Type']}")

print("\n=== 查看题目表的 apply_department ===")
cursor.execute("SELECT apply_department FROM crm_questionnaire_template_subject LIMIT 1")
row = cursor.fetchone()
print(f"  apply_department: {row['apply_department'] if row else 'N/A'}")

cursor.close()
conn.close()