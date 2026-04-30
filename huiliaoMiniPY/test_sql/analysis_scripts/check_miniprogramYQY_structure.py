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

print('=== miniprogramYQY 表结构检查 ===')
print()

# 检查模板表结构
print('1. crm_questionnaire_template 表结构:')
cursor.execute('DESCRIBE crm_questionnaire_template')
for row in cursor.fetchall():
    print(row)

# 检查题目表结构
print('\n2. crm_questionnaire_template_subject 表结构:')
cursor.execute('DESCRIBE crm_questionnaire_template_subject')
for row in cursor.fetchall():
    print(row)

# 检查用户记录表结构
print('\n3. crm_questionnaire_user_record 表结构:')
cursor.execute('DESCRIBE crm_questionnaire_user_record')
for row in cursor.fetchall():
    print(row)

# 检查模板表数据
print('\n4. crm_questionnaire_template 数据:')
cursor.execute('SELECT * FROM crm_questionnaire_template LIMIT 5')
for row in cursor.fetchall():
    print(row)

conn.close()