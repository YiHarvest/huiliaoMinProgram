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

print("=== crm_questionnaire_user_record 结构 ===")
cursor.execute("SHOW CREATE TABLE crm_questionnaire_user_record")
row = cursor.fetchone()
print(row['Create Table'])

cursor.close()
conn.close()