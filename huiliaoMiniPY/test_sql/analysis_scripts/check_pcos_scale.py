import sqlite3

# 连接SQLite
sqlite_path = 'd:\\huiliao\\huiliao\\huiliaoMiniPY\\data\\questionnaire.sqlite'
conn = sqlite3.connect(sqlite_path)
conn.row_factory = sqlite3.Row

cursor = conn.cursor()

# 查找PCOS量表
print('=== SQLite中PCOS不孕症线上初筛信息表 ===')

# 查找模板
cursor.execute("SELECT id, questionnaire_name FROM crm_questionnaire_template WHERE questionnaire_name LIKE ?", ("%PCOS%",))
template = cursor.fetchone()

if template:
    template_id = template['id']
    print(f"模板ID: {template_id}")
    print(f"模板名称: {template['questionnaire_name']}")
    
    # 查找题目
    cursor.execute("SELECT id, subject_title, sort FROM crm_questionnaire_template_subject WHERE template_id = ? ORDER BY sort", (template_id,))
    subjects = cursor.fetchall()
    
    print(f"\n题目数量: {len(subjects)}")
    print("题目列表:")
    for i, subject in enumerate(subjects):
        print(f"  第{i+1}题: subject_id={subject['id']}, title={subject['subject_title']}, sort={subject['sort']}")
else:
    print("未找到PCOS量表")

conn.close()