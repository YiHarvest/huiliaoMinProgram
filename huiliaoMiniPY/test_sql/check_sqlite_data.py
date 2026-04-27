import sqlite3
import csv
import os

# 连接SQLite
db_path = 'd:\\huiliao\\huiliao\\huiliaoMiniPY\\data\\questionnaire.sqlite'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

cursor = conn.cursor()

print('=== SQLite 源库数据检查 ===')
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
SELECT template_id, id as subject_id, sort as sort_order, COUNT(*) AS cnt
FROM crm_questionnaire_template_subject
GROUP BY template_id, id, sort
HAVING COUNT(*) > 1
ORDER BY template_id, sort
''')
duplicates = cursor.fetchall()
print(f'   发现 {len(duplicates)} 组重复数据:')
for row in duplicates:
    print(f'   template_id={row["template_id"]}, subject_id={row["subject_id"]}, sort_order={row["sort_order"]}, count={row["cnt"]}')

# 4. 导出模板表为CSV
print('\n4. 导出数据为CSV:')
template_csv = 'd:\\huiliao\\huiliao\\huiliaoMiniPY\\test_sql\\sqlite_template_export.csv'
subject_csv = 'd:\\huiliao\\huiliao\\huiliaoMiniPY\\test_sql\\sqlite_subject_export.csv'

# 导出模板表
cursor.execute('SELECT * FROM crm_questionnaire_template')
template_rows = cursor.fetchall()
with open(template_csv, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    if template_rows:
        writer.writerow([description[0] for description in cursor.description])
        for row in template_rows:
            writer.writerow(row)
print(f'   模板表导出到: {template_csv}')

# 导出题目表
cursor.execute('SELECT * FROM crm_questionnaire_template_subject')
subject_rows = cursor.fetchall()
with open(subject_csv, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    if subject_rows:
        writer.writerow([description[0] for description in cursor.description])
        for row in subject_rows:
            writer.writerow(row)
print(f'   题目表导出到: {subject_csv}')

print('\n=== 检查完成 ===')

conn.close()