import sqlite3

conn = sqlite3.connect('data/mini_program.db')
cursor = conn.cursor()

# 获取所有表名
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence'")
tables = [row[0] for row in cursor.fetchall()]

print('Tables in mini_program.db:')
for table in tables:
    print(f'\n--- {table} ---')
    cursor.execute(f"PRAGMA table_info({table})")
    columns = cursor.fetchall()
    for col in columns:
        col_id, name, type_, notnull, dflt_value, pk = col
        pk_str = "PRIMARY KEY" if pk else ""
        print(f"{name} ({type_}) {pk_str}")

conn.close()