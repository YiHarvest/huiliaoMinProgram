import mysql.connector
import csv
import os

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

print('=== MySQL 临时表创建与数据导入 ===')
print()

# 1. 创建临时模板表
print('1. 创建临时模板表:')
cursor.execute('''
CREATE TABLE IF NOT EXISTS sqlite_template_stage (
    id BIGINT PRIMARY KEY,
    questionnaire_name TEXT,
    description TEXT,
    status INTEGER,
    create_time TEXT,
    update_time TEXT,
    is_deleted INTEGER,
    create_user TEXT,
    update_user TEXT
)
''')
print('   临时模板表创建成功')

# 2. 创建临时题目表
print('\n2. 创建临时题目表:')
cursor.execute('''
CREATE TABLE IF NOT EXISTS sqlite_subject_stage (
    id BIGINT PRIMARY KEY,
    template_id BIGINT,
    subject_title TEXT,
    subject_type INTEGER,
    subject_content TEXT,
    sort INTEGER,
    create_time TEXT,
    update_time TEXT,
    is_deleted INTEGER,
    create_user TEXT,
    update_user TEXT
)
''')
print('   临时题目表创建成功')

# 3. 清空临时表
print('\n3. 清空临时表:')
cursor.execute('TRUNCATE TABLE sqlite_template_stage')
cursor.execute('TRUNCATE TABLE sqlite_subject_stage')
print('   临时表清空成功')

# 4. 导入模板数据
print('\n4. 导入模板数据:')
template_csv = 'd:\\huiliao\\huiliao\\huiliaoMiniPY\\test_sql\\sqlite_template_export.csv'
with open(template_csv, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    header = next(reader)  # 跳过表头
    count = 0
    for row in reader:
        if len(row) >= 9:
            cursor.execute('''
            INSERT INTO sqlite_template_stage 
            (id, questionnaire_name, description, status, create_time, update_time, is_deleted, create_user, update_user)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8]))
            count += 1
            if count % 10 == 0:
                conn.commit()
    conn.commit()
print(f'   导入模板数据 {count} 条')

# 5. 导入题目数据
print('\n5. 导入题目数据:')
subject_csv = 'd:\\huiliao\\huiliao\\huiliaoMiniPY\\test_sql\\sqlite_subject_export.csv'
with open(subject_csv, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    header = next(reader)  # 跳过表头
    count = 0
    for row in reader:
        if len(row) >= 11:
            cursor.execute('''
            INSERT INTO sqlite_subject_stage 
            (id, template_id, subject_title, subject_type, subject_content, sort, create_time, update_time, is_deleted, create_user, update_user)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10]))
            count += 1
            if count % 50 == 0:
                conn.commit()
    conn.commit()
print(f'   导入题目数据 {count} 条')

# 6. 验证导入结果
print('\n6. 验证导入结果:')
cursor.execute('SELECT COUNT(*) FROM sqlite_template_stage')
template_count = cursor.fetchone()[0]
print(f'   临时模板表行数: {template_count}')

cursor.execute('SELECT COUNT(*) FROM sqlite_subject_stage')
subject_count = cursor.fetchone()[0]
print(f'   临时题目表行数: {subject_count}')

print('\n=== 临时表创建与数据导入完成 ===')

conn.close()