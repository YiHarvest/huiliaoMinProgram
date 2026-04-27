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

print('=== MySQL表结构检查 ===')
print()

# 检查用户题目记录表结构
print('1. crm_questionnaire_user_subject_record 表结构:')
cursor.execute('DESCRIBE crm_questionnaire_user_subject_record')
for row in cursor.fetchall():
    print(row)

# 检查提交结果表结构
print('\n2. crm_questionnaire_user_submit_result 表结构:')
cursor.execute('DESCRIBE crm_questionnaire_user_submit_result')
for row in cursor.fetchall():
    print(row)

# 检查分析结果表结构
print('\n3. crm_questionnaire_user_submit_result_analysis 表结构:')
cursor.execute('DESCRIBE crm_questionnaire_user_submit_result_analysis')
for row in cursor.fetchall():
    print(row)

conn.close()