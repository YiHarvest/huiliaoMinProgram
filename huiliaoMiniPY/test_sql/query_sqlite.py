import sqlite3

# 连接SQLite
conn = sqlite3.connect('d:\\huiliao\\huiliao\\huiliaoMiniPY\\data\\questionnaire.sqlite')
conn.row_factory = sqlite3.Row

cursor = conn.cursor()

print('=== SQLite 查询结果 ===')
print('1. 模板信息:')
cursor.execute('SELECT id, questionnaire_name FROM crm_questionnaire_template WHERE id = 2044969684322750465')
for row in cursor.fetchall():
    print(dict(row))

print('2. 题目数量:')
cursor.execute('SELECT COUNT(*) FROM crm_questionnaire_template_subject WHERE template_id = 2044969684322750465')
print(dict(cursor.fetchone()))

print('3. 前5题:')
cursor.execute('SELECT subject_id, subject_title, sort_order FROM crm_questionnaire_template_subject WHERE template_id = 2044969684322750465 ORDER BY sort_order LIMIT 5')
for row in cursor.fetchall():
    print(dict(row))

# 检查SQLite表结构
print('\n=== SQLite 表结构 ===')
cursor.execute('PRAGMA table_info(crm_questionnaire_template_subject)')
print('crm_questionnaire_template_subject 表结构:')
for row in cursor.fetchall():
    print(dict(row))

# 检查最近的提交记录
print('\n=== 最近的提交记录 ===')
cursor.execute('SELECT id, template_id, created_at FROM crm_questionnaire_user_record ORDER BY created_at DESC LIMIT 5')
print('最近5条用户记录:')
for row in cursor.fetchall():
    print(dict(row))

conn.close()