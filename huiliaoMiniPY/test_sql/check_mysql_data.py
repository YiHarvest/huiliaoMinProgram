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

cursor = conn.cursor(dictionary=True)

print('=== MySQL 当前数据检查 ===')
print()

# 1. 检查模板表总行数
print('1. 模板表检查:')
cursor.execute('SELECT COUNT(*) AS template_cnt FROM crm_questionnaire_template')
template_count = cursor.fetchone()['template_cnt']
print(f'   总行数: {template_count}')

# 2. 检查题目表总行数
print('\n2. 题目表检查:')
cursor.execute('SELECT COUNT(*) AS subject_cnt FROM crm_questionnaire_template_subject')
subject_count = cursor.fetchone()['subject_cnt']
print(f'   总行数: {subject_count}')

# 3. 检查题目表重复数据
print('\n3. 题目表重复数据检查:')
cursor.execute('''
SELECT template_id, subject_id, sort_order, COUNT(*) AS cnt
FROM crm_questionnaire_template_subject
GROUP BY template_id, subject_id, sort_order
HAVING COUNT(*) > 1
ORDER BY template_id, sort_order
''')
duplicates = cursor.fetchall()
print(f'   发现 {len(duplicates)} 组重复数据:')
for row in duplicates:
    print(f'   template_id={row["template_id"]}, subject_id={row["subject_id"]}, sort_order={row["sort_order"]}, count={row["cnt"]}')

print('\n=== 检查完成 ===')

conn.close()