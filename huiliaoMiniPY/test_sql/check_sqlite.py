import sqlite3

conn = sqlite3.connect('data/mini_program.db')
cursor = conn.cursor()

print("=== SQLite 源库数据检查 ===")
print()

# 检查有题目的模板
cursor.execute('''
SELECT COUNT(*) FROM crm_questionnaire_template_subject
WHERE subject_title IS NOT NULL AND subject_title != ''
AND subject_content IS NOT NULL AND subject_content != '{}' AND subject_content != '[]'
''')
print("SQLite 有题目的记录总数:", cursor.fetchone()[0])

cursor.execute('''
SELECT DISTINCT COUNT(*) FROM crm_questionnaire_template_subject
WHERE subject_title IS NOT NULL AND subject_title != ''
AND subject_content IS NOT NULL AND subject_content != '{}' AND subject_content != '[]'
''')
print("SQLite 唯一 template_id 数:", cursor.fetchone()[0])

cursor.execute('''
SELECT template_id, COUNT(*) as cnt
FROM crm_questionnaire_template_subject
WHERE subject_title IS NOT NULL AND subject_title != ''
AND subject_content IS NOT NULL AND subject_content != '{}' AND subject_content != '[]'
GROUP BY template_id
ORDER BY template_id
''')
results = cursor.fetchall()
print()
print("每个模板的题目数:")
for r in results:
    print(f"  template_id={r[0]}, 题目数={r[1]}")
print()
print(f"共有 {len(results)} 个模板有题目")

# 检查模板总数
cursor.execute("SELECT COUNT(*) FROM crm_questionnaire_template")
print()
print("SQLite 模板总数:", cursor.fetchone()[0])

conn.close()