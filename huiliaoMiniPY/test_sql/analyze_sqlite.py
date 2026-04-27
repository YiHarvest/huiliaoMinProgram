import sqlite3

def analyze_database(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 获取所有表名
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence'")
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f"\n=== {db_path} ===")
    print(f"Tables: {tables}")
    
    # 分析每张表的结构
    for table in tables:
        print(f"\n--- {table} ---")
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        
        for col in columns:
            col_id, name, type_, notnull, dflt_value, pk = col
            pk_str = "PRIMARY KEY" if pk else ""
            print(f"{name} ({type_}) {pk_str}")
    
    conn.close()

# 分析两个数据库
analyze_database('data/questionnaire.sqlite')
analyze_database('data/mini_program.db')