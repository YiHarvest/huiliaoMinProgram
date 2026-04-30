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
cursor.execute('SELECT id, subject_title, sort FROM crm_questionnaire_template_subject WHERE template_id = 2044969684322750465 ORDER BY sort LIMIT 5')
for row in cursor.fetchall():
    print(dict(row))

# 检查最近的提交记录
print('\n=== 最近的提交记录 ===')
cursor.execute('SELECT id, template_id, external_user_id, status, create_time FROM crm_questionnaire_user_record ORDER BY create_time DESC LIMIT 3')
print('最近3条用户记录:')
records = []
for row in cursor.fetchall():
    record = dict(row)
    records.append(record)
    print(record)

# 检查提交结果
if records:
    record_id = records[0]['id']
    print(f'\n=== 提交结果 (record_id={record_id}) ===')
    cursor.execute('SELECT id, record_id FROM crm_questionnaire_user_submit_result WHERE record_id = ?', (record_id,))
    for row in cursor.fetchall():
        print(dict(row))
    
    print(f'\n=== 分析结果 (record_id={record_id}) ===')
    cursor.execute('SELECT id, record_id FROM crm_questionnaire_user_submit_result_analysis WHERE record_id = ?', (record_id,))
    for row in cursor.fetchall():
        print(dict(row))

conn.close()