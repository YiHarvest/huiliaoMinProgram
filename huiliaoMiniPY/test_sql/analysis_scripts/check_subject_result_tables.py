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

for table in ['crm_questionnaire_user_subject_record', 'crm_questionnaire_user_submit_result', 'crm_questionnaire_user_submit_result_analysis']:
    print(f"\n=== {table} ===")
    cursor.execute(f"SHOW CREATE TABLE {table}")
    row = cursor.fetchone()
    print(row['Create Table'])

cursor.close()
conn.close()