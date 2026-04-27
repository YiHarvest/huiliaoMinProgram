import sqlite3

# 连接SQLite
sqlite_path = 'd:\\huiliao\\huiliao\\huiliaoMiniPY\\data\\questionnaire.sqlite'
conn = sqlite3.connect(sqlite_path)
conn.row_factory = sqlite3.Row

cursor = conn.cursor()

print('=== SQLite表结构检查 ===')
print()

# 检查用户题目记录表结构
print('1. crm_questionnaire_user_subject_record 表结构:')
cursor.execute('PRAGMA table_info(crm_questionnaire_user_subject_record)')
for row in cursor.fetchall():
    print(row)

# 检查前5条数据
print('\n2. crm_questionnaire_user_subject_record 前5条数据:')
cursor.execute('SELECT * FROM crm_questionnaire_user_subject_record LIMIT 5')
for row in cursor.fetchall():
    print(dict(row))

# 检查其他运行时表结构
print('\n3. crm_questionnaire_user_submit_result 表结构:')
cursor.execute('PRAGMA table_info(crm_questionnaire_user_submit_result)')
for row in cursor.fetchall():
    print(row)

print('\n4. crm_questionnaire_user_submit_result_analysis 表结构:')
cursor.execute('PRAGMA table_info(crm_questionnaire_user_submit_result_analysis)')
for row in cursor.fetchall():
    print(row)

conn.close()