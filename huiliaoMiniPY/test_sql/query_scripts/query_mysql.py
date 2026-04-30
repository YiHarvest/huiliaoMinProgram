import mysql.connector

# 连接MySQL
conn = mysql.connector.connect(
    host='117.89.185.157',
    port=13049,
    user='jinlong',
    password='jinlong@880208',
    database='huiliao_dev',
    charset='utf8mb4'
)

cursor = conn.cursor(dictionary=True)

print('=== MySQL 查询结果 ===')
print('1. 模板信息:')
cursor.execute('SELECT id, questionnaire_name FROM crm_questionnaire_template WHERE id = 2044969684322750465')
for row in cursor.fetchall():
    print(row)

print('2. 题目数量:')
cursor.execute('SELECT COUNT(*) FROM crm_questionnaire_template_subject WHERE template_id = 2044969684322750465')
print(cursor.fetchone())

print('3. 前5题:')
cursor.execute('SELECT subject_id, subject_title, sort_order FROM crm_questionnaire_template_subject WHERE template_id = 2044969684322750465 ORDER BY sort_order LIMIT 5')
for row in cursor.fetchall():
    print(row)

conn.close()