import sqlite3
import os

# SQLite文件路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_PATH = os.path.join(BASE_DIR, 'data', 'questionnaire.sqlite')

def test_template_id(template_id):
    """测试模板ID是否存在"""
    print(f"[测试] 检查模板ID: {template_id}")
    print(f"[测试] 数据库路径: {SQLITE_PATH}")
    
    try:
        conn = sqlite3.connect(SQLITE_PATH)
        cursor = conn.cursor()
        
        # 检查模板是否存在
        cursor.execute('''
        SELECT id, questionnaire_name FROM crm_questionnaire_template 
        WHERE id = ?
        ''', (template_id,))
        result = cursor.fetchone()
        
        if result:
            print(f"[测试] 模板存在: ID={result[0]}, 名称={result[1]}")
        else:
            print(f"[测试] 模板不存在: {template_id}")
        
        # 检查模板是否有有效题目
        cursor.execute('''
        SELECT COUNT(*) FROM crm_questionnaire_template_subject 
        WHERE template_id = ?
        AND subject_title IS NOT NULL AND subject_title != ''
        AND subject_content IS NOT NULL AND subject_content != '{}' AND subject_content != '[]'
        ''', (template_id,))
        count = cursor.fetchone()[0]
        print(f"[测试] 有效题目数量: {count}")
        
    except Exception as e:
        print(f"[测试] 错误: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

# 测试前端传入的模板ID
test_template_id(2044996968432275050)
test_template_id(2044968508025999400)

# 查看前10个模板的ID
print("\n[测试] 前10个模板ID:")
try:
    conn = sqlite3.connect(SQLITE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    SELECT id, questionnaire_name FROM crm_questionnaire_template 
    ORDER BY id DESC LIMIT 10
    ''')
    results = cursor.fetchall()
    for row in results:
        print(f"ID: {row[0]}, 名称: {row[1]}")
except Exception as e:
    print(f"[测试] 错误: {str(e)}")
finally:
    if 'conn' in locals():
        conn.close()
