import mysql.connector

# 连接MySQL
conn = mysql.connector.connect(
    host='192.168.1.208',
    port=13060,
    user='miniprogramYQY',
    password='yqy123456',
    database='miniprogramYQY',
    charset='utf8mb4'
)

cursor = conn.cursor()

print('=== crm_subject 表结构 ===')
cursor.execute('DESCRIBE crm_subject')
for row in cursor.fetchall():
    print(row)

print('\n=== crm_questionnaire_user_subject_record 表结构 ===')
cursor.execute('DESCRIBE crm_questionnaire_user_subject_record')
for row in cursor.fetchall():
    print(row)

print('\n=== crm_questionnaire_user_submit_result 表结构 ===')
cursor.execute('DESCRIBE crm_questionnaire_user_submit_result')
for row in cursor.fetchall():
    print(row)

print('\n=== crm_questionnaire_user_submit_result_analysis 表结构 ===')
cursor.execute('DESCRIBE crm_questionnaire_user_submit_result_analysis')
for row in cursor.fetchall():
    print(row)

conn.close()
