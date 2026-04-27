import sqlite3

def get_table_structure(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 获取所有表名
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence'")
    tables = [row[0] for row in cursor.fetchall()]
    
    structure = {}
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        structure[table] = [col[1] for col in columns]
    
    conn.close()
    return structure

def compare_databases():
    print("=== 数据库结构对比报告 ===")
    print("\n1. 表结构对比")
    
    # 获取两个数据库的结构
    mini_program_structure = get_table_structure('data/mini_program.db')
    questionnaire_structure = get_table_structure('data/questionnaire.sqlite')
    
    # 获取所有表名
    all_tables = set(mini_program_structure.keys()) | set(questionnaire_structure.keys())
    
    # 对比相同表的字段差异
    common_tables = set(mini_program_structure.keys()) & set(questionnaire_structure.keys())
    print(f"\n共有 {len(common_tables)} 个共同表:")
    
    for table in common_tables:
        mini_cols = set(mini_program_structure[table])
        ques_cols = set(questionnaire_structure[table])
        
        # 找出差异字段
        only_in_mini = mini_cols - ques_cols
        only_in_ques = ques_cols - mini_cols
        
        print(f"\n--- {table} ---")
        if only_in_ques:
            print(f"  questionnaire.sqlite 特有字段: {sorted(only_in_ques)}")
        if only_in_mini:
            print(f"  mini_program.db 特有字段: {sorted(only_in_mini)}")
        if not only_in_ques and not only_in_mini:
            print("  字段完全相同")
    
    # 找出各自独有的表
    only_in_mini = set(mini_program_structure.keys()) - set(questionnaire_structure.keys())
    only_in_ques = set(questionnaire_structure.keys()) - set(mini_program_structure.keys())
    
    if only_in_mini:
        print(f"\nmini_program.db 独有表: {sorted(only_in_mini)}")
    
    if only_in_ques:
        print(f"\nquestionnaire.sqlite 独有表: {sorted(only_in_ques)}")
    
    print("\n2. 数据迁移建议")
    print("\n建议将 questionnaire.sqlite 的历史数据导入到以下独立的 legacy 表中:")
    for table in common_tables:
        print(f"  - {table}_legacy")
    
    print("\n3. 需要补充的字段")
    print("对于共同表，questionnaire.sqlite 比 mini_program.db 多了以下字段:")
    for table in common_tables:
        mini_cols = set(mini_program_structure[table])
        ques_cols = set(questionnaire_structure[table])
        only_in_ques = ques_cols - mini_cols
        if only_in_ques:
            print(f"  {table}: {sorted(only_in_ques)}")

if __name__ == '__main__':
    compare_databases()